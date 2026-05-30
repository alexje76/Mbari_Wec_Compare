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
import plotly.graph_objects as go

########################################Start Spectrum Gathering#################################################
def get_all_data ():
    df = spectrums.read_spectrums()
    return df
########################################End Spectrum Gathering#################################################

def plot_hs_tp():
    """
    Plots the spectra as a function of Hs and Tp

    ----------------
    Parameters:
        Year: Which years are gathered if not all

    ----------------
    Returns:
    """
    df = get_all_data()
    print(f"df{df}")

    df = df.dropna(subset=["peakPeriod", "significantWaveHeight", "spectrum_type", "spectrum_id"])

    fig = go.Figure()

    for spectrum_type in sorted(df["spectrum_type"].unique()):
        subset = df[df["spectrum_type"] == spectrum_type]

        fig.add_trace(
            go.Scatter(
                x=subset["peakPeriod"],
                y=subset["significantWaveHeight"],
                mode="markers",
                name=str(spectrum_type),
                marker=dict(
                    color=mcolors.to_hex(mcolors.to_rgba(spectrums.get_color_for_spectrum_type(spectrum_type))), #get_color returns tab:red but need hex
                    size=9,
                    opacity=0.8,
                    line=dict(width=0.5, color="black"),
                ),
                customdata=subset[["spectrum_id"]],
                hovertemplate=(
                    "spectrum_id: %{customdata[0]}<br>"
                    "spectrum_type: " + str(spectrum_type) + "<br>"
                    "peakPeriod: %{x}<br>"
                    "significantWaveHeight: %{y}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="Significant Wave Height vs Peak Period",
        xaxis_title="Peak Period",
        yaxis_title="Significant Wave Height",
        legend_title="Spectrum Type",
        template="plotly_white",
    )

    return fig

def main():
    fig = plot_hs_tp()
    fig.show()

if __name__ == '__main__':
    main()