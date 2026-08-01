import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from turtle import color

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib as mpl
import pandas as pd
import os
import glob
import textwrap
import math
import scipy.integrate as integrate
import re
from collections import defaultdict

import mainDF_management as mDF_mgmt 
import run_analytics
import wave_operations
import spectrums
import visualization


def full_batches():
    batch_names = ['batch_spotter_bret_30_37374379_20260720', 'batch_spotter_bret_SFP_30+_37450154_20260721', 'batch_spotter_bret_SFP_30+_37450154_20260722'] #FULL SPECTRUMS
    
    resolved_batches = run_analytics.resolve_hyak_batch_names(batch_names)
    batch_kwargs = {f'batch_name{i+1 if i > 0 else ""}': name for i, name in enumerate(resolved_batches)}

    # Add explicitly defined batch names to batch_kwargs
    additional_batches = {
        "batch_name": "batch_results_20260213182532",
        "batch_name2": "batch_results_20260211181904",
        "batch_name3": "batch_results_20260304113810",
        "batch_name4": "batch_results_20260315141339",
        "batch_name5": "batch_results_20260327142504",
    }
    batch_kwargs.update(additional_batches)
    return batch_kwargs

def resolve_hyak_batch_names(hyak_batch_names):
    """
    Given a list of HYAK parent batch names, returns the corresponding
    batch_results_XXXXX names stored in mainDF by matching against run_data_path.
    """
    mainDF = mDF_mgmt.access_mainDF()
    resolved = set()
    for hyak_name in hyak_batch_names:
        matches = mainDF[mainDF['run_data_path'].str.contains(hyak_name, na=False, regex=False)]['batch_file_name'].unique()
        resolved.update(matches)
    return list(resolved)

def _extract_spectrum_params(param_str):
    """
    Parses a semicolon-delimited IncWaveSpectrumType;IncWaveSpectrumParams string
    into a flat list of rounded floats, consistent with the matching logic used
    across slide1dampingcurve and damping_seed_comparison_plot.

    Parameters
    ----------
    param_str : str
        Raw spectrum parameter string from the simulation DataFrame.

    Returns
    -------
    list of float
        Extracted numeric tokens: first frequency value, first 5 non-zero Szz
        values, and all values for other prefixes (Hs, Tp, A, T, etc.).
    """
    result = []
    for part in str(param_str).strip().split(';'):
        if ':' not in part:
            continue
        tokens = part.split(':')
        prefix = tokens[0].strip()
        numbers = []
        for x in tokens[1:]:
            try:
                numbers.append(round(float(x), 4))
            except ValueError:
                continue
        if prefix == 'f':
            result.extend(numbers[:1])
        elif prefix == 'Szz':
            result.extend([n for n in numbers if n != 0.0][:5])
        else:
            result.extend(numbers)
    return result

def slide1spotter(spectrum=1000, name ="slide1spotter.png", types = ('spotter', 'BretSFP'), fontsizetitle=24, fontsizelabel=20, width=16, heightper =9, title=None):
    """
    Plots multiple spectrums on the same axes for comparison, with presentation-ready styling.

    -------
    Parameters:
        spectrum_nums: list of spectrum numbers to plot
        plots_per_page: number of spectrums to plot per page (default 6)
        types: list of spectrum types to include (e.g., ["spotter", "bretschneider", "jonswap"]) or 'all' for all types (default None)
        **kwargs: additional parameters for styling and plot configuration, such as 'period' to indicate whether to plot period instead of frequency.
            Period: bool, whether to plot period instead of frequency (default False)
            n_cols: number of columns in the subplot grid (default 2)
            metric_sv: a metric you want also represented - single value.
            cumsum: bool, whether or not to plot the cumulative sum of the spectrum
    ------
    Returns:
        None (displays the plots)
    """
    reo_df = None
    metric_sv = None
    period = False
    plots_per_page = 1
    n_cols = 1
    spectrum_nums = [spectrum]
    total_plots = len(spectrum_nums)

    # Define available models and their plotting styles
    models = {
        "spotter": {"label": "Spotter", "color": spectrums.get_color_for_spectrum_type("spotter"), "fmt": "scatter", "alpha": 0.7, "marker": "o"},
        "bretschneider": {"label": "Bretschneider", "color": spectrums.get_color_for_spectrum_type("bretschneider"), "fmt": "plot"},
        "BretHFP": {"label": "BretHFP", "color": spectrums.get_color_for_spectrum_type("BretHFP"), "fmt": "plot"},
        "BretSFP": {"label": "BretSFP", "color": spectrums.get_color_for_spectrum_type("BretSFP"), "fmt": "plot"},
        "jonswap": {"label": "Jonswap", "color": spectrums.get_color_for_spectrum_type("jonswap"), "fmt": "plot", "marker": "x"},
        "regular": {"label": "Regular", "color": spectrums.get_color_for_spectrum_type("regular"), "fmt": "vline", "alpha": 0.65},
        "regularHFP": {"label": "RegularHFP", "color": spectrums.get_color_for_spectrum_type("regularHFP"), "fmt": "vline", "alpha": 0.65}
    }

    # If types is None or 'all', use all keys in the models dict
    if types is None or types == 'all':
        selected_types = list(models.keys())
    elif isinstance(types, str):
        selected_types = [types]  # Convert a single string into a list
    else:
        selected_types = types

    for start_idx in range(0, total_plots, plots_per_page):

        def sort_by_embedded_id(spectrum_key):
            """
            Extracts the first continuous block of digits from the spectrum key 
            to use as a sorting integer. If no number is found, returns a high number.
            """
            match = re.search(r'\d+', str(spectrum_key))
            return int(match.group()) if match else 99999

        spectrum_nums = sorted(spectrum_nums, key=sort_by_embedded_id)

        batch = spectrum_nums[start_idx: start_idx + plots_per_page]
        n_rows = (len(batch)) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(width, heightper * n_rows), sharey=True)
        axes = np.atleast_1d(axes).flatten()

        for idx, i in enumerate(batch):
            ax = axes[idx]
            xlabel = 'Period (s)' if period else 'Frequency (Hz)'

            # Dynamic plotting based on selection
            for model_name in selected_types:
                if model_name not in models:
                    continue

                style = models[model_name]
                f, szz = spectrums.spectrum(i, model_name)
                x = 1 / np.array(f) if period else np.array(f)
                szz = np.array(szz) * (np.array(f) ** 2) if period else np.array(szz)

                label = style["label"]

                if style.get("fmt") == "scatter":
                    ax.plot(x, szz, label=label, color=style["color"], alpha=style.get("alpha", 1), marker=style.get("marker"), ms=5.0, linewidth=3)
                elif style.get("fmt") == "vline":
                    ax.axvline(x, color=style["color"], alpha=style.get("alpha", 1), label=label, linewidth=3)
                else:
                    ax.plot(x, szz, label=label, color=style["color"], marker=style.get("marker"), linewidth=3)

            # --- Styling ---
            ax.set_title(f"{title}", fontsize=fontsizetitle)
            ax.set_xlabel(xlabel, fontsize=fontsizelabel)
            if idx % 2 == 0:
                ax.set_ylabel('Spectral Density (m^2/Hz)', fontsize=fontsizelabel)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(fontsize=fontsizelabel)
            ax.tick_params(axis='both', labelsize=16)

        for j in range(len(batch), len(axes)):
            fig.delaxes(axes[j])

        plt.tight_layout()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(current_dir, name)
        plt.savefig(save_path, dpi=600, bbox_inches='tight', transparent=False)
        # plt.show()

