"""
batch_yaml_gen.py
Batch-generates YAML files for the MBARI WEC Simulator for HYAK/SLURM usage.
"""

import math
import yaml
import numpy as np
from pathlib import Path
import spectrums as spec_module

BASE_OUTPUT_DIR = Path(
    r"C:\Users\Alex Eagan\OneDrive - UW\Documents\GitHub\Mbari_Wec_Compare\HYAK_batch_yamls"
)

# ─── Type Mapping ─────────────────────────────────────────────────────────────

# Maps internal spectrum_type strings (from spectrums.csv) to YAML key names.
# 'spotter'       → Custom       (writes full f / Szz arrays)
# 'bretschneider' → Bretschneider (writes Hs / Tp scalars)
# 'BretHFP'       → Bretschneider (writes Hs / Tp scalars)
_YAML_KEY_MAP = {
    "spotter":       "Custom",
    "bretschneider": "Bretschneider",
    "BretHFP":       "Bretschneider",
    "BretSFP":       "Bretschneider",
}

# ─── YAML Formatting ──────────────────────────────────────────────────────────

class _InlineListDumper(yaml.Dumper):
    """Renders simple (flat) lists inline; nested structures stay block-style."""
    pass

def _represent_list(dumper, data):
    flat = all(isinstance(v, (int, float, str, bool)) for v in data)
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=flat)

_InlineListDumper.add_representer(list, _represent_list)

# ─── Utilities ────────────────────────────────────────────────────────────────

def parse_slurm_time(slurm_time: str) -> float:
    """Parse '[D-]HH:MM:SS' SLURM time string → total minutes (float)."""
    days, rest = (slurm_time.split("-", 1) + [None])[:2]
    if rest is None:
        rest, days = days, 0
    h, m, s = (int(x) for x in rest.split(":"))
    return int(days) * 1440 + h * 60 + m + s / 60

def chunk_list(lst: list, size: int) -> list[list]:
    """Split list into contiguous sublists of at most `size`."""
    return [lst[i : i + size] for i in range(0, len(lst), size)]

def _round_to_4dp(arr) -> list:
    """
    Convert an array-like to a list of floats rounded to 4 decimal places.
    Matches the precision used in print_custom_spectrum().
    """
    return [round(float(x), 4) for x in arr]

# ─── Wave Conditions ──────────────────────────────────────────────────────────

def make_wave_conditions(spectrum_ids: list, spectrum_types: list) -> list[dict]:
    """
    Build wave condition dicts by fetching all data from the spectrums CSV.

    For 'spotter' types              → fetches f and Szz arrays → Custom YAML key.
    For 'bretschneider' / 'BretHFP' → fetches Hs and Tp        → Bretschneider YAML key.

    Parameters
    ----------
    spectrum_ids : list of int
        Spectrum IDs matching entries in spectrums.csv.
    spectrum_types : list of str
        Internal spectrum type strings (e.g. 'spotter', 'BretHFP', 'bretschneider').

    Returns
    -------
    list of dict, each containing:
        spectrum_index, internal_type, yaml_key, and either
        (f, Szz) for Custom or (Hs, Tp) for Bretschneider.
    """
    # Dynamically create combinations of spectrum_ids and spectrum_types
    spectrum_combinations = [
        (sid, stype) for sid in spectrum_ids for stype in spectrum_types
    ]

    conditions = []
    for sid, stype in spectrum_combinations:
        yaml_key = _YAML_KEY_MAP.get(stype)
        if yaml_key is None:
            raise ValueError(
                f"Unknown spectrum type '{stype}'. "
                f"Supported types: {list(_YAML_KEY_MAP.keys())}"
            )

        if yaml_key == "Custom":
            # spec_module.spectrum() reads and parses f/Szz from the CSV,
            # returning numpy arrays ready for rounding.
            f_arr, szz_arr = spec_module.spectrum(sid, stype)
            conditions.append({
                "spectrum_index": sid,
                "internal_type":  stype,
                "yaml_key":       "Custom",
                "f":              _round_to_4dp(f_arr),
                "Szz":            _round_to_4dp(szz_arr),
            })

        else:  # Bretschneider
            df = spec_module.read_spectrums()
            row = df[(df["spectrum_id"] == sid) & (df["spectrum_type"] == stype)]
            if row.empty:
                raise ValueError(
                    f"Spectrum ID {sid} of type '{stype}' not found in spectrums CSV."
                )
            hs = float(row["significantWaveHeight"].iloc[0])
            tp = float(row["peakPeriod"].iloc[0])
            conditions.append({
                "spectrum_index": sid,
                "internal_type":  stype,
                "yaml_key":       "Bretschneider",
                "Hs":             round(hs, 4),
                "Tp":             round(tp, 4),
            })

    return conditions

