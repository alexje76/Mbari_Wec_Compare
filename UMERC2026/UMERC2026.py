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

import matplotlib.pyplot as plt
import numpy as np
import re

def slide1spotter(spectrum=1000):
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
    types = ('spotter', 'BretSFP')
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
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 5 * n_rows), sharey=True)
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
            ax.set_title(f"Spectrum {i}", fontsize=24)
            ax.set_xlabel(xlabel, fontsize=20)
            if idx % 2 == 0:
                ax.set_ylabel('Spectral Density (m^2/Hz)', fontsize=20)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(fontsize=20)
            ax.tick_params(axis='both', labelsize=16)

        for j in range(len(batch), len(axes)):
            fig.delaxes(axes[j])

        plt.tight_layout()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(current_dir, "slide1spotter.png")
        plt.savefig(save_path, dpi=600, bbox_inches='tight', transparent=False)
        # plt.show()

def slide1dampingcurve():
    pass
       
###############################
def main():
    # Define names that will be used throughout
    spectrum1simple = 1239

    # Create Graphs

    slide1spotter(spectrum = spectrum1simple)


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