def slide1dampingcurve(
    name="damping_avg_by_spec.png",
    spectrum_types=('spotter',),
    spectrum_id=None,
    metric='avg_tot_power',
    cols=1,
    fontsizetitle=24,
    fontsizelabel=20,
    width=16,
    heightper=9,
    verticaltitle='Average Power (W)',
    **kwargs
):
    """
    Presentation-ready plot of average metric across damping/scale factor values,
    grouped by root spectrum. Only spectrums matching the given spectrum_types are plotted.

    Parameters
    ----------
    name : str
        Output filename (saved relative to this file's directory).
    spectrum_types : str, tuple, or list
        Spectrum type(s) to include. Pass a single string (e.g. 'spotter'),
        a tuple/list (e.g. ('spotter', 'BretSFP')), or 'all' / None for all types.
    metric : str
        The DataFrame column to plot on the y-axis.
    cols : int
        Number of subplot columns (default 2).
    fontsizetitle : int
        Font size for subplot titles.
    fontsizelabel : int
        Font size for axis labels and legend.
    width : int
        Total figure width in inches.
    heightper : int
        Figure height per row of subplots, in inches.
    **kwargs
        batch_name, batch_name2, ... : batch file name strings to filter mainDF.
    """

    # --- Resolve spectrum_types to a list (or None for all) ---
    if spectrum_types is None or spectrum_types == 'all':
        selected_types = None
    elif isinstance(spectrum_types, str):
        selected_types = [spectrum_types]
    else:
        selected_types = list(spectrum_types)

    # --- Access and filter data ---
    mainDF = mDF_mgmt.access_mainDF()

    batch_keys = [k for k in kwargs if k.startswith('batch_name')]
    frames_to_concat = []
    for key in batch_keys:
        if key in kwargs:
            temp_df = mainDF[mainDF['batch_file_name'] == kwargs[key]].copy()
            frames_to_concat.append(temp_df)

    function_data = pd.concat(frames_to_concat, ignore_index=True)
    function_data = function_data[function_data[' SimReturnCode'] == 0]

    spectrum = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
    full_names_spectrums_here = spectrums.read_spectrums()

    # --- Build display titles and spectrum metadata ---
    for i, spec in enumerate(spectrum):
        spec_data = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]

        target_str = str(spec_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].iloc[0]).strip()
        extracted_target = []
        for part in target_str.split(';'):
            if ':' not in part:
                continue
            tokens = part.split(':')
            prefix = tokens[0].strip()
            numbers = []
            for x in tokens[1:]:
                try:
                    numbers.append(round(float(x), 4))
                except ValueError:
                    continue
            if prefix == 'f':
                extracted_target.extend(numbers[:1])
            elif prefix == 'Szz':
                non_zeros = [n for n in numbers if n != 0.0]
                extracted_target.extend(non_zeros[:5])
            else:
                extracted_target.extend(numbers)

        f_val1, *szz_vals1 = extracted_target

        ref_parts = full_names_spectrums_here[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.strip().str.split(';')
        ref_parts_backup = full_names_spectrums_here['IncWaveBackupName'].str.strip().str.split(';')

        def extract_rounded(row_parts):
            if not isinstance(row_parts, list):
                return []
            vals = []
            for part in row_parts:
                if ':' not in part:
                    continue
                tokens = part.split(':')
                prefix = tokens[0].strip()
                numbers = []
                for x in tokens[1:]:
                    try:
                        numbers.append(round(float(x), 4))
                    except ValueError:
                        continue
                if prefix == 'f':
                    vals.extend(numbers[:1])
                elif prefix == 'Szz':
                    non_zeros = [n for n in numbers if n != 0.0]
                    vals.extend(non_zeros[:5])
                else:
                    vals.extend(numbers)
            return vals

        extracted_data = ref_parts.apply(extract_rounded)
        extracted_data_backup = ref_parts_backup.apply(extract_rounded)

        matches = full_names_spectrums_here[extracted_data.apply(lambda x: x == [f_val1] + szz_vals1)]
        matches_backup = full_names_spectrums_here[extracted_data_backup.apply(lambda x: x == [f_val1] + szz_vals1)]

        def build_display_title(row):
            match row['spectrum_type']:
                case "bretschneider":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:4]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "BretHFP":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "BretSFP":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "spotter":
                    return f"{row['spectrum_id']}, {row['spectrum_type']}"
                case "regular":
                    return f"{row['spectrum_id']}, Mono, Hs = {str(row['significantWaveHeight'])[:4]}, T = {str(row['peakPeriod'])[:4]}"
                case "regularHFP":
                    return f"{row['spectrum_id']}, MonoHFP, Hs = {str(row['significantWaveHeight'])[:4]}, T = {str(row['peakPeriod'])[:4]}"
                case _:
                    return f"{row['spectrum_id']}, Wildcard Spectrum"

        if not matches.empty:
            matching_row = matches.iloc[0]
            all_possible_types = matches['spectrum_type'].unique().tolist()
        elif not matches_backup.empty:
            matching_row = matches_backup.iloc[0]
            all_possible_types = matches_backup['spectrum_type'].unique().tolist()
        else:
            display_title = target_str[0:12]
            spectrum_type = "unknown"
            function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'display_title'] = display_title
            function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'spectrum_type'] = spectrum_type
            function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'possible_spectrum_types'] = spectrum_type
            function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'color'] = spectrums.get_color_for_spectrum_type(spectrum_type)
            continue

        display_title = build_display_title(matching_row)
        spectrum_type = matching_row['spectrum_type']

        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'display_title'] = str(display_title)
        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'spectrum_id'] = matching_row['spectrum_id']
        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'spectrum_type'] = spectrum_type
        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'possible_spectrum_types'] = '|'.join(str(t) for t in all_possible_types)
        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'color'] = spectrums.get_color_for_spectrum_type(matching_row['spectrum_type'])

    # --- Filter to selected spectrum types ---
    if selected_types is not None:
        function_data = function_data[function_data['spectrum_type'].isin(selected_types)]
    # --- Filter to a single spectrum ID if specified ---        
    if spectrum_id is not None:
        function_data = function_data[function_data['spectrum_id'] == spectrum_id]

    # Re-sync spectrum list to only those still present in function_data
    spectrum = [s for s in spectrum if s in function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].values]

    # --- Sort spectrums by embedded ID in their display title ---
    title_map = function_data.set_index(' IncWaveSpectrumType;IncWaveSpectrumParams')['display_title'].to_dict()

    def sort_by_embedded_id(spectrum_key):
        match = re.search(r'\d+', str(spectrum_key))
        return int(match.group()) if match else 99999

    spectrum = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
    spectrum = sorted(spectrum, key=lambda x: sort_by_embedded_id(title_map.get(x, "")))

    # --- Group spectrums by root ID (text before first comma in display title) ---
    groups = defaultdict(list)
    for spec in spectrum:
        sample_name = str(function_data[
            function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec
        ]['display_title'].iloc[0])
        group_key = sample_name.split(',', 1)[0]
        groups[group_key].append(spec)

    # --- Build subplot grid ---
    n_groups = len(groups)
    rows = math.ceil(n_groups / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(width, heightper * rows), constrained_layout=True)
    axes_flat = np.atleast_1d(axes).flatten()

    # --- Plot each group ---
    for i, (prefix, spec_list) in enumerate(groups.items()):
        ax = axes_flat[i]

        for spec in spec_list:
            spec_data = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]
            avg_data = spec_data.groupby(' ScaleFactor')[metric].mean().reset_index()

            ax.plot(
                avg_data[' ScaleFactor'],
                avg_data[metric],
                label=spec_data['display_title'].iloc[0],
                marker='o',
                linestyle='-',
                linewidth=3,
                color=spec_data['color'].iloc[0]
            )

        ax.set_title(f"Spectrum: {prefix}", fontsize=fontsizetitle)
        ax.set_xlabel('Scale Factor', fontsize=fontsizelabel)
        ax.set_ylabel(verticaltitle, fontsize=fontsizelabel)
        ax.legend(fontsize=fontsizelabel)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.tick_params(axis='both', labelsize=16)

    # --- Remove unused axes ---
    for j in range(i + 1, len(axes_flat)):
        fig.delaxes(axes_flat[j])

    # --- Save ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(current_dir, name)
    plt.savefig(save_path, dpi=600, bbox_inches='tight', transparent=False)
    #plt.show()

def slide2seastates(
    name="hs_tp_spotter.png",
    highlight=True,
    highlight_color="#39FF14",
    highlight_id = None,
    fontsizetitle=24,
    fontsizelabel=20,
    title = 'Significant Wave Height vs Frequency',
    width=16,
    heightper=9,
    base_marker_size=9,
    highlight_width=1.75,
    **kwargs,
):
    """
    Presentation-ready scatter plot of Significant Wave Height vs Frequency
    for spotter spectrums only.

    All spotter spectrums are plotted uniformly. If batch_name kwargs are
    provided and highlight=True, those that have associated successful simulation
    runs are highlighted with a distinct marker outline color and a separate
    legend entry.

    Parameters
    ----------
    name : str
        Output filename, saved relative to this file's directory.
    highlight : bool
        Whether to visually highlight spectrums with associated run data.
        Requires at least one batch_name kwarg to have any effect. Default True.
    highlight_color : str
        Matplotlib-compatible color for the highlighted marker outline.
        Default is neon green "#39FF14".
    fontsizetitle : int
        Font size for the plot title.
    fontsizelabel : int
        Font size for axis labels and legend text.
    width : int
        Figure width in inches.
    heightper : int
        Figure height in inches.
    base_marker_size : int or float
        Marker size (scatter s = base_marker_size ** 2).
    **kwargs
        batch_name, batch_name2, batch_name3, ... : str
            Batch file name strings (values of 'batch_file_name' column in
            mainDF) used to identify which spotter spectrums have successfully
            run simulation data (SimReturnCode == 0).

    Returns
    -------
    None
        Saves the figure to disk at the resolved save_path.

    Examples
    --------
    # No highlight — just plot all spotter spectrums
    plot_hs_tp_spotter(highlight=False)

    # Highlight those with run data from two batches
    plot_hs_tp_spotter(
        name="hs_tp_spotter_highlighted.png",
        batch_name="batch_results_20260213182532",
        batch_name2="batch_results_20260211181904",
    )
    """

    # ── 1. Load and filter to spotter spectrums only ──────────────────────────
    df = spectrums.read_spectrums()
    df = df[df['spectrum_type'] == 'spotter'].copy()
    df = df.dropna(subset=['peakPeriod', 'significantWaveHeight', 'spectrum_id']).copy()
    df = df[df['peakPeriod'] > 0].copy()
    df['frequency_hz'] = 1.0 / df['peakPeriod']

    # ── 2. Resolve highlighted spectrum IDs from batch data ───────────────────
    highlighted_ids = set()
    batch_keys = sorted(k for k in kwargs if k.startswith('batch_name'))

    if highlight and batch_keys:
        mainDF = mDF_mgmt.access_mainDF()

        frames = []
        for key in batch_keys:
            temp_df = mainDF[mainDF['batch_file_name'] == kwargs[key]].copy()
            frames.append(temp_df)

        if frames:
            function_data = pd.concat(frames, ignore_index=True)
            function_data = function_data[function_data[' SimReturnCode'] == 0]

            full_names = spectrums.read_spectrums()

            # Pre-extract rounded params for every row in the reference table
            ref_extracted = full_names[
                ' IncWaveSpectrumType;IncWaveSpectrumParams'
            ].str.strip().apply(_extract_spectrum_params)

            ref_extracted_backup = full_names[
                'IncWaveBackupName'
            ].str.strip().apply(_extract_spectrum_params)

            unique_specs = function_data[
                ' IncWaveSpectrumType;IncWaveSpectrumParams'
            ].unique()

            for spec_str in unique_specs:
                target = _extract_spectrum_params(spec_str)
                if not target:
                    continue

                matches = full_names[ref_extracted.apply(lambda x: x == target)]
                if matches.empty:
                    matches = full_names[ref_extracted_backup.apply(lambda x: x == target)]

                if not matches.empty:
                    spotter_matches = matches[matches['spectrum_type'] == 'spotter']
                    highlighted_ids.update(spotter_matches['spectrum_id'].tolist())

    if highlight and highlight_id is not None:
        highlighted_ids.add(highlight_id)

    # ── 3. Split into highlighted / non-highlighted subsets ───────────────────
    df_base = df[~df['spectrum_id'].isin(highlighted_ids)]
    df_hi   = df[ df['spectrum_id'].isin(highlighted_ids)]

    spotter_color = spectrums.get_color_for_spectrum_type('spotter')
    marker_s = base_marker_size ** 2

    # ── 4. Build figure ───────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(width, heightper), constrained_layout=True)

    # Base (non-highlighted) points
    if not df_base.empty:
        ax.scatter(
            df_base['frequency_hz'],
            df_base['significantWaveHeight'],
            color=spotter_color,
            edgecolors='black',
            linewidths=0.75,
            s=marker_s,
            alpha=0.8,
            zorder=2,
            label='Spotter',
        )

    # Highlighted points — drawn on top with distinct outline
    if not df_hi.empty:
        ax.scatter(
            df_hi['frequency_hz'],
            df_hi['significantWaveHeight'],
            color=spotter_color,
            edgecolors=highlight_color,
            linewidths=highlight_width,
            s=marker_s,
            alpha=0.95,
            zorder=3,
            label='Spotter (Run Data)',
        )

    # ── 5. Presentation styling (matches UMERC2026 conventions) ──────────────
    ax.set_title(
        title,
        fontsize=fontsizetitle,
    )
    ax.set_xlabel('Frequency (Hz)', fontsize=fontsizelabel)
    ax.set_ylabel('Significant Wave Height (m)', fontsize=fontsizelabel)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=fontsizelabel)
    ax.tick_params(axis='both', labelsize=16)

    # ── 6. Save ───────────────────────────────────────────────────────────────
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(current_dir, name)
    plt.savefig(save_path, dpi=600, bbox_inches='tight', transparent=False)
    plt.close(fig)
    #plt.show()

