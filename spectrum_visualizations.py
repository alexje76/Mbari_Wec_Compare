"""
Module that handles plotting for multiple spectrum. 

get_MBARI_2022: Gets all spectrum from MBARI 2022 data IDs
get_MBARI_2023: Gets all spectrum from MBARI 2023 data IDs
get_damping_swept_data: Gets the spectrums that have been run with a swept damping ratio
get_all_data: Gets all the data
plot_hs_tp: Plots the spectra with Hs and Tp
"""
import spectrums
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
import tempfile
import plotly.graph_objects as go
from pathlib import Path

########################################Start Spectrum Gathering#################################################
def get_all_data ():
    df = spectrums.read_spectrums()
    return df
########################################End Spectrum Gathering#################################################

def get_spectrum_type_style(spectrum_type):
    """
    Returns the marker color and symbol for a spectrum type.
    """
    marker_symbols = {
        "BretHFP": "diamond",
        "bretschneider": "square",
        "regular": "circle",
        "regularHFP": "triangle-up",
    }

    return {
        "color": mcolors.to_hex(
            mcolors.to_rgba(spectrums.get_color_for_spectrum_type(spectrum_type))
        ),
        "symbol": marker_symbols.get(spectrum_type, "circle"),
    }



def plot_hs_tp(
    highlight_spectrum_types=None,
    spectrum_type_visibility=None,
    base_marker_size=9,
    mbari_2022=None,
):
    """
    Plots spectra as Significant Wave Height vs Frequency.

    Parameters
    ----------
    highlight_spectrum_types : iterable, optional
        Spectrum types to emphasize. These are plotted last so they appear on top,
        and their markers are drawn at 2x the base size.
    spectrum_type_visibility : dict, optional
        Mapping of spectrum type -> bool. If False, the trace starts hidden but
        remains available in the legend so it can be toggled on.
    base_marker_size : int or float, optional
        Marker size for non-highlighted spectrum types.
    mbari_2022 : list, optional
        List of spectrum IDs that have been run. These will have neon green outlines.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    highlight_spectrum_types = set(highlight_spectrum_types or [])
    spectrum_type_visibility = spectrum_type_visibility or {}
    mbari_2022 = set(mbari_2022 or [])

    df = get_all_data()
 
    df = df.dropna(
        subset=["peakPeriod", "significantWaveHeight", "spectrum_type", "spectrum_id"]
    ).copy()

    # Frequency = 1 / period. Remove invalid periods to avoid divide-by-zero.
    df = df[df["peakPeriod"] > 0].copy()
    df["frequency_hz"] = 1.0 / df["peakPeriod"]

    fig = go.Figure()

    spectrum_types = sorted(df["spectrum_type"].unique())
    normal_types = [s for s in spectrum_types if s not in highlight_spectrum_types]
    highlighted_types = [s for s in spectrum_types if s in highlight_spectrum_types]

    # Plot non-highlighted traces first.
    for spectrum_type in normal_types + highlighted_types:
        subset = df[df["spectrum_type"] == spectrum_type]
        is_highlighted = spectrum_type in highlight_spectrum_types
        style = get_spectrum_type_style(spectrum_type)

        # Split into run and not-run spectrums
        subset_not_run = subset[~subset["spectrum_id"].isin(mbari_2022)]
        subset_run = subset[subset["spectrum_id"].isin(mbari_2022)]

        # Plot not-run spectrums (black outline)
        if len(subset_not_run) > 0:
            fig.add_trace(
                go.Scatter(
                    x=subset_not_run["frequency_hz"],
                    y=subset_not_run["significantWaveHeight"],
                    mode="markers",
                    name=str(spectrum_type),
                    visible=(
                        True
                        if spectrum_type_visibility.get(spectrum_type, True)
                        else "legendonly"
                    ),
                    marker=dict(
                        color=style["color"],
                        symbol=style["symbol"],
                        size=base_marker_size * 2 if is_highlighted else base_marker_size,
                        opacity=0.9 if is_highlighted else 0.8,
                        line=dict(width=0.75 if is_highlighted else 0.5, color="black"),
                    ),
                    customdata=subset_not_run[["spectrum_id", "peakPeriod"]],
                    hovertemplate=(
                        "spectrum_id: %{customdata[0]}<br>"
                        f"spectrum_type: {spectrum_type}<br>"
                        "frequency: %{x:.4f} Hz<br>"
                        "peakPeriod: %{customdata[1]:.4f} s<br>"
                        "significantWaveHeight: %{y}<extra></extra>"
                    ),
                    showlegend=True,
                )
            )

        # Plot run spectrums (neon green outline)
        if len(subset_run) > 0:
            fig.add_trace(
                go.Scatter(
                    x=subset_run["frequency_hz"],
                    y=subset_run["significantWaveHeight"],
                    mode="markers",
                    name=str(spectrum_type),
                    visible=(
                        True
                        if spectrum_type_visibility.get(spectrum_type, True)
                        else "legendonly"
                    ),
                    marker=dict(
                        color=style["color"],
                        symbol=style["symbol"],
                        size=base_marker_size * 2 if is_highlighted else base_marker_size,
                        opacity=0.9 if is_highlighted else 0.8,
                        line=dict(width=0.75 if is_highlighted else 0.5, color="#39FF14"),
                    ),
                    customdata=subset_run[["spectrum_id", "peakPeriod"]],
                    hovertemplate=(
                        "spectrum_id: %{customdata[0]}<br>"
                        f"spectrum_type: {spectrum_type}<br>"
                        "frequency: %{x:.4f} Hz<br>"
                        "peakPeriod: %{customdata[1]:.4f} s<br>"
                        "significantWaveHeight: %{y}<extra></extra>"
                    ),
                    showlegend=(len(subset_not_run) == 0),
                )
            )

    fig.update_layout(
        title="Significant Wave Height vs Frequency",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Significant Wave Height",
        legend_title="Spectrum Type",
        template="plotly_white",
    )

    return fig



def show_plot_in_window(fig, title="Hs vs Frequency"):
    """
    Opens the Plotly figure in its own desktop window using pywebview.

    Install first if needed:
        pip install pywebview

    Falls back to fig.show() if pywebview is not installed.
    """
    try:
        import webview
    except ImportError:
        print("pywebview is not installed; falling back to fig.show().")
        fig.show()
        return

    html = fig.to_html(full_html=True, include_plotlyjs="cdn")
    html_path = Path(tempfile.gettempdir()) / "hs_vs_frequency_plot.html"
    html_path.write_text(html, encoding="utf-8")

    webview.create_window(title, html_path.as_uri(), width=1200, height=800)
    webview.start()



def main():
    mbari_2022 = [114, 198, 260, 384, 532, 597]
    mbari_2022_more = [729, 1239, 52, 363, 901, 270, 712, 803, 444]
    mbari_2022_moremorea = [462, 494, 1255, 38]
    mbari_2022_moremoreb = [62, 496]
    spec_ids_add = mbari_2022 + mbari_2022_more + mbari_2022_moremorea + mbari_2022_moremoreb
    spectrum_ids   = [18, 83, 107, 297, 303, 371, 412, 429, 437, 454, 456, 484, 535, 570, 619, 737, 757, 758, 805, 819, 822, 833, 838, 846, 1031, 1045, 1115, 1143, 1174, 1181]
    spectrum_ids = sorted(spectrum_ids + spec_ids_add)
    
    # Replace these with whichever spectrum types you want to emphasize.
    highlight_types = {
        "BretHFP",
        "bretschneider",
        "regular",
        "regularHFP",
    }

    # Set any spectrum type to False to start it hidden.
    spectrum_type_visibility = {
        "BretHFP": True,
        "bretschneider": True,
        "regular": True,
        "regularHFP": True,
    }

    fig = plot_hs_tp(
        highlight_spectrum_types=highlight_types,
        spectrum_type_visibility=spectrum_type_visibility,
        mbari_2022=spectrum_ids,
    )

    # Opens in a standalone window if pywebview is installed.
    show_plot_in_window(fig)



if __name__ == '__main__':
    main()