# ─── Divide Batch: Optimisers ─────────────────────────────────────────────────

def _optimize_two_chunk(A: int, B: int, budget: int) -> tuple:
    """
    Find (a_chunk, b_chunk) minimising ceil(A/a)*ceil(B/b) s.t. a*b <= budget.
    Returns (n_yamls, a_chunk, b_chunk); infeasible → (inf, 0, 0).
    """
    if budget < 1:
        return math.inf, 0, 0
    best_n, best_a, best_b = math.inf, 1, 1
    for a in range(1, A + 1):
        b = min(budget // a, B)
        if b < 1:
            break
        n = math.ceil(A / a) * math.ceil(B / b)
        if n < best_n:
            best_n, best_a, best_b = n, a, b
    return best_n, best_a, best_b

def _best_one_param_split(S, F, W, M) -> tuple:
    """
    Minimum yamls when only 1 parameter varies.
    Returns (n_yamls, param_name, chunk_size) or (inf, None, None).
    """
    options = []
    if 0 < F * W <= M:
        options.append((math.ceil(S / (M // (F * W))), "seeds", M // (F * W)))
    if 0 < S * W <= M:
        options.append((math.ceil(F / (M // (S * W))), "scale", M // (S * W)))
    if 0 < S * F <= M:
        options.append((math.ceil(W / (M // (S * F))), "waves", M // (S * F)))
    return min(options, key=lambda x: x[0]) if options else (math.inf, None, None)

def _best_two_param_split(S, F, W, M) -> tuple:
    """
    Minimum yamls when exactly 2 parameters vary.
    Returns (n_yamls, (param_a, param_b), (chunk_a, chunk_b)) or (inf, None, None).
    """
    options = []
    for labels, A, B, fixed in [
        (("seeds", "scale"), S, F, W),
        (("seeds", "waves"), S, W, F),
        (("scale", "waves"), F, W, S),
    ]:
        n, ca, cb = _optimize_two_chunk(A, B, M // fixed if fixed > 0 else 0)
        if n != math.inf:
            options.append((n, labels, (ca, cb)))
    return min(options, key=lambda x: x[0]) if options else (math.inf, None, None)

def _best_three_param_split(S, F, W, M) -> tuple:
    """
    Minimum yamls when all 3 parameters vary.
    Returns (n_yamls, (s_chunk, f_chunk, w_chunk)).
    """
    best_n, best_chunks = math.inf, (1, 1, 1)
    for s in range(1, S + 1):
        if M // s < 1:
            break
        for f in range(1, F + 1):
            if s * f > M:
                break
            w = min(M // (s * f), W)
            n = math.ceil(S / s) * math.ceil(F / f) * math.ceil(W / w)
            if n < best_n:
                best_n, best_chunks = n, (s, f, w)
    return best_n, best_chunks

# ─── Divide Batch: Assembly ───────────────────────────────────────────────────

def _assemble_yamls(seeds, scales, waves, strategy, vary_info, chunk_info) -> list:
    """Convert a chosen strategy into a list of (seed_chunk, scale_chunk, wave_chunk)."""
    if strategy == 1:
        param, size = vary_info, chunk_info
        if param == "seeds":  return [(sc, scales, waves) for sc in chunk_list(seeds, size)]
        if param == "scale":  return [(seeds, fc, waves) for fc in chunk_list(scales, size)]
        if param == "waves":  return [(seeds, scales, wc) for wc in chunk_list(waves, size)]

    if strategy == 2:
        (pa, pb), (ca, cb) = vary_info, chunk_info
        if (pa, pb) == ("seeds", "scale"):
            return [(sc, fc, waves) for sc in chunk_list(seeds, ca) for fc in chunk_list(scales, cb)]
        if (pa, pb) == ("seeds", "waves"):
            return [(sc, scales, wc) for sc in chunk_list(seeds, ca) for wc in chunk_list(waves, cb)]
        if (pa, pb) == ("scale", "waves"):
            return [(seeds, fc, wc) for fc in chunk_list(scales, ca) for wc in chunk_list(waves, cb)]

    # strategy == 3
    s_c, f_c, w_c = chunk_info
    return [
        (sc, fc, wc)
        for sc in chunk_list(seeds, s_c)
        for fc in chunk_list(scales, f_c)
        for wc in chunk_list(waves, w_c)
    ]

def divide_batch(
    seeds: list, scale_factors: list, wave_conditions: list,
    max_jobs: int, readability_threshold: int
) -> list:
    """
    Divide parameters into (seed_chunk, scale_chunk, wave_chunk) tuples for each yaml.

    Strategy selection:
      - Prefer fewest varying parameters.
      - Accept a more complex strategy only when the simpler one adds more than
        `readability_threshold` extra yamls compared to the next strategy down.
    """
    S, F, W = len(seeds), len(scale_factors), len(wave_conditions)
    assert max_jobs >= 1, f"max_jobs={max_jobs}: check max_time and time_per_job."

    if S * F * W <= max_jobs:
        return [(seeds, scale_factors, wave_conditions)]

    n1, p1, c1 = _best_one_param_split(S, F, W, max_jobs)
    n2, p2, c2 = _best_two_param_split(S, F, W, max_jobs)
    n3, c3     = _best_three_param_split(S, F, W, max_jobs)

    if n1 != math.inf and (n1 - n2) <= readability_threshold:
        return _assemble_yamls(seeds, scale_factors, wave_conditions, 1, p1, c1)
    elif n2 != math.inf and (n2 - n3) <= readability_threshold:
        return _assemble_yamls(seeds, scale_factors, wave_conditions, 2, p2, c2)
    else:
        return _assemble_yamls(seeds, scale_factors, wave_conditions, 3, None, c3)

# ─── File Naming ──────────────────────────────────────────────────────────────

def make_yaml_name(batch_name: str, seed_chunk, scale_chunk, wave_chunk) -> str:
    """Encode parameter ranges into a descriptive filename."""
    s_tag    = f"s{seed_chunk[0]}-{seed_chunk[-1]}"    if len(seed_chunk)  > 1 else f"s{seed_chunk[0]}"
    sf_tag   = f"sf{scale_chunk[0]}-{scale_chunk[-1]}" if len(scale_chunk) > 1 else f"sf{scale_chunk[0]}"
    spec_tag = "spectrums" + ",".join(str(w["spectrum_index"]) for w in wave_chunk)
    return f"{batch_name}_{s_tag}_{sf_tag}_{spec_tag}.yaml"

# ─── YAML Construction ────────────────────────────────────────────────────────

def build_fixed_params(
    duration, physics_rtf, enable_gui, physics_step, door_state, battery_soc
) -> dict:
    """
    Return fixed-parameter dict.
    Centralised here so adding a new fixed param in the future is a single-line change.
    """
    return {
        "duration":     duration,
        "physics_rtf":  physics_rtf,
        "enable_gui":   enable_gui,
        "physics_step": physics_step,
        "door_state":   door_state,
        "battery_soc":  battery_soc,
    }

def _wave_yaml_entry(wave_chunk: list) -> list:
    """
    Convert wave condition dicts → IncidentWaveSpectrumType yaml structure.

    Custom entries write full f / Szz arrays.
    Bretschneider entries write Hs / Tp scalar lists.
    Includes comments for each spectrum ID and type.
    """
    entries = []
    for w in wave_chunk:
        if w["yaml_key"] == "Custom":
            entries.append({
                # Add YAML comment for Custom spectrum - It leaves Null as an artifact and this was chosen to be better than swapping from PyYAML
                f"# Spectrum ID {w['spectrum_index']} of type {w['internal_type']}": None, 
                "Custom": {
                    "f":   w["f"],
                    "Szz": w["Szz"],
                }
            })
        elif w["yaml_key"] == "Bretschneider":
            entries.append({
                # Add YAML comment for Bretschneider spectrum
                f"# Spectrum ID {w['spectrum_index']} of type {w['internal_type']}": None,
                "Bretschneider": {
                    "Hs": [w["Hs"]],
                    "Tp": [w["Tp"]],
                }
            })
    return entries

def build_yaml_dict(fixed_params: dict, seed_chunk, scale_chunk, wave_chunk) -> dict:
    """Assemble the complete content dict for one yaml file."""
    return {
        **fixed_params,
        "seed":                     seed_chunk,
        "scale_factor":             scale_chunk,
        "IncidentWaveSpectrumType": _wave_yaml_entry(wave_chunk),
    }

# ─── YAML Writing ─────────────────────────────────────────────────────────────

def write_yaml(batch_folder: Path, yaml_name: str, yaml_dict: dict):
    """Write a single yaml file into batch_folder (created if absent)."""
    batch_folder.mkdir(parents=True, exist_ok=True)
    with open(batch_folder / yaml_name, "w") as f:
        yaml.dump(yaml_dict, f, Dumper=_InlineListDumper,
                  default_flow_style=False, sort_keys=False)

def write_yamls(batch_name: str, yaml_specs: list, fixed_params: dict) -> tuple:
    """Write all yaml files; returns (count, batch_folder)."""
    batch_folder = BASE_OUTPUT_DIR / batch_name
    for seed_chunk, scale_chunk, wave_chunk in yaml_specs:
        name = make_yaml_name(batch_name, seed_chunk, scale_chunk, wave_chunk)
        data = build_yaml_dict(fixed_params, seed_chunk, scale_chunk, wave_chunk)
        write_yaml(batch_folder, name, data)
    return len(yaml_specs), batch_folder

# ─── Input Checking ───────────────────────────────────────────────────────────

def _prompt(label: str, value):
    """Print one parameter and require 'y' to continue."""
    resp = input(f"  {label}: {value}  [y/n] > ").strip().lower()
    if resp != "y":
        raise SystemExit(f"\n✗ Aborted at: '{label}'")

def check_inputs(
    batch_name, max_jobs, readability_threshold,
    seeds, scale_factors, wave_conditions, fixed_params
):
    """
    Interactive y/n confirmation of all batch parameters before any files are written.

    Custom spectrums display spectrum_id, type, and array lengths.
    Bretschneider spectrums display spectrum_id, type, Hs, and Tp.
    """
    total_jobs = len(seeds) * len(scale_factors) * len(wave_conditions)
    print("\n╔══ Batch Configuration ══════════════════════════════════╗")

    # Overhead
    _prompt("Batch name",            batch_name)
    _prompt("Max jobs per yaml",      max_jobs)
    _prompt("Readability threshold",  readability_threshold)

    # Variable parameters
    _prompt("Seeds",         seeds)
    _prompt("Scale factors", scale_factors)

    for w in wave_conditions:
        if w["yaml_key"] == "Custom":
            _prompt(
                f"Wave (spectrum {w['spectrum_index']}, {w['internal_type']})",
                f"Custom — len(f)={len(w['f'])}, len(Szz)={len(w['Szz'])}",
            )
        elif w["yaml_key"] == "Bretschneider":
            _prompt(
                f"Wave (spectrum {w['spectrum_index']}, {w['internal_type']})",
                f"Bretschneider — Hs={w['Hs']}, Tp={w['Tp']}",
            )

    # Fixed parameters
    print("  Fixed parameters:")
    for k, v in fixed_params.items():
        _prompt(f"  {k}", v)

    # Summary
    print(f"\n  Total jobs in full batch: {total_jobs}")
    _prompt("Proceed with writing yamls?", "confirm")
    print("╚══════════════════════════════════════════════════════════╝\n")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # ── Overhead / timing ────────────────────────────────────────────────────
    batch_name            = "Test" #"spotter_bret_SFP_30+"
    max_time              = "4:00:00"   # SLURM format [D-]HH:MM:SS
    time_per_job          = 30          # minutes per simulation job
    readability_threshold = 10          # max extra yamls to accept fewer varying params

    # ── Derive max jobs per yaml (n-1 safety buffer) ─────────────────────────
    max_jobs = int(parse_slurm_time(max_time) / time_per_job) - 1

    # ── Variable parameters ──────────────────────────────────────────────────
    seeds         = [1]#[1, 2, 3]
    scale_factors = [1] #[0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]

    # f/Szz (Custom) or Hs/Tp (Bretschneider) are fetched automatically from
    # spectrums.csv based on the spectrum_type provided here.
    mbari_2022 = [114, 198, 260, 384, 532, 597]
    mbari_2022_more = [729, 1239, 52, 363, 901, 270, 712, 803, 444]
    mbari_2022_moremorea = [462, 494, 1255, 38]
    mbari_2022_moremoreb = [62, 496]
    spec_ids_add = mbari_2022 + mbari_2022_more + mbari_2022_moremorea + mbari_2022_moremoreb
    spectrum_ids   = [18, 83, 107, 297, 303, 371, 412, 429, 437, 454, 456, 484, 535, 570, 619, 737, 757, 758, 805, 819, 822, 833, 838, 846, 1031, 1045, 1115, 1143, 1174, 1181]
    spectrum_ids = sorted(spectrum_ids + spec_ids_add)
    print(spectrum_ids)
    spectrum_ids = [4, 1204]
    spectrum_types = ["BretSFP", "spotter"]   # 'spotter' → Custom, 'BretHFP' → Bretschneider
    wave_conditions = make_wave_conditions(spectrum_ids, spectrum_types)

    # ── Fixed parameters (add new fixed params here + in build_fixed_params) ──
    fixed_params = build_fixed_params(
        duration     = 2360,
        physics_rtf  = 10,
        enable_gui   = False,
        physics_step = 0.01,
        door_state   = ["closed"],
        battery_soc  = 0.5,
    )

    # ── Validate with user ────────────────────────────────────────────────────
    check_inputs(batch_name, max_jobs, readability_threshold,
                 seeds, scale_factors, wave_conditions, fixed_params)

    # ── Divide and write ──────────────────────────────────────────────────────
    yaml_specs = divide_batch(
        seeds, scale_factors, wave_conditions, max_jobs, readability_threshold
    )
    count, batch_folder = write_yamls(batch_name, yaml_specs, fixed_params)

    print(f"✓ Wrote {count} yaml files → {batch_folder}")

if __name__ == "__main__":
    main()