def slide3_damping_bar_single_spectrum(
    name="slide3damping_bar_single_spectrum.png",
    spectrum_id=None,
    metric='avg_tot_power',
    fontsizetitle=24,
    fontsizelabel=20,
    width=16,
    heightper=9,
    verticaltitle='Percent Difference from Peak (%)',
    title='Damping Sensitivity by Scale Factor',
    **kwargs
):
    """
    Presentation-ready bar chart of percent difference from the best (peak) damping
    scale factor for a single spectrum. Seeds are averaged per scale factor before
    computing the percent difference. Seed counts are printed to terminal only.

    The bar at the best scale factor will be exactly 0.0% by construction — this
    is computed from the data and never hardcoded.

    Parameters
    ----------
    name : str
        Output filename (saved relative to this file's directory).
    spectrum_id : int or float
        The spectrum ID to isolate and plot.
    metric : str
        DataFrame column to plot on the y-axis.
    fontsizetitle : int
        Font size for the plot title.
    fontsizelabel : int
        Font size for axis labels.
    width : int
        Total figure width in inches.
    heightper : int
        Figure height in inches.
    verticaltitle : str
        Y-axis label.
    title : str
        Main figure title (shown above the spectrum display_title).
    **kwargs
        batch_name, batch_name2, ... : batch file name strings to filter mainDF.
    """
    # ── Access and filter data ────────────────────────────────────────────────
    mainDF     = mDF_mgmt.access_mainDF()
    batch_keys = sorted(k for k in kwargs if k.startswith('batch_name'))
    frames     = [mainDF[mainDF['batch_file_name'] == kwargs[k]].copy()
                  for k in batch_keys if k in kwargs]
    function_data = pd.concat(frames, ignore_index=True)
    function_data = function_data[function_data[' SimReturnCode'] == 0]

    spectrum                  = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
    full_names_spectrums_here = spectrums.read_spectrums()

    # ── Build display titles and spectrum metadata ────────────────────────────
    for spec in spectrum:
        spec_data  = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]
        target_str = str(spec_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].iloc[0]).strip()

        extracted_target = []
        for part in target_str.split(';'):
            if ':' not in part:
                continue
            tokens   = part.split(':')
            prefix_t = tokens[0].strip()
            numbers  = []
            for x in tokens[1:]:
                try:
                    numbers.append(round(float(x), 4))
                except ValueError:
                    continue
            if prefix_t == 'f':
                extracted_target.extend(numbers[:1])
            elif prefix_t == 'Szz':
                extracted_target.extend([n for n in numbers if n != 0.0][:5])
            else:
                extracted_target.extend(numbers)

        if not extracted_target:
            continue
        f_val1, *szz_vals1 = extracted_target
        target_vals        = [f_val1] + szz_vals1

        ref_parts        = full_names_spectrums_here[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.strip().str.split(';')
        ref_parts_backup = full_names_spectrums_here['IncWaveBackupName'].str.strip().str.split(';')

        def extract_rounded(row_parts):
            if not isinstance(row_parts, list):
                return []
            vals = []
            for part in row_parts:
                if ':' not in part:
                    continue
                tokens   = part.split(':')
                prefix_t = tokens[0].strip()
                numbers  = []
                for x in tokens[1:]:
                    try:
                        numbers.append(round(float(x), 4))
                    except ValueError:
                        continue
                if prefix_t == 'f':
                    vals.extend(numbers[:1])
                elif prefix_t == 'Szz':
                    vals.extend([n for n in numbers if n != 0.0][:5])
                else:
                    vals.extend(numbers)
            return vals

        extracted_data        = ref_parts.apply(extract_rounded)
        extracted_data_backup = ref_parts_backup.apply(extract_rounded)
        matches        = full_names_spectrums_here[extracted_data.apply(lambda x: x == target_vals)]
        matches_backup = full_names_spectrums_here[extracted_data_backup.apply(lambda x: x == target_vals)]

        def build_display_title(row):
            match row['spectrum_type']:
                case "bretschneider":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:4]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "BretHFP":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "BretSFP":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "spotter":
                    return f"{row['spectrum_id']}, {row['spectrum_type']}"
                case "regular":
                    return f"{row['spectrum_id']}, Mono, Hs = {str(row['significantWaveHeight'])[:4]}, T = {str(row['peakPeriod'])[:4]}"
                case "regularHFP":
                    return f"{row['spectrum_id']}, MonoHFP, Hs = {str(row['significantWaveHeight'])[:4]}, T = {str(row['peakPeriod'])[:4]}"
                case _:
                    return f"{row['spectrum_id']}, Wildcard Spectrum"

        if not matches.empty:
            matching_row       = matches.iloc[0]
            all_possible_types = matches['spectrum_type'].unique().tolist()
        elif not matches_backup.empty:
            matching_row       = matches_backup.iloc[0]
            all_possible_types = matches_backup['spectrum_type'].unique().tolist()
        else:
            mask = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec
            function_data.loc[mask, 'display_title']           = target_str[:12]
            function_data.loc[mask, 'spectrum_type']           = 'unknown'
            function_data.loc[mask, 'possible_spectrum_types'] = 'unknown'
            function_data.loc[mask, 'color']                   = spectrums.get_color_for_spectrum_type('unknown')
            continue

        display_title = build_display_title(matching_row)
        spectrum_type = matching_row['spectrum_type']
        mask          = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec
        function_data.loc[mask, 'display_title']           = str(display_title)
        function_data.loc[mask, 'spectrum_id']             = matching_row['spectrum_id']
        function_data.loc[mask, 'spectrum_type']           = spectrum_type
        function_data.loc[mask, 'possible_spectrum_types'] = '|'.join(str(t) for t in all_possible_types)
        function_data.loc[mask, 'color']                   = spectrums.get_color_for_spectrum_type(spectrum_type)

    # ── Filter to the requested spectrum_id ──────────────────────────────────
    if spectrum_id is not None:
        function_data = function_data[function_data['spectrum_id'] == spectrum_id]

    if function_data.empty:
        print(f"[ERROR] No data found for spectrum_id={spectrum_id}. Aborting.")
        return

    # ── Compute per-scale-factor averages and seed counts ────────────────────
    # Scale factors sorted numerically ascending
    scale_factors    = sorted(function_data[' ScaleFactor'].unique())
    avg_by_sf        = {}
    seed_count_by_sf = {}

    for sf in scale_factors:
        sf_data             = function_data[function_data[' ScaleFactor'] == sf]
        avg_by_sf[sf]       = sf_data[metric].mean()
        seed_count_by_sf[sf] = sf_data[' Seed'].nunique()

    # ── Terminal report ───────────────────────────────────────────────────────
    print(f"\n[INFO] Seed counts per scale factor for spectrum_id={spectrum_id}:")
    for sf in scale_factors:
        print(f"  Scale Factor {sf:>8}: {seed_count_by_sf[sf]} seed(s) averaged  |  "
              f"avg {metric} = {avg_by_sf[sf]:.4f}")

    max_avg = max(avg_by_sf.values())
    best_sf = max(avg_by_sf, key=avg_by_sf.get)
    print(f"\n[INFO] Best scale factor: {best_sf}  |  avg {metric} = {max_avg:.4f}")

    # ── Percent difference from peak (all ≤ 0; best SF = 0.0 from data) ─────
    pct_diffs = [(avg_by_sf[sf] - max_avg) / max_avg * 100 for sf in scale_factors]
    x_labels  = [str(sf) for sf in scale_factors]

    display_title = function_data['display_title'].iloc[0]
    color         = function_data['color'].iloc[0]

    # ── Plot ─────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(width, heightper), constrained_layout=True)

    bars = ax.bar(x_labels, pct_diffs, color=color, edgecolor='black', linewidth=0.8)
    ax.bar_label(bars, fmt='%.1f%%', padding=3, fontsize=fontsizelabel - 4)

    ax.set_title(f"{title}\n{display_title}", fontsize=fontsizetitle)
    ax.set_xlabel('Scale Factor', fontsize=fontsizelabel)
    ax.set_ylabel(verticaltitle, fontsize=fontsizelabel)
    ax.axhline(y=0, linewidth=1, color='k')
    ax.grid(True, linestyle='--', alpha=0.5, axis='y')
    ax.tick_params(axis='both', labelsize=16)

    min_y  = min(pct_diffs)
    max_y  = max(pct_diffs)
    buffer = max(0.1 * abs(max_y - min_y), 1.0)
    ax.set_ylim(min_y - buffer, max_y + buffer)

    # ── Save ─────────────────────────────────────────────────────────────────
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path   = os.path.join(current_dir, name)
    plt.savefig(save_path, dpi=600, bbox_inches='tight', transparent=False)
    print(f"\n[INFO] Saved figure to: {save_path}")
    #plt.show()
       
