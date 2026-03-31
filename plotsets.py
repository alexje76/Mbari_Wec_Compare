"""
    This module is used to keep a log of what is used for what plots.
    Each function should be labeled with a date and purpose and well documented.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import pandas as pd

import mainDF_management as mDF_mgmt 
import run_analytics
import wave_operations
import spectrums
import visualization

def damping_opt_3_31():
    """
    This function is used to plot damping optimization plots. 
    -The spectrums plotted on a single plot, without any RAO
    -The plots that include the damping sweep by 0.1 for reg, regHFP, bret, bretHFP, and spotter.
    """
    spectrum_nums = spectrums.spectrum_list()
    visualization.plot_overlayed_spectrums((spectrum_nums), plots_per_page=6, period=False, types=['spotter', 'bretschneider', 'BretHFP', 'regular', 'regularHFP'], n_cols=3, metric_sv='energy', cumsum=False)
    visualization.damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339', batch_name5='batch_results_20260327142504', metric='avg_tot_power', cols=6, damping_values_avg=True, col_org = True, plot_type='avg_by_spec')
    plt.tight_layout()
    plt.show()
def combination_pre_03_31_26():
    #plot_data(batch_name='batch_results_20251102162754_1', x=' PhysicsStep', y='max_spring_range', remove_end_runs=2)
    #plot_data_runs(pblog_name='results_run_2_20251121161212\\pblog', x=' Timestamp (epoch seconds)', y=' XB X Rate', y2=' XB Y Rate', y3=' XB Z Rate')
    ##plot_data_runs(pblog_name='results_run_2_20251121161212\\pblog', x=' Timestamp (epoch seconds)', y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')
    ###plot_data_runs(pblog_name='results_run_0_20251104192421\\pblog', x=' Timestamp (epoch seconds)', y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #use for transient solution, originally plotted wrong
    
    #plot_data_runs(pblog_name='results_run_4_20251121162305', x=' Timestamp (epoch seconds)', y=' XB North Vel', y2=' XB East Vel', y3=' XB Down Vel')
    #plot_data_runs(pblog_name='results_run_9_20251208125330\\pblog', x=' Timestamp (epoch seconds)', y=' SC Range Finder (in)')
    #plot_data_runs(pblog_name='results_run_0_20251104192421\\pblog', x=' Timestamp (epoch seconds)', y=' XB North Vel', y2=' XB East Vel', y3=' XB X Rate', y4=' XB Z Rate')
    #plot_data_runs(pblog_name='results_run_1_20251208101612\\pblog', x=' Timestamp (epoch seconds)', y=' PC Battery Curr (A)', y2=' PC Load Dump Current (A)')
    # plot_data_runs(pblog_name='results_run_15_20260114113725/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')#b #Trying to chase down the 134 error by comparing a bunch of yaws
    # plot_data_runs(pblog_name='results_run_19_20260114114647/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #Trying to chase down the 134 error by comparing a bunch of yaws
    # plot_data_runs(pblog_name='results_run_25_20260114120200/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')#b #Trying to chase down the 134 error by comparing a bunch of yaws
    # plot_data_runs(pblog_name='results_run_26_20260114120259/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')#b #Trying to chase down the 134 error by comparing a bunch of yaws
    # plot_data_runs(pblog_name='results_run_31_20260114121314/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')#b #Trying to chase down the 134 error by comparing a bunch of yaws
    # plot_data_runs(pblog_name='results_run_49_20260114124445/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')#b #Trying to chase down the 134 error by comparing a bunch of yaws
    # plot_data_runs(pblog_name='results_run_51_20260114124542/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #Trying to chase down the 134 error by comparing a bunch of yaws
    # plot_data_runs(pblog_name='results_run_55_20260114125154/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #Trying to chase down the 134 error by comparing a bunch of yaws
    # plot_data_runs(pblog_name='results_run_56_20260114125255/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #Trying to chase down the 134 error by comparing a bunch of yaws

    # plot_data_runs(pblog_name='results_run_0_20260123185817/pblog', x=' Timestamp (epoch seconds)',  y=' PC Load Dump Current (A)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #Gui Run 0
    # plot_data_runs(pblog_name='results_run_1_20260123190035/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #Gui Run 1

    # plot_data_runs(pblog_name='results_run_0_20260123185204/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #No GUI Run 0
    # plot_data_runs(pblog_name='results_run_1_20260123185414/pblog', x=' Timestamp (epoch seconds)',  y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)') #No GUI Run 1


    #hack_heatmap_plot(batch_name='batch_results_20251208124051', value='avg_tot_power')
    #hack_heatmap_plot(batch_name='batch_results_20260110154141', value='avg_tot_power', error_removal=True, one_physics_step=0.01)
    #error_code_analysis_plot(batch_name='batch_results_20251217001004', batch_name2='batch_results_20251208124051', batch_name3='batch_results_20260110154141', batch_name4='batch_results_20251218153359') #batch_results_20251208191310
    #error_code_analysis_plot(batch_name='batch_results_20260110154141', breaking_line=False, physics_step_compare=True) 
    ##error_code_analysis_plot(batch_name='batch_results_20260114105529', batch_name2='batch_results_20260110154141', breaking_line=True, damping_altered=True, physics_step_only=0.01) #batch_results_20260114105529 is for the two different physics steps
    #hack_heatmap_plot(batch_name='batch_results_20260114105529', batch_name2='batch_results_20260110154141', value='avg_tot_power', error_removal=True, one_physics_step   =0.01, val_plotted=False, damping_values=True, REO = 0.5)
    
    #damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', metric='avg_tot_power', cols=2, damping_values_avg=True)
    #damping_seed_comparison_plot(batch_name='batch_results_20260220105054', metric='avg_tot_power', cols=2, damping_values_avg=True)
    ##damping_seed_comparison_plot(batch_name='batch_results_20260304113810', batch_name3='batch_results_20260213182532', batch_name2='batch_results_20260211181904', metric='avg_tot_power', cols=2, damping_values_avg=True)
    #damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', metric='avg_tot_power', cols=1, damping_values_avg=True)
    #plot_data_runs(pblog_name='results_run_1_20260220111851/pblog', x=' Timestamp (epoch seconds)',  y=' SC Range Finder (in)') #For repeat period
    spectrum_nums = spectrums.spectrum_list()
    #plot_overlayed_spectrums(spectrum_nums, plots_per_page=6, period=True, types=['spotter', 'bretschneider'], n_cols=2, metric_sv='energy', cumsum=True)
    #plot_overlayed_spectrums((spectrum_nums), plots_per_page=6, period=False, types=['spotter', 'bretschneider', 'BretHFP'], n_cols=3, metric_sv='energy', cumsum=False)

    #out = hack_heatmap_plot(batch_name='batch_results_20260114105529', batch_name2='batch_results_20260110154141', value='avg_tot_power', error_removal=True, one_physics_step   =0.01, val_plotted=False, damping_values=True, REO = 0.5)
    #plot_overlayed_spectrums((spectrum_nums), plots_per_page=6, period=False, types=['spotter', 'bretschneider', 'BretHFP', 'regular'], n_cols=3, metric_sv='energy', cumsum=False, reo_df = out)
    visualization.plot_overlayed_spectrums((spectrum_nums), plots_per_page=6, period=False, types=['spotter', 'bretschneider', 'BretHFP', 'regular', 'regularHFP'], n_cols=3, metric_sv='energy', cumsum=False)

    #Morteza Pres
    #plot_overlayed_spectrums(np.array([532, 114]), plots_per_page=6, period=False, types=['spotter', 'bretschneider'], n_cols=2, metric_sv='energy', cumsum=False)
    #damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339', metric='avg_tot_power', cols=6, damping_values_avg=True, seed_coloration=True, col_org = True)
    #damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339', metric='avg_tot_power', cols=6, damping_values_avg=True, col_org = True, plot_type='avg_on_one')
    visualization.damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339', batch_name5='batch_results_20260327142504', metric='avg_tot_power', cols=6, damping_values_avg=True, col_org = True, plot_type='avg_by_spec')
    plt.tight_layout()
    plt.show()

##################TESTING##################
def main():
    damping_opt_3_31()
##################DONE TESTING##################
if __name__ == '__main__':
    main()