def slide3_damping_violin_by_scalefactor(
    name="damping_violin_by_scalefactor.png",
    metric='avg_tot_power',
    fontsizetitle=24,
    fontsizelabel=20,
    width=16,
    heightper=9,
    verticaltitle='Percent Difference from Spotter Peak (%)',
    title='Damping Scale Factor Distribution across Spectra',
    **kwargs
):
    """
    Presentation-ready violin plot showing the distribution of percent difference
    from the spotter peak energy, with one violin per damping scale factor.

    Each data point in a violin represents one spectrum group's spotter-averaged
    energy at that scale factor, expressed as a percent difference from that
    group's own spotter peak. Scale factors are ordered numerically ascending.
    Groups with no spotter spectrum are skipped with a terminal warning.

    Parameters
    ----------
    name : str
        Output filename (saved relative to this file's directory).
    metric : str
        DataFrame column to use for energy values.
    fontsizetitle : int
        Font size for the plot title.
    fontsizelabel : int
        Font size for axis labels.
    width : int
        Minimum figure width in inches (expands if many scale factors).
    heightper : int
        Figure height in inches.
    verticaltitle : str
        Y-axis label.
    title : str
        Figure title.
    **kwargs
        batch_name, batch_name2, ... : batch file name strings to filter mainDF.
    """
    # ── Access and filter data ────────────────────────────────────────────────
    mainDF     = mDF_mgmt.access_mainDF()
    batch_keys = sorted(k for k in kwargs if k.startswith('batch_name'))
    frames     = [mainDF[mainDF['batch_file_name'] == kwargs[k]].copy()
                  for k in batch_keys if k in kwargs]
    function_data = pd.concat(frames, ignore_index=True)
    function_data = function_data[function_data[' SimReturnCode'] == 0]

    spectrum                  = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
    full_names_spectrums_here = spectrums.read_spectrums()

    # ── Build display titles and spectrum metadata ────────────────────────────
    for spec in spectrum:
        spec_data  = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]
        target_str = str(spec_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].iloc[0]).strip()

        extracted_target = []
        for part in target_str.split(';'):
            if ':' not in part:
                continue
            tokens   = part.split(':')
            prefix_t = tokens[0].strip()
            numbers  = []
            for x in tokens[1:]:
                try:
                    numbers.append(round(float(x), 4))
                except ValueError:
                    continue
            if prefix_t == 'f':
                extracted_target.extend(numbers[:1])
            elif prefix_t == 'Szz':
                extracted_target.extend([n for n in numbers if n != 0.0][:5])
            else:
                extracted_target.extend(numbers)

        if not extracted_target:
            continue
        f_val1, *szz_vals1 = extracted_target
        target_vals        = [f_val1] + szz_vals1

        ref_parts        = full_names_spectrums_here[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.strip().str.split(';')
        ref_parts_backup = full_names_spectrums_here['IncWaveBackupName'].str.strip().str.split(';')

        def extract_rounded(row_parts):
            if not isinstance(row_parts, list):
                return []
            vals = []
            for part in row_parts:
                if ':' not in part:
                    continue
                tokens   = part.split(':')
                prefix_t = tokens[0].strip()
                numbers  = []
                for x in tokens[1:]:
                    try:
                        numbers.append(round(float(x), 4))
                    except ValueError:
                        continue
                if prefix_t == 'f':
                    vals.extend(numbers[:1])
                elif prefix_t == 'Szz':
                    vals.extend([n for n in numbers if n != 0.0][:5])
                else:
                    vals.extend(numbers)
            return vals

        extracted_data        = ref_parts.apply(extract_rounded)
        extracted_data_backup = ref_parts_backup.apply(extract_rounded)
        matches        = full_names_spectrums_here[extracted_data.apply(lambda x: x == target_vals)]
        matches_backup = full_names_spectrums_here[extracted_data_backup.apply(lambda x: x == target_vals)]

        def build_display_title(row):
            match row['spectrum_type']:
                case "bretschneider":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:4]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "BretHFP":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "BretSFP":
                    return f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, Hs = {str(row['significantWaveHeight'])[:4]}, Tp = {str(row['peakPeriod'])[:4]}"
                case "spotter":
                    return f"{row['spectrum_id']}, {row['spectrum_type']}"
                case "regular":
                    return f"{row['spectrum_id']}, Mono, Hs = {str(row['significantWaveHeight'])[:4]}, T = {str(row['peakPeriod'])[:4]}"
                case "regularHFP":
                    return f"{row['spectrum_id']}, MonoHFP, Hs = {str(row['significantWaveHeight'])[:4]}, T = {str(row['peakPeriod'])[:4]}"
                case _:
                    return f"{row['spectrum_id']}, Wildcard Spectrum"

        if not matches.empty:
            matching_row       = matches.iloc[0]
            all_possible_types = matches['spectrum_type'].unique().tolist()
        elif not matches_backup.empty:
            matching_row       = matches_backup.iloc[0]
            all_possible_types = matches_backup['spectrum_type'].unique().tolist()
        else:
            mask = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec
            function_data.loc[mask, 'display_title']           = target_str[:12]
            function_data.loc[mask, 'spectrum_type']           = 'unknown'
            function_data.loc[mask, 'possible_spectrum_types'] = 'unknown'
            function_data.loc[mask, 'color']                   = spectrums.get_color_for_spectrum_type('unknown')
            continue

        display_title = build_display_title(matching_row)
        spectrum_type = matching_row['spectrum_type']
        mask          = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec
        function_data.loc[mask, 'display_title']           = str(display_title)
        function_data.loc[mask, 'spectrum_id']             = matching_row['spectrum_id']
        function_data.loc[mask, 'spectrum_type']           = spectrum_type
        function_data.loc[mask, 'possible_spectrum_types'] = '|'.join(str(t) for t in all_possible_types)
        function_data.loc[mask, 'color']                   = spectrums.get_color_for_spectrum_type(spectrum_type)

    # ── Sort spectrums by embedded ID in display title ────────────────────────
    title_map = function_data.set_index(
        ' IncWaveSpectrumType;IncWaveSpectrumParams'
    )['display_title'].to_dict()

    def sort_by_embedded_id(key):
        m = re.search(r'\d+', str(key))
        return int(m.group()) if m else 99999

    spectrum = sorted(spectrum, key=lambda x: sort_by_embedded_id(title_map.get(x, '')))

    # ── Group by root spectrum prefix ─────────────────────────────────────────
    groups = defaultdict(list)
    for spec in spectrum:
        sample_name = str(
            function_data[
                function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec
            ]['display_title'].iloc[0]
        )
        groups[sample_name.split(',', 1)[0]].append(spec)

    # ── Accumulate pct-diff per scale factor across groups ────────────────────
    data_by_sf = defaultdict(list)   # {scale_factor: [pct_diff, ...]}

    for prefix, spec_list in groups.items():
        group_data    = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].isin(spec_list)]

        # Identify spotter baseline using possible_spectrum_types (mirrors original logic)
        spec_dat_spot = group_data[
            group_data['possible_spectrum_types'].str.lower().str.contains('spotter', na=False)
        ]

        if spec_dat_spot.empty:
            spectrum_ids = group_data['spectrum_id'].unique().tolist()
            print(f"\n[WARNING] Group '{prefix}' (spectrum IDs: {spectrum_ids}) has no "
                  f"spotter spectrum. Skipping — this group will not contribute data "
                  f"points to the violin.")
            continue

        # Pin to a single spotter string if multiple exist
        spec_spot              = spec_dat_spot[' IncWaveSpectrumType;IncWaveSpectrumParams'].iloc[0]
        unique_spotter_strings = spec_dat_spot[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
        if len(unique_spotter_strings) > 1:
            print(f"\n[WARNING] Group '{prefix}' has {len(unique_spotter_strings)} distinct "
                  f"spotter strings. Pinning to first: '{spec_spot}'. "
                  f"Others ignored: {unique_spotter_strings[1:].tolist()}")
        spec_dat_spot = spec_dat_spot[
            spec_dat_spot[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec_spot
        ]

        avg_data_spot = spec_dat_spot.groupby(' ScaleFactor')[metric].mean().reset_index()
        if avg_data_spot.empty:
            print(f"\n[WARNING] Baseline data empty for group '{prefix}'. Skipping.")
            continue

        spot_max_val = avg_data_spot[metric].max()

        # One data point per scale factor for this group
        for _, row in avg_data_spot.iterrows():
            sf       = row[' ScaleFactor']
            pct_diff = (row[metric] - spot_max_val) / spot_max_val * 100
            data_by_sf[sf].append(pct_diff)

    if not data_by_sf:
        print("[ERROR] No data accumulated. Check that spotter spectra are present in the batches.")
        return

    # ── Sort scale factors numerically ascending ──────────────────────────────
    sorted_sfs  = sorted(data_by_sf.keys())
    violin_data = [data_by_sf[sf] for sf in sorted_sfs]
    x_labels    = [str(sf) for sf in sorted_sfs]
    positions   = list(range(len(sorted_sfs)))

    # Assign colors via tab10 cycling (scale factors have no intrinsic color)
    cmap   = plt.get_cmap('tab10')
    colors = [cmap(i % 10) for i in range(len(sorted_sfs))]

    # ── Draw plot ─────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(
        figsize=(max(width, len(sorted_sfs) * 1.8), heightper),
        constrained_layout=True
    )

    drawable     = [i for i, v in enumerate(violin_data) if len(v) >= 2]
    single_point = [i for i, v in enumerate(violin_data) if len(v) <  2]

    if drawable:
        parts = ax.violinplot(
            [violin_data[i] for i in drawable],
            positions=[positions[i] for i in drawable],
            showmeans=True,
            showmedians=True,
            showextrema=True
        )
        for pc, idx in zip(parts['bodies'], drawable):
            pc.set_facecolor(colors[idx])
            pc.set_edgecolor('black')
            pc.set_alpha(0.7)
        for partname in ('cbars', 'cmins', 'cmaxes', 'cmeans', 'cmedians'):
            if partname in parts:
                parts[partname].set_edgecolor('black')
                parts[partname].set_linewidth(1.2)

        for i, idx in enumerate(drawable):
            data       = violin_data[idx]
            mean_val   = np.mean(data)
            median_val = np.median(data)
            ax.annotate(
                f"Mean: {mean_val:.2f}",
                xy=(positions[idx], mean_val), xytext=(-15, 10),
                textcoords='offset points', fontsize=fontsizelabel - 12,
                color='blue', arrowprops=dict(arrowstyle='->', color='blue')
            )
            ax.annotate(
                f"Median: {median_val:.2f}",
                xy=(positions[idx], median_val), xytext=(-15, -15),
                textcoords='offset points', fontsize=fontsizelabel - 12,
                color='green', arrowprops=dict(arrowstyle='->', color='green')
            )

    # ── Overlay jittered individual data points ───────────────────────────────
    rng = np.random.default_rng(seed=42)
    for i, vals in enumerate(violin_data):
        jitter = rng.uniform(-0.06, 0.06, size=len(vals))
        ax.scatter(
            np.full(len(vals), i) + jitter,
            vals,
            color='black',
            s=40,
            zorder=3,
            alpha=0.3,
            label='_nolegend_'
        )

    # Single-point categories: draw a prominent marker; no on-plot n= annotation
    for i in single_point:
        ax.scatter(
            [i], violin_data[i],
            color=colors[i], s=120, zorder=4,
            edgecolors='black', linewidth=1.2
        )

    ax.set_xticks(positions)
    ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=16)
    ax.set_xlabel('Scale Factor', fontsize=fontsizelabel)
    ax.set_ylabel(verticaltitle, fontsize=fontsizelabel)
    ax.set_title(title, fontsize=fontsizetitle)
    ax.axhline(y=0, linewidth=1, color='k', linestyle='--', alpha=0.6)
    ax.grid(True, alpha=0.3, axis='y')
    ax.tick_params(axis='y', labelsize=16)

    # ── Save ─────────────────────────────────────────────────────────────────
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path   = os.path.join(current_dir, name)
    plt.savefig(save_path, dpi=600, bbox_inches='tight', transparent=False)
    print(f"\n[INFO] Saved figure to: {save_path}")
    #plt.show()

def slide6spotter(spectra=(114, 83), name="slide1spotter.png", types=('spotter', 'BretSFP'), fontsizetitle=24, fontsizelabel=20, width=16, heightper=9):
    """
    Plots multiple spectrums on the same axes for comparison, with presentation-ready styling.

    -------
    Parameters:
        spectra: tuple of spectrum numbers to plot side by side (e.g. (114, 83))
        name: output filename (default 'slide1spotter.png')
        types: list of spectrum types to include (e.g., ["spotter", "bretschneider", "jonswap"]) or 'all' for all types
        fontsizetitle: font size for subplot titles (default 24)
        fontsizelabel: font size for axis labels and legend (default 20)
        width: figure width in inches (default 16)
        heightper: figure height per row in inches (default 9)
    ------
    Returns:
        None (saves the plot to disk)
    """
    reo_df = None
    metric_sv = None
    period = False
    n_cols = 2
    plots_per_page = 2
    spectrum_nums = list(spectra)
    total_plots = len(spectrum_nums)

    # Define available models and their plotting styles
    models = {
        "spotter": {"label": "Spotter", "color": spectrums.get_color_for_spectrum_type("spotter"), "fmt": "scatter", "alpha": 0.7, "marker": "o"},
        "bretschneider": {"label": "Bretschneider", "color": spectrums.get_color_for_spectrum_type("bretschneider"), "fmt": "plot"},
        "BretHFP": {"label": "BretHFP", "color": spectrums.get_color_for_spectrum_type("BretHFP"), "fmt": "plot"},
        "BretSFP": {"label": "BretSFP", "color": spectrums.get_color_for_spectrum_type("BretSFP"), "fmt": "plot"},
        "BretTPFP": {"label": "BretTPFP", "color": spectrums.get_color_for_spectrum_type("BretTPFP"), "fmt": "plot"},
        "BretPFP": {"label": "BretPFP", "color": spectrums.get_color_for_spectrum_type("BretPFP"), "fmt": "plot"},
        "jonswap": {"label": "Jonswap", "color": spectrums.get_color_for_spectrum_type("jonswap"), "fmt": "plot", "marker": "x"},
        "regular": {"label": "Regular", "color": spectrums.get_color_for_spectrum_type("regular"), "fmt": "vline", "alpha": 0.65},
        "regularHFP": {"label": "RegularHFP", "color": spectrums.get_color_for_spectrum_type("regularHFP"), "fmt": "vline", "alpha": 0.65}
    }

    # If types is None or 'all', use all keys in the models dict
    if types is None or types == 'all':
        selected_types = list(models.keys())
    elif isinstance(types, str):
        selected_types = [types]
    else:
        selected_types = types

    for start_idx in range(0, total_plots, plots_per_page):

        def sort_by_embedded_id(spectrum_key):
            """
            Extracts the first continuous block of digits from the spectrum key
            to use as a sorting integer. If no number is found, returns a high number.
            """
            match = re.search(r'\d+', str(spectrum_key))
            return int(match.group()) if match else 99999

        spectrum_nums = sorted(spectrum_nums, key=sort_by_embedded_id)

        batch = spectrum_nums[start_idx: start_idx + plots_per_page]
        n_rows = max(1, len(batch) // n_cols)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(width, heightper * n_rows), sharey=True)
        axes = np.atleast_1d(axes).flatten()

        for idx, i in enumerate(batch):
            ax = axes[idx]
            xlabel = 'Period (s)' if period else 'Frequency (Hz)'

            # Dynamic plotting based on selection
            for model_name in selected_types:
                if model_name not in models:
                    continue

                style = models[model_name]
                f, szz = spectrums.spectrum(i, model_name)
                x = 1 / np.array(f) if period else np.array(f)
                szz = np.array(szz) * (np.array(f) ** 2) if period else np.array(szz)

                label = style["label"]

                if style.get("fmt") == "scatter":
                    ax.plot(x, szz, label=label, color=style["color"], alpha=style.get("alpha", 1), marker=style.get("marker"), ms=5.0, linewidth=3)
                elif style.get("fmt") == "vline":
                    ax.axvline(x, color=style["color"], alpha=style.get("alpha", 1), label=label, linewidth=3)
                else:
                    ax.plot(x, szz, label=label, color=style["color"], marker=style.get("marker"), linewidth=3)

            # --- Styling ---
            ax.set_title(f"Spectrum {i}", fontsize=fontsizetitle)
            ax.set_xlabel(xlabel, fontsize=fontsizelabel)
            if idx % 2 == 0:
                ax.set_ylabel('Spectral Density (m^2/Hz)', fontsize=fontsizelabel)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(fontsize=fontsizelabel)
            ax.tick_params(axis='both', labelsize=16)

        for j in range(len(batch), len(axes)):
            fig.delaxes(axes[j])

        plt.tight_layout()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(current_dir, name)
        plt.savefig(save_path, dpi=600, bbox_inches='tight', transparent=False)
        # plt.show()

#############Helpers and such for violin plots
def _load_and_filter(kwargs):
    """Load mainDF, filter by batch_name kwargs, drop failed sims."""
    mainDF     = mDF_mgmt.access_mainDF()
    batch_keys = sorted(k for k in kwargs if k.startswith('batch_name'))
    frames     = [mainDF[mainDF['batch_file_name'] == kwargs[k]].copy()
                  for k in batch_keys if k in kwargs]
    data = pd.concat(frames, ignore_index=True)
    return data[data[' SimReturnCode'] == 0].copy()


def _build_spectrum_metadata(function_data, full_names_spectrums_here):
    """
    Attach display_title, spectrum_id, spectrum_type, possible_spectrum_types,
    and color columns to function_data in-place.  Returns the mutated DataFrame.
    """
    spectrum = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()

    def _extract_rounded(row_parts):
        if not isinstance(row_parts, list):
            return []
        vals = []
        for part in row_parts:
            if ':' not in part:
                continue
            tokens   = part.split(':')
            prefix_t = tokens[0].strip()
            numbers  = []
            for x in tokens[1:]:
                try:
                    numbers.append(round(float(x), 4))
                except ValueError:
                    continue
            if prefix_t == 'f':
                vals.extend(numbers[:1])
            elif prefix_t == 'Szz':
                vals.extend([n for n in numbers if n != 0.0][:5])
            else:
                vals.extend(numbers)
        return vals

    def _build_display_title(row):
        match row['spectrum_type']:
            case "bretschneider":
                return (f"{row['spectrum_id']}, {row['spectrum_type'][:4]}, "
                        f"Hs = {str(row['significantWaveHeight'])[:4]}, "
                        f"Tp = {str(row['peakPeriod'])[:4]}")
            case "BretHFP":
                return (f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, "
                        f"Hs = {str(row['significantWaveHeight'])[:4]}, "
                        f"Tp = {str(row['peakPeriod'])[:4]}")
            case "BretSFP":
                return (f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, "
                        f"Hs = {str(row['significantWaveHeight'])[:4]}, "
                        f"Tp = {str(row['peakPeriod'])[:4]}")
            case "BretTPFP":
                return (f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, "
                        f"Hs = {str(row['significantWaveHeight'])[:4]}, "
                        f"Tp = {str(row['peakPeriod'])[:4]}")
            case "BretPFP":
                return (f"{row['spectrum_id']}, {row['spectrum_type'][:7]}, "
                        f"Hs = {str(row['significantWaveHeight'])[:4]}, "
                        f"Tp = {str(row['peakPeriod'])[:4]}")
            case "spotter":
                return f"{row['spectrum_id']}, {row['spectrum_type']}"
            case "regular":
                return (f"{row['spectrum_id']}, Mono, "
                        f"Hs = {str(row['significantWaveHeight'])[:4]}, "
                        f"T = {str(row['peakPeriod'])[:4]}")
            case "regularHFP":
                return (f"{row['spectrum_id']}, MonoHFP, "
                        f"Hs = {str(row['significantWaveHeight'])[:4]}, "
                        f"T = {str(row['peakPeriod'])[:4]}")
            case _:
                return f"{row['spectrum_id']}, Wildcard Spectrum"

    ref_parts        = full_names_spectrums_here[
        ' IncWaveSpectrumType;IncWaveSpectrumParams'].str.strip().str.split(';')
    ref_parts_backup = full_names_spectrums_here[
        'IncWaveBackupName'].str.strip().str.split(';')
    extracted_data        = ref_parts.apply(_extract_rounded)
    extracted_data_backup = ref_parts_backup.apply(_extract_rounded)

    for spec in spectrum:
        spec_data  = function_data[
            function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]
        target_str = str(
            spec_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].iloc[0]).strip()

        extracted_target = []
        for part in target_str.split(';'):
            if ':' not in part:
                continue
            tokens   = part.split(':')
            prefix_t = tokens[0].strip()
            numbers  = []
            for x in tokens[1:]:
                try:
                    numbers.append(round(float(x), 4))
                except ValueError:
                    continue
            if prefix_t == 'f':
                extracted_target.extend(numbers[:1])
            elif prefix_t == 'Szz':
                extracted_target.extend([n for n in numbers if n != 0.0][:5])
            else:
                extracted_target.extend(numbers)

        if not extracted_target:
            continue
        target_vals = extracted_target

        matches        = full_names_spectrums_here[
            extracted_data.apply(lambda x: x == target_vals)]
        matches_backup = full_names_spectrums_here[
            extracted_data_backup.apply(lambda x: x == target_vals)]

        mask = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec

        if not matches.empty:
            matching_row       = matches.iloc[0]
            all_possible_types = matches['spectrum_type'].unique().tolist()
        elif not matches_backup.empty:
            matching_row       = matches_backup.iloc[0]
            all_possible_types = matches_backup['spectrum_type'].unique().tolist()
        else:
            function_data.loc[mask, 'display_title']           = target_str[:12]
            function_data.loc[mask, 'spectrum_type']           = 'unknown'
            function_data.loc[mask, 'possible_spectrum_types'] = 'unknown'
            function_data.loc[mask, 'color']                   = spectrums.get_color_for_spectrum_type('unknown')
            continue

        if len(all_possible_types) > 1:
            print(f"\n[INFO] Ambiguous match for '{target_str[:40]}': "
                  f"maps to {all_possible_types}.")

        display_title = _build_display_title(matching_row)
        spectrum_type = matching_row['spectrum_type']

        function_data.loc[mask, 'display_title']           = str(display_title)
        function_data.loc[mask, 'spectrum_id']             = matching_row['spectrum_id']
        function_data.loc[mask, 'spectrum_type']           = spectrum_type
        function_data.loc[mask, 'possible_spectrum_types'] = '|'.join(
            str(t) for t in all_possible_types)
        function_data.loc[mask, 'color']                   = spectrums.get_color_for_spectrum_type(
            spectrum_type)

    return function_data


def _sort_spectrum_keys(spectrum_list, title_map):
    """Sort spectrum strings by embedded numeric ID in their display title."""
    def _key(s):
        m = re.search(r'\d+', str(title_map.get(s, '')))
        return int(m.group()) if m else 99999
    return sorted(spectrum_list, key=_key)


def _group_by_root_id(spectrum_list, function_data):
    """Group spectrum strings by the text before the first comma in display_title."""
    groups = defaultdict(list)
    for spec in spectrum_list:
        name = str(function_data[
            function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec
        ]['display_title'].iloc[0])
        groups[name.split(',', 1)[0]].append(spec)
    return groups


def _type_label(spectrum_type):
    """Normalise a raw spectrum_type string to a consistent violin category label."""
    st = str(spectrum_type)
    if 'bret' in st.lower():
        if 'HFP' in st:
            return 'BretHFP'
        if 'SFP' in st:
            return 'BretSFP'
        if 'TPFP' in st:
            return 'BretTPFP'
        if 'PFP' in st:
            return 'BretPFP'
        return 'Bretschneider'
    return st


def _resolve_spotter(group_data, prefix, metric):
    """
    Identify and pin the single spotter spectrum string for a group.
    Returns (spec_dat_spot filtered to one string, avg_data_spot, spot_max_val)
    or (None, None, None) if the group should be skipped.
    """
    spec_dat_spot = group_data[
        group_data['possible_spectrum_types'].str.lower().str.contains('spotter', na=False)
    ]

    if spec_dat_spot.empty:
        spectrum_ids = group_data['spectrum_id'].unique().tolist()
        print(f"\n[WARNING] Group '{prefix}' (IDs: {spectrum_ids}) has no spotter. Skipping.")
        return None, None, None

    spec_spot              = spec_dat_spot[' IncWaveSpectrumType;IncWaveSpectrumParams'].iloc[0]
    unique_spotter_strings = spec_dat_spot[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
    if len(unique_spotter_strings) > 1:
        print(f"\n[WARNING] Group '{prefix}' has {len(unique_spotter_strings)} spotter strings. "
              f"Pinning to first: '{spec_spot}'.")
    spec_dat_spot = spec_dat_spot[
        spec_dat_spot[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec_spot
    ]

    avg_data_spot = spec_dat_spot.groupby(' ScaleFactor')[metric].mean().reset_index()
    if avg_data_spot.empty:
        print(f"\n[WARNING] Baseline data empty for group '{prefix}'. Skipping.")
        return None, None, None

    spot_max_val = avg_data_spot[metric].max()
    return spec_dat_spot, avg_data_spot, spot_max_val


def _draw_violin(ax, positions, violin_data, violin_colors):
    """
    Draw violin bodies with jittered scatter overlay, mean/median annotations,
    and single-point 'n=1' markers.  Returns the violinplot parts dict or None.
    """
    drawable     = [i for i, v in enumerate(violin_data) if len(v) >= 2]
    single_point = [i for i, v in enumerate(violin_data) if len(v) <  2]

    parts = None
    if drawable:
        parts = ax.violinplot(
            [violin_data[i] for i in drawable],
            positions=[positions[i] for i in drawable],
            showmeans=True,
            showmedians=True,
            showextrema=True
        )
        for pc, idx in zip(parts['bodies'], drawable):
            pc.set_facecolor(violin_colors[idx])
            pc.set_edgecolor('black')
            pc.set_alpha(0.7)
        for partname in ('cbars', 'cmins', 'cmaxes', 'cmeans', 'cmedians'):
            if partname in parts:
                parts[partname].set_edgecolor('black')
                parts[partname].set_linewidth(1.2)

        for i, idx in enumerate(drawable):
            data       = violin_data[idx]
            mean_val   = float(np.mean(data))
            median_val = float(np.median(data))
            ax.annotate(
                f"Mean: {mean_val:.2f}",
                xy=(positions[idx], mean_val),
                xytext=(-15, 10),
                textcoords='offset points',
                fontsize=8,
                color='blue',
                arrowprops=dict(arrowstyle='->', color='blue')
            )
            ax.annotate(
                f"Median: {median_val:.2f}",
                xy=(positions[idx], median_val),
                xytext=(-15, -10),
                textcoords='offset points',
                fontsize=8,
                color='green',
                arrowprops=dict(arrowstyle='->', color='green')
            )

    rng = np.random.default_rng(seed=42)
    for i, vals in enumerate(violin_data):
        jitter = rng.uniform(-0.06, 0.06, size=len(vals))
        ax.scatter(
            np.full(len(vals), positions[i]) + jitter,
            vals,
            color='black',
            s=40,
            zorder=3,
            alpha=0.8,
            label='_nolegend_'
        )

    for i in single_point:
        ax.annotate(
            'n=1',
            xy=(positions[i], violin_data[i][0]),
            xytext=(0, 6),
            textcoords='offset points',
            ha='center',
            fontsize=7,
            color='dimgray'
        )

    return parts


def _save_figure(fig, name):
    """Save figure at 600 dpi to the same directory as this file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path   = os.path.join(current_dir, name)
    fig.savefig(save_path, dpi=600, bbox_inches='tight', transparent=False)
    print(f"\n[SAVED] {save_path}")


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 1 — Bar chart: % diff from best scale factor, single spectrum
# ═════════════════════════════════════════════════════════════════════════════

def slide1_damping_bar_single_spectrum(
    name="damping_bar_single_spectrum.png",
    spectrum_id=None,
    metric='avg_tot_power',
    fontsizetitle=24,
    fontsizelabel=20,
    width=16,
    heightper=9,
    verticaltitle='Percent Difference from Peak (%)',
    title='Damping Sensitivity by Scale Factor',
    **kwargs
):
    """
    Presentation-ready bar chart of percent difference from the best (peak) damping
    scale factor for a single spectrum. Seeds are averaged per scale factor before
    computing the percent difference. Seed counts are printed to terminal only.

    The bar at the best scale factor will be exactly 0.0% by construction — this
    is computed from the data and never hardcoded.

    Parameters
    ----------
    name : str
        Output filename (saved relative to this file's directory).
    spectrum_id : int or float
        The spectrum ID to isolate and plot.
    metric : str
        DataFrame column to plot on the y-axis.
    fontsizetitle : int
        Font size for the plot title.
    fontsizelabel : int
        Font size for axis labels.
    width : int
        Total figure width in inches.
    heightper : int
        Figure height in inches.
    verticaltitle : str
        Y-axis label.
    title : str
        Main figure title (shown above the spectrum display_title).
    **kwargs
        batch_name, batch_name2, ... : batch file name strings to filter mainDF.
    """
    # ── Load, filter, annotate ────────────────────────────────────────────────
    function_data = _load_and_filter(kwargs)
    function_data = _build_spectrum_metadata(function_data, spectrums.read_spectrums())

    # ── Isolate single spectrum ───────────────────────────────────────────────
    if spectrum_id is not None:
        function_data = function_data[function_data['spectrum_id'] == spectrum_id]

    if function_data.empty:
        print(f"[ERROR] No data found for spectrum_id={spectrum_id}. Aborting.")
        return

    # ── Compute per-scale-factor averages and seed counts ────────────────────
    scale_factors = sorted(function_data[' ScaleFactor'].unique())
    avg_by_sf     = {}
    n_seeds_by_sf = {}

    print(f"\n[INFO] Seed summary — spectrum_id={spectrum_id}, metric={metric}:")
    print(f"  {'Scale Factor':>14} | {'N Seeds':>7} | {'Avg Metric':>14}")
    print(f"  {'-'*14}-+-{'-'*7}-+-{'-'*14}")
    for sf in scale_factors:
        sf_data        = function_data[function_data[' ScaleFactor'] == sf]
        avg_by_sf[sf]  = sf_data[metric].mean()
        n_seeds_by_sf[sf] = sf_data[' Seed'].nunique()
        print(f"  {sf:>14.4f} | {n_seeds_by_sf[sf]:>7} | {avg_by_sf[sf]:>14.4f}")

    # ── Percent difference from best (peak) scale factor ─────────────────────
    best_sf   = max(avg_by_sf, key=avg_by_sf.get)
    best_val  = avg_by_sf[best_sf]
    pct_diffs = [(avg_by_sf[sf] - best_val) / best_val * 100 for sf in scale_factors]

    print(f"\n[INFO] Best scale factor: {best_sf} "
          f"(avg {metric} = {best_val:.4f}, pct diff = 0.0% by definition)")

    bar_labels    = [str(sf) for sf in scale_factors]
    bar_color     = function_data['color'].iloc[0]
    display_title = function_data['display_title'].iloc[0]

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(width, heightper), constrained_layout=True)

    bars = ax.bar(bar_labels, pct_diffs,
                  color=bar_color, edgecolor='black', linewidth=0.8)
    ax.bar_label(bars, fmt='%.1f%%', padding=3, fontsize=fontsizelabel - 4)

    ax.set_title(f"{title}\n{display_title}", fontsize=fontsizetitle)
    ax.set_xlabel('Scale Factor',  fontsize=fontsizelabel)
    ax.set_ylabel(verticaltitle,   fontsize=fontsizelabel)
    ax.tick_params(axis='both', labelsize=fontsizelabel - 4)
    ax.axhline(y=0, linewidth=1, color='k')
    ax.grid(True, linestyle='--', alpha=0.4, axis='y')

    # Dynamic y-limits: all bars are ≤ 0; small positive margin so labels fit
    min_y  = min(pct_diffs)
    buffer = max(0.1 * abs(min_y), 1.0)
    ax.set_ylim(min_y - buffer, buffer * 1.5)

    _save_figure(fig, name)


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 2 — Violin: % diff by scale factor (damping values only)
# ═════════════════════════════════════════════════════════════════════════════

def slide1_damping_violin_by_scalefactor(
    name="damping_violin_by_scalefactor.png",
    metric='avg_tot_power',
    fontsizetitle=24,
    fontsizelabel=20,
    width=16,
    heightper=9,
    verticaltitle='Percent Difference from Spotter Peak Energy (%)',
    title='Damping Scale Factor Sensitivity across Spectrums',
    **kwargs
):
    """
    Presentation-ready violin plot with one violin per scale factor (numerically
    ascending). Each data point is one spectrum group's spotter energy at that
    scale factor expressed as a percent difference from that group's spotter peak.

    Groups without a spotter spectrum are skipped with a terminal warning.
    All values are ≤ 0% by construction (peak energy is the baseline).

    Parameters
    ----------
    name : str
        Output filename (saved relative to this file's directory).
    metric : str
        DataFrame column to plot on the y-axis.
    fontsizetitle : int
        Font size for the plot title.
    fontsizelabel : int
        Font size for axis labels.
    width : int
        Total figure width in inches.
    heightper : int
        Figure height in inches.
    verticaltitle : str
        Y-axis label.
    title : str
        Main figure title.
    **kwargs
        batch_name, batch_name2, ... : batch file name strings to filter mainDF.
    """
    # ── Load, filter, annotate ────────────────────────────────────────────────
    function_data = _load_and_filter(kwargs)
    function_data = _build_spectrum_metadata(function_data, spectrums.read_spectrums())

    spectrum  = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
    title_map = function_data.set_index(
        ' IncWaveSpectrumType;IncWaveSpectrumParams')['display_title'].to_dict()
    spectrum  = _sort_spectrum_keys(spectrum, title_map)
    groups    = _group_by_root_id(spectrum, function_data)

    # ── Accumulate pct-diff values per scale factor ───────────────────────────
    sf_data_by_category = defaultdict(list)   # {sf_value: [pct_diff, ...]}

    for prefix, spec_list in groups.items():
        group_data = function_data[
            function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].isin(spec_list)]
        _, avg_data_spot, spot_max_val = _resolve_spotter(group_data, prefix, metric)
        if avg_data_spot is None:
            continue

        for _, row in avg_data_spot.iterrows():
            sf       = row[' ScaleFactor']
            pct_diff = (row[metric] - spot_max_val) / spot_max_val * 100
            sf_data_by_category[sf].append(pct_diff)

    if not sf_data_by_category:
        print("[ERROR] No scale factor data accumulated. Aborting.")
        return

    # ── Build ordered violin data (ascending scale factor) ────────────────────
    ordered_sfs   = sorted(sf_data_by_category.keys())
    positions     = list(range(len(ordered_sfs)))
    violin_data   = [sf_data_by_category[sf] for sf in ordered_sfs]
    cmap          = plt.get_cmap('tab10')
    violin_colors = [cmap(i % 10) for i in range(len(ordered_sfs))]
    x_labels      = [str(sf) for sf in ordered_sfs]

    # ── Draw ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(
        figsize=(max(8, len(ordered_sfs) * 1.8), heightper),
        constrained_layout=True
    )
    _draw_violin(ax, positions, violin_data, violin_colors)

    ax.set_title(title, fontsize=fontsizetitle)
    ax.set_xticks(positions)
    ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=fontsizelabel)
    ax.set_ylabel(verticaltitle, fontsize=fontsizelabel)
    ax.tick_params(axis='y', labelsize=fontsizelabel - 4)
    ax.axhline(y=0, linewidth=1, color='k', linestyle='--', alpha=0.6)
    ax.grid(True, alpha=0.3, axis='y')

    _save_figure(fig, name)


# ═════════════════════════════════════════════════════════════════════════════
# FUNCTION 3 — Violin: best damping SF vs non-spotter spectrum types
# ═════════════════════════════════════════════════════════════════════════════

def slide8_damping_violin_best_vs_types(
    name="damping_violin_best_vs_types.png",
    metric='avg_tot_power',
    fontsizetitle=24,
    fontsizelabel=20,
    exclude_types=None,
    exclude_spectrum_ids: list[int] | None = None,   # e.g. [3, 7]
    width=16,
    heightper=9,
    verticaltitle='Percent Difference from Spotter Peak Energy (%)',
    title='Optimal Damping vs Spectrum Type',
    show_best_damping=True,
    **kwargs
):
    """
    Presentation-ready violin plot comparing the single best damping scale factor
    (optional) against all non-spotter spectrum types (BretSFP, BretHFP, etc.).

    Best damping is defined as the scale factor whose mean percent difference across
    all spectrum groups is closest to 0% — identical logic to
    slide1_damping_violin_by_scalefactor, computed internally from scratch.

    Spotter is excluded as a category (it is the percent-difference baseline and
    contributes 0% at its own peak by construction). All plotted values are ≤ 0%.

    Non-spotter categories are ordered alphabetically. Best damping, when shown,
    appears as the first (leftmost) category.

    Parameters
    ----------
    name : str
        Output filename (saved relative to this file's directory).
    metric : str
        DataFrame column to plot on the y-axis.
    fontsizetitle : int
        Font size for the plot title.
    fontsizelabel : int
        Font size for axis labels.
    width : int
        Total figure width in inches.
    heightper : int
        Figure height in inches.
    verticaltitle : str
        Y-axis label.
    title : str
        Main figure title.
    show_best_damping : bool
        If True (default), prepends a violin for the best-performing damping scale
        factor. Set to False to plot spectrum types only.
    **kwargs
        batch_name, batch_name2, ... : batch file name strings to filter mainDF.
    """
    # ── Load, filter, annotate ────────────────────────────────────────────────
    function_data = _load_and_filter(kwargs)
    function_data = _build_spectrum_metadata(function_data, spectrums.read_spectrums())

    if exclude_spectrum_ids:
        function_data = function_data[
            ~function_data['spectrum_id'].isin(exclude_spectrum_ids)
        ]

    spectrum  = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
    title_map = function_data.set_index(
        ' IncWaveSpectrumType;IncWaveSpectrumParams')['display_title'].to_dict()
    spectrum  = _sort_spectrum_keys(spectrum, title_map)
    groups    = _group_by_root_id(spectrum, function_data)

    # ── Accumulate per-group data ─────────────────────────────────────────────
    # sf_data_by_category   — mirrors Function 2; used only to select best SF
    # type_data_by_category — one pct-diff per group per non-spotter label
    sf_data_by_category   = defaultdict(list)
    type_data_by_category = defaultdict(list)
    type_category_colors  = {}

    for prefix, spec_list in groups.items():
        group_data = function_data[
            function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].isin(spec_list)]
        _, avg_data_spot, spot_max_val = _resolve_spotter(group_data, prefix, metric)
        if avg_data_spot is None:
            continue

        # ── Scale factor pct-diffs (for best-SF selection) ────────────────────
        for _, row in avg_data_spot.iterrows():
            sf       = row[' ScaleFactor']
            pct_diff = (row[metric] - spot_max_val) / spot_max_val * 100
            sf_data_by_category[sf].append(pct_diff)

        # ── Non-spotter spectrum type pct-diffs ───────────────────────────────
        spec_rows = []
        for spec in spec_list:
            spec_data = function_data[
                function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]

            possible_types_raw = spec_data['possible_spectrum_types'].iloc[0]
            if pd.notna(possible_types_raw) and '|' in str(possible_types_raw):
                possible_types = str(possible_types_raw).split('|')
            else:
                possible_types = [spec_data['spectrum_type'].iloc[0]]

            # Skip spectra that are purely spotter
            if all(t.lower() == 'spotter' for t in possible_types):
                continue

            avg_data = spec_data.groupby(' ScaleFactor')[metric].mean().reset_index()
            if avg_data.empty:
                continue

            max_energy_damp = avg_data.nlargest(1, columns=[metric])[' ScaleFactor'].iloc[0]
            max_energy_row  = avg_data_spot[
                avg_data_spot[' ScaleFactor'] == max_energy_damp].copy()

            if max_energy_row.empty:
                print(f"\n[WARNING] SF {max_energy_damp} from spectrum '{spec}' not found "
                      f"in spotter data for group '{prefix}'. Skipping.")
                continue

            sf_val         = max_energy_row[' ScaleFactor'].iloc[0]
            spotter_val_sf = max_energy_row[metric].iloc[0]
            pct_diff       = (spotter_val_sf - spot_max_val) / spot_max_val * 100
            new_vals       = spec_data.loc[
                spec_data[' ScaleFactor'] == sf_val, ['display_title', 'color']].iloc[0]

            for p_type in possible_types:
                if p_type.lower() == 'spotter':
                    continue
                if exclude_types and p_type in exclude_types:
                    continue
                p_color = (spectrums.get_color_for_spectrum_type(p_type)
                           if len(possible_types) > 1
                           else new_vals['color'])
                spec_rows.append({
                    'spectrum_type': p_type,
                    ' ScaleFactor':  sf_val,
                    metric:          spotter_val_sf,
                    'pct_diff':      pct_diff,
                    'color':         p_color,
                })

        # Deduplicate — same physical run can appear via multiple ambiguous strings
        seen_spec = set()
        deduped   = []
        for row in spec_rows:
            key = (row['spectrum_type'], row[' ScaleFactor'], round(row[metric], 8))
            if key not in seen_spec:
                seen_spec.add(key)
                deduped.append(row)
            else:
                print(f"\n[INFO] Duplicate suppressed: type '{row['spectrum_type']}' "
                      f"at SF {row[' ScaleFactor']} in group '{prefix}'.")
        spec_rows = deduped

        for row in spec_rows:
            label = _type_label(row['spectrum_type'])
            type_data_by_category[label].append(row['pct_diff'])
            type_category_colors[label] = row['color']

    # ── Find best damping scale factor (mean pct-diff closest to 0%) ──────────
    if not sf_data_by_category:
        print("[ERROR] No scale factor data accumulated. Cannot determine best SF. Aborting.")
        return

    best_sf      = min(sf_data_by_category.keys(),
                       key=lambda sf: abs(float(np.mean(sf_data_by_category[sf]))))
    best_sf_mean = float(np.mean(sf_data_by_category[best_sf]))
    n_groups     = len(sf_data_by_category[best_sf])
    print(f"\n[INFO] Best damping scale factor: SF={best_sf} "
          f"(mean % diff = {best_sf_mean:.3f}% across {n_groups} groups)")

    # ── Assemble final violin categories ──────────────────────────────────────
    # Order: [Best Damping (optional)] + [spectrum types alphabetically]
    category_order = []
    violin_data    = []
    violin_colors  = []

    if show_best_damping:
        best_label = f"Best Damping\n(SF={best_sf})"
        category_order.append(best_label)
        violin_data.append(sf_data_by_category[best_sf])
        violin_colors.append('#555555')

    if not type_data_by_category and not show_best_damping:
        print("[ERROR] No spectrum type data and show_best_damping=False. Nothing to plot. Aborting.")
        return

    for label in sorted(type_data_by_category.keys()):
        if exclude_types and label in exclude_types:
            continue
        category_order.append(label)
        violin_data.append(type_data_by_category[label])
        violin_colors.append(type_category_colors[label])

    # ── Draw ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(
        figsize=(max(8, len(category_order) * 1.8), heightper),
        constrained_layout=True
    )
    positions = list(range(len(category_order)))
    _draw_violin(ax, positions, violin_data, violin_colors)

    ax.set_title(title, fontsize=fontsizetitle)
    ax.set_xticks(positions)
    ax.set_xticklabels(category_order, rotation=45, ha='right', fontsize=fontsizelabel)
    ax.set_ylabel(verticaltitle, fontsize=fontsizelabel)
    ax.tick_params(axis='y', labelsize=fontsizelabel - 4)
    ax.axhline(y=0, linewidth=1, color='k', linestyle='--', alpha=0.6)
    ax.grid(True, alpha=0.3, axis='y')

    _save_figure(fig, name)




###############################
def main():
    # Define names that will be used throughout
    spectrum1simple = 437
    batches_slide2 = resolve_hyak_batch_names({
        'batch_spot_Bret_PFP_TPFP_30+_37730593_20260726',
        })
    batches_slide2 = {f'batch_name{i+1 if i > 0 else ""}': name for i, name in enumerate(batches_slide2)}

    # Create Graphs
    ##Slide1
    # slide1spotter(spectrum = spectrum1simple, types=('spotter'), width=5, heightper=5, title='Wave Spectrum')

    # additional_batches_slide1 = {
    #     "batch_name": "batch_results_20260213182532",
    #     "batch_name2": "batch_results_20260211181904",
    #     "batch_name3": "batch_results_20260304113810",
    #     "batch_name4": "batch_results_20260315141339",
    #     "batch_name5": "batch_results_20260327142504",
    # }
    # slide1dampingcurve(name='slide1dampingcurve', metric='avg_tot_power', spectrum_id=spectrum1simple, width=5, 
    #                         heightper=5, title='Optimal Damping', **batches_slide2)

    # ##Slide2
    # slide2seastates(highlight=False, name='slide2seastatesunhighlighted', title='', width=14, heightper=6)
    # batches_slide2 = resolve_hyak_batch_names({
    #     'batch_spot_Bret_PFP_TPFP_30+_37730593_20260726',
    #     })
    # batches_slide2 = {f'batch_name{i+1 if i > 0 else ""}': name for i, name in enumerate(batches_slide2)}
    # slide2seastates(name='slide2seastateshighlighted', title='', width=14, heightper=6, **batches_slide2)

    # ##Slide3
    # slide3spectrum = 297
    # slide1_damping_bar_single_spectrum(name = 'slide3damping_bar_single_spectrum', spectrum_id=slide3spectrum, title='', width=14, heightper=6, **batches_slide2) #297
    # slide1_damping_violin_by_scalefactor(name = 'slide3dampingviolinscalefactor', title='', width=14, heightper=8, **batches_slide2)

    # ##Slide4
    # slide4spectrum = 437
    # slide2seastates(name='slide4seastate_highlighted', highlight_id = slide4spectrum, title='', width=14, heightper=6, highlight_width=3)
    # slide1spotter(name='slide4spot', spectrum = slide4spectrum, width=15, heightper=7, types=('spotter'))
    # slide1spotter(name='slide4spotbret', spectrum = slide4spectrum, width=15, heightper=7, types=('spotter', 'bretschneider', 'BretPFP'))

    ##Slide5
    slide5spectrum = 363
    # slide1dampingcurve(name='slide5dampingcurve', metric='avg_tot_power', spectrum_id=slide5spectrum, **batches_slide2)
    slide1dampingcurve(name='slide5dampingcurvebret', metric='avg_tot_power', spectrum_id=slide5spectrum, spectrum_types=('all'), **batches_slide2)

    # ##Slide6
    # slide6spectrums = (437, 535)
    # slide6spotter(name='slide6dampingspot', spectra = slide6spectrums, types=('spotter',), width=10, heightper=5)
    # slide6spotter(name='slide6dampingspot_bretTPFP', spectra = slide6spectrums, types=('spotter', 'BretTPFP'), width=10, heightper=5)

    # #slide 7
    # slide6spectrums = (456, 846)
    # slide6spotter(name='slide7dampingspot', spectra = slide6spectrums, types=('spotter',), width=10, heightper=5)
    # slide6spotter(name='slide7dampingspot_bretPFP', spectra = slide6spectrums, types=('spotter', 'BretPFP'), width=10, heightper=5)

    # #Slide 8
    # slide8_damping_violin_best_vs_types(name = 'slide8dampingviolinscalefactor', exclude_types=['BretSFP', 'BretHFP'], exclude_spectrum_ids=[882, 1031, 1045], title='',  **batches_slide2)




    # ###########TESTING WITH SMALLER SUBSET
    # batch_names = ['batch_spotter_bret_SFP_30+_37450154_20260721']
    
    # resolved_batches = run_analytics.resolve_hyak_batch_names(batch_names)
    # print(resolved_batches)
    # batch_kwargs = {f'batch_name{i+1 if i > 0 else ""}': name for i, name in enumerate(resolved_batches)}
    # ###########TESTING WITH SMALLER SUBSET

    # #damping_seed_comparison_plot(metric='avg_tot_power', cols=4, damping_values_avg=True, col_org = True, plot_type='avg_by_spec', **batch_kwargs)
    # print(batch_kwargs)
    # damping_seed_comparison_plot(metric='avg_tot_power', cols=4, damping_values_avg=True, col_org = True, plot_type='cor_max_diff_by_spec', damping_ref='all_scales', **batch_kwargs)
    # #damping_seed_comparison_plot(metric='avg_tot_power', cols=4, damping_values_avg=True, col_org = True, plot_type='cor_max_diff_violin', damping_ref='all_scales', **batch_kwargs)

    # # #spectrum_nums=[104, 105, 192, 271]
    # # mbari_2022 = [114, 198, 260, 384, 532, 597]
    # # mbari_2022_more = [729, 1239, 52, 363, 901, 270, 712, 803, 444]
    # # mbari_2022_moremorea = [462, 494, 1255, 38]
    # # mbari_2022_moremoreb = [62, 496]
    # # spec_ids_add = mbari_2022 + mbari_2022_more + mbari_2022_moremorea + mbari_2022_moremoreb
    # # spectrum_ids   = [18, 83, 107, 297, 303, 371, 412, 429, 437, 454, 456, 484, 535, 570, 619, 737, 757, 758, 805, 819, 822, 833, 838, 846, 1031, 1045, 1115, 1143, 1174, 1181]
    # # spectrum_ids = sorted(spectrum_ids + spec_ids_add)
    # # spectrum_nums = spectrum_ids
    # # #plot_overlayed_spectrums((spectrum_nums), plots_per_page=8, period=False, types=['spotter', 'BretSFP', 'bretscneider'], n_cols=4, metric_sv='energy', cumsum=False)
    # # # # damping_seed_comparison_plot(batch_name='batch_results_20260518185853',  metric='avg_tot_power', cols=3, damping_values_avg=True, col_org = True, plot_type='avg_by_spec')
    # # # # damping_seed_comparison_plot(batch_name='batch_results_20260518185853',  metric='avg_tot_power', cols=3, damping_values_avg=True, col_org = True, plot_type='cor_max_diff_by_spec', damping_ref='all_scales')
    # # # # # #out = heatmap_RXO(batch_name='batch_results_20260114105529', batch_name2='batch_results_20260110154141', value='max_spring_range', error_removal=True, one_physics_step =0.01, val_plotted=False, damping_values=True, RXO = 1.5, csv_data = True)

    # # # # spectrum_nums = spectrums.spectrum_list()
    # # # # # #out = hack_heatmap_plot(batch_name='batch_results_20260114105529', batch_name2='batch_results_20260110154141', value='avg_tot_power', error_removal=True, one_physics_step   =0.01, val_plotted=False, damping_values=True, REO = 0.5)
    # # # # plot_overlayed_spectrums((spectrum_nums), plots_per_page=9, period=False, types=['spotter', 'bretschneider', 'BretHFP'], n_cols=3, metric_sv='energy', cumsum=False)

    # # # # damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339', batch_name5='batch_results_20260327142504', metric='avg_tot_power', cols=3, damping_values_avg=True, col_org = True, plot_type='avg_by_spec')
    # # # # damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339', batch_name5='batch_results_20260327142504', metric='avg_tot_power', cols=3, damping_values_avg=True, col_org = True, plot_type='cor_max_diff_by_spec', damping_ref='all_scales')
    plt.show()
##################DONE TESTING##################
if __name__ == '__main__':
    main() 