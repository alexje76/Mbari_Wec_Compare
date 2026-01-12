"""
This module contains functions for visualizing MBARI WEC data in a variety of ways
Functions:
- plot_data(**kwargs): Plot data from mainDF based on specified parameters.
- plot_data_runs(**kwargs): Plot data for a specific run as a time series.
- transient_investigation_plot(transient, pblog_name): Plot transient investigation results.
- hack_heatmap_plot(**kwargs): Plot a "heatmap" for wave spectrum data - currently hardcoded for avg power of regular waves (12/10/25).
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib as mpl
import pandas as pd
import os
import glob

import mainDF_management as mDF_mgmt 
import run_analytics
import wave_operations

def plot_data(**kwargs):
    """
    Plot the data using the specified parameters.
    """
    #Access the data
    mainDF = mDF_mgmt.access_mainDF()    

    #Use function pass to get data indices
    if 'batch_name' in kwargs and not 'run_number' in kwargs:
        #get mainDF indices from batch name
        plot_data = mainDF[mainDF['batch_file_name'] == kwargs['batch_name']]
        plot_data_name = kwargs['batch_name']
    elif 'batch_name' in kwargs and 'run_number' in kwargs:
        #get mainDF index from batch name and run number
        #TODO:implement
        pass
    elif 'mainDF_index' in kwargs:
        #get pblog name from mainDF index
        #TODO: implement
        pass
    elif 'pblog_name' in kwargs:
        #get pblog name directly
        pblog_name = kwargs['pblog_name']
    elif 'dataframecsv' in kwargs:
        df = pd.read_csv(kwargs['dataframecsv'])
        #TODO
    else:
        raise ValueError("Must provide information relating to data to plot: such as batch_name or mainDF_index")

    x = plot_data[kwargs['x']]
    y = plot_data[kwargs['y']]

    if 'remove_end_runs' in kwargs:
        removal = kwargs['remove_end_runs']
        x = x.iloc[:-removal]
        y = y.iloc[:-removal]
        print(x)
        print(y)

    #print(x)
    
    #Plot the data
    plt.figure(figsize=(10, 6))
    plt.title(f"Data Plot for {plot_data_name}: {kwargs['y']} vs {kwargs['x']}")

    plt.scatter(x, y)
    #plt.xscale('log') #for physics step #TODO add toggle argument, for y as well
    plt.xlabel(kwargs['x'])
    plt.ylabel(kwargs['y'])
    plt.grid()
    plt.show()

def plot_data_runs(**kwargs):
    """
    Plot data for a run as a timeseries
    """
    #Access the data
    mainDF = mDF_mgmt.access_mainDF()    

    #Use function pass to get data indices
    run_data = run_analytics.get_data(**kwargs) #TODO: add in trim functionality
    plot_data_name = kwargs['batch_name'] if 'batch_name' in kwargs else kwargs['pblog_name'] #TODO: improve

    run_data_y = run_data[[kwargs['x'], kwargs['y']]]
    run_data_clean_y = run_data_y.dropna()
    y_name = kwargs['y']

    plt.figure(figsize=(15, 9))
    plt.scatter(run_data_clean_y[kwargs['x']], run_data_clean_y[kwargs['y']], label=kwargs['y'], s =2)

    if 'y2' in kwargs:
        run_data_y2 = run_data[[kwargs['x'], kwargs['y2']]]
        run_data_clean_y2 = run_data_y2.dropna()
        y_name += f" and {kwargs['y2']}"
        print(run_data_clean_y2) # debugging
        plt.scatter(run_data_clean_y2[kwargs['x']], run_data_clean_y2[kwargs['y2']], label=kwargs['y2'], s=.2)

    if 'y3' in kwargs:
        run_data_y3 = run_data[[kwargs['x'], kwargs['y3']]]
        run_data_clean_y3 = run_data_y3.dropna()
        y_name += f", {kwargs['y3']}"
        plt.scatter(run_data_clean_y3[kwargs['x']], run_data_clean_y3[kwargs['y3']], label=kwargs['y3'], s=.2)

    if 'y4' in kwargs:
        run_data_y4 = run_data[[kwargs['x'], kwargs['y4']]]
        run_data_clean_y4 = run_data_y4.dropna()
        y_name += f", {kwargs['y4']}"
        plt.scatter(run_data_clean_y4[kwargs['x']], run_data_clean_y4[kwargs['y4']], label=kwargs['y4'], s=.2)

    #plt.xscale('log') #for physics step
    plt.xlabel(kwargs['x'])
    plt.ylabel('')

    plt.title(f"Data Plot for {plot_data_name}: {y_name} vs {kwargs['x']}")
    plt.legend(markerscale = 7)
    #plt.grid()
    #plt.gca().yaxis.set_major_locator(MaxNLocator(nbins=9))

    plt.show()

def transient_investigation_plot(transient, pblog_name):
    x = transient['i']
    y = transient['avg_power']

    x = x[1:]
    y = y[1:]

        
        #Plot the data
    plt.figure(figsize=(10, 6))
    plt.title(f"Data Plot for Transient test {pblog_name}: power vs trim")

    plt.scatter(x, y)
    # plt.xscale('log') #for physics step
    plt.xlabel('trim(periods)')
    plt.ylabel('power')
    plt.grid()
    plt.show()

def hack_heatmap_plot(**kwargs):
    """
    Plot a heatmap using the specified parameters. #TODO make sure it will not try to hand other spectrum types
    """
    #Access the data
    mainDF = mDF_mgmt.access_mainDF()    

    #Use function pass to get data indices
    if 'batch_name' in kwargs and not 'run_number' in kwargs:
        #get mainDF indices from batch name
        heatmap_data = mainDF[mainDF['batch_file_name'] == kwargs['batch_name']].copy()
        heatmap_data_name = kwargs['batch_name']

    heatmap_data[['A', 'T']] = heatmap_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.extract(r'A:([0-9.]+);T:([0-9.]+)') #capture A,T all after that have a 0-9 or .
    g = 9.81
    row = 1020
    wec_diameter = 2.64 #meters
    heatmap_data[['A', 'T']] = heatmap_data[['A', 'T']].astype(float)

    heatmap_data['flux'] = (((g**2)*row/8)*wec_diameter*(heatmap_data['A']**2) * (heatmap_data['T']))  # Flux, munltiplied by wec area to just get watts  TODO: implememnt the non simplified version
    heatmap_data['avg_pwr_eff'] = heatmap_data[kwargs['value']] / heatmap_data['flux']
    print(heatmap_data[['A', 'T', 'flux', kwargs['value'], 'avg_pwr_eff']])

    cmap = mpl.colormaps['PiYG'] # Choose a colormap
    norm = mpl.colors.CenteredNorm(vcenter=0) #center the colormap at 0
    norm.autoscale(heatmap_data['avg_pwr_eff']) #autoscale based on data, matching color map endpoints to data

    heatmap_data['edgecolor'] = heatmap_data['avg_pwr_eff'].apply(lambda v: 'purple' if v <= 0 else 'green')  # Example condition for edge color
    #print(heatmap_data['avg_pwr_eff'].max())
    #print(heatmap_data['avg_pwr_eff'].min())
    sc = plt.scatter(heatmap_data['T'], heatmap_data['A'], c=heatmap_data['avg_pwr_eff'], cmap = cmap, norm = norm, edgecolors=heatmap_data['edgecolor'], linewidths=0.5, s=200)

    cmap2 = mpl.colormaps['bwr'] # Choose a colormap for power
    norm2 = mpl.colors.TwoSlopeNorm(vmin = heatmap_data[kwargs['value']].min(), vmax=heatmap_data[kwargs['value']].max(), vcenter=0) #center the colormap at 0
    #norm2.autoscale(heatmap_data[kwargs['value']]) #autoscale based on data, matching color map endpoints to data
    sc2 = plt.scatter(heatmap_data['T']+0.1, heatmap_data['A'], c=heatmap_data[kwargs['value']], cmap = cmap2, norm = norm2, edgecolors='black', linewidths=0.5, s=100, marker='d')

    cbar = plt.colorbar(sc)
    cbar.set_label("Power efficiency of incident wave")  # label for the color scale

    cbar2 = plt.colorbar(sc2)
    cbar2.set_label(f"{kwargs['value']} (W)")  # label for the color scale

    plt.title(f"Heatmap for {heatmap_data_name}: Avg power efficiency vs Wave Period and Amplitude")
    plt.xlabel('Period (s)')
    plt.ylabel('Amplitude (m)')
    plt.grid()
    plt.show()

def error_code_analysis_plot(**kwargs):
    """
    Plot error code vs the specified parameters. to view the correlations #TODO
    """
    plt.figure()
    #Access the data
    mainDF = mDF_mgmt.access_mainDF()    

    #Use function pass to get data indices
    if 'batch_name' in kwargs and not 'run_number' in kwargs:
        #get mainDF indices from batch name
        heatmap_data = mainDF[mainDF['batch_file_name'] == kwargs['batch_name']].copy()
        heatmap_data_name = kwargs['batch_name']
    
    if 'batch_name2' in kwargs and not 'run_number' in kwargs:
        #get mainDF indices from batch name
        heatmap_data_batch2 = mainDF[mainDF['batch_file_name'] == kwargs['batch_name2']].copy()
        heatmap_data_name2 = kwargs['batch_name2']
        heatmap_data = pd.concat([heatmap_data, heatmap_data_batch2], ignore_index=True)

    if 'batch_name3' in kwargs and not 'run_number' in kwargs:
        #get mainDF indices from batch name
        heatmap_data_batch3 = mainDF[mainDF['batch_file_name'] == kwargs['batch_name3']].copy()
        heatmap_data_name3 = kwargs['batch_name3']
        heatmap_data = pd.concat([heatmap_data, heatmap_data_batch3], ignore_index=True)

    if 'batch_name4' in kwargs and not 'run_number' in kwargs:
        #get mainDF indices from batch name
        heatmap_data_batch4 = mainDF[mainDF['batch_file_name'] == kwargs['batch_name4']].copy()
        heatmap_data_name4 = kwargs['batch_name4']
        heatmap_data = pd.concat([heatmap_data, heatmap_data_batch4], ignore_index=True)

    heatmap_data['RegularWaves'] = heatmap_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.contains('MonoChromatic')
    heatmap_data.loc[heatmap_data['RegularWaves'], ['A', 'T']] = heatmap_data.loc[heatmap_data['RegularWaves'], ' IncWaveSpectrumType;IncWaveSpectrumParams'].str.extract(r'A:([0-9.]+);T:([0-9.]+)').values #capture A,T all after that have a 0-9 or .
    heatmap_data[['A', 'T']] = heatmap_data[['A', 'T']].astype(float)
    print(heatmap_data.head())

    heatmap_data['simcode color'] = heatmap_data[' SimReturnCode'].apply(lambda v: 'red' if v == 134 else 'green' if v == 0 else 'blue')
    heatmap_data['marker'] = heatmap_data[' PhysicsStep'].apply(lambda v: 'o' if v == 0.007 else 's' if v == 0.01 else '^' if v == 0.015 else 'D')
   # print(heatmap_data['marker'])
    phystep1 = heatmap_data[heatmap_data[' PhysicsStep'] == 0.007]
    phystep2 = heatmap_data[heatmap_data[' PhysicsStep'] == 0.01]
    phystep3 = heatmap_data[heatmap_data[' PhysicsStep'] == 0.015]
    phystep4 = heatmap_data[heatmap_data[' PhysicsStep'] != 0.007]
    sc1 = plt.scatter(phystep1['T']-0.1, phystep1['A'], c=phystep1['simcode color'], edgecolors=phystep1['simcode color'], linewidths=0.5, s=100, marker='o', label='Physics Step 0.007s')
    sc2 = plt.scatter(phystep2['T'], phystep2['A'], c=phystep2['simcode color'], edgecolors=phystep2['simcode color'], linewidths=0.5, s=100, marker='s', label='Physics Step 0.01s')
    sc3 = plt.scatter(phystep3['T']+0.1, phystep3['A'], c=phystep3['simcode color'], edgecolors=phystep3['simcode color'], linewidths=0.5, s=100, marker='^', label='Physics Step 0.015s')
    sc4 = plt.scatter(phystep4['T']+0.2, phystep4['A'], c=phystep4['simcode color'], edgecolors=phystep4['simcode color'], linewidths=0.5, s=100, marker='d', label='Physics Step 0.02')
    #sc2 = plt.scatter(heatmap_data['T'], heatmap_data['A'], c=heatmap_data['simcode color'], edgecolors=heatmap_data['simcode color'], linewidths=0.5, s=100, marker='D')

    plt.title(f"Simcode map for {heatmap_data_name} and {heatmap_data_name2 if 'batch_name2' in kwargs else ''} and {heatmap_data_name3 if 'batch_name3' in kwargs else ''}: Simcode 0=green, 134=red, else=blue")
    plt.xlabel('Period (s)')
    plt.ylabel('Amplitude (m)')
    plt.grid()

    #Creating Breaking line
    T = {'T': np.linspace(heatmap_data['T'].min(), heatmap_data['T'].max(), 1000)}
    d = 80 #depth - hardcoded for MBARI WEC

    bounding_breaking = pd.DataFrame(T)
    bounding_breaking['wavenum'] = wave_operations.wavenum(bounding_breaking['T'], depth=d)
    bounding_breaking['length'] = 2*np.pi/bounding_breaking['wavenum']
    bounding_breaking['d/L'] = d / bounding_breaking['length']         # Helper for condition calculation

    # Define conditions
    conditions = [
        (bounding_breaking['d/L'] >= 0.5), # Deep water
        (bounding_breaking['d/L'] <= 0.05)  # Shallow water
    ]

    # Define corresponding choices (amplitudes)
    choices = [
        0.142 * bounding_breaking['length'] / 2,
        0.78 * d / 2
    ]

    # Apply conditions; use the "else" (transitional) logic as the default
    bounding_breaking['amp_b'] = np.select(
        conditions, 
        choices, 
        default=0.142 * bounding_breaking['length'] * np.tanh(bounding_breaking['wavenum']*d) / 2
    )

    # Now plot
    print(bounding_breaking.to_string())
    plt.plot(bounding_breaking['T'], bounding_breaking['amp_b'], color='blue', label='Breaking Wave Limit')

    #Pre-transitional relic
    T = np.linspace(heatmap_data['T'].min(), heatmap_data['T'].max() if heatmap_data['T'].max() < 11 else 8, 1000)
    Ab = (T**2 *0.22)/2 #Height (H = .142*g/(pi*2)) divided by 2 to get amplitude
    plt.plot(T, Ab, color='black', linestyle='--', label='Breaking Wave Limit Approximation - deep water')
    #Pre-transitional relic

    #plt.plot (T, A*4, color='orange', linestyle='--', label='Breaking Wave Limit Approximation (Ho multiplied by 2)')
    #plt.plot(T, A*2, color='blue', linestyle='--', label='Breaking Wave Limit Approximation (Ho not divided by 2)')
    plt.legend()

##################TESTING##################
def main():
    #plot_data(batch_name='batch_results_20251102162754_1', x=' PhysicsStep', y='max_spring_range', remove_end_runs=2)
    #plot_data_runs(pblog_name='results_run_2_20251121161212\\pblog', x=' Timestamp (epoch seconds)', y=' XB X Rate', y2=' XB Y Rate', y3=' XB Z Rate')
    #plot_data_runs(pblog_name='results_run_2_20251121161212\\pblog', x=' Timestamp (epoch seconds)', y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')
    #plot_data_runs(pblog_name='results_run_4_20251121162305', x=' Timestamp (epoch seconds)', y=' XB North Vel', y2=' XB East Vel', y3=' XB Down Vel')
    #plot_data_runs(pblog_name='results_run_9_20251208125330\\pblog', x=' Timestamp (epoch seconds)', y=' SC Range Finder (in)')
    #plot_data_runs(pblog_name='results_run_0_20251104192421\\pblog', x=' Timestamp (epoch seconds)', y=' XB North Vel', y2=' XB East Vel', y3=' XB X Rate', y4=' XB Z Rate')
    #plot_data_runs(pblog_name='results_run_1_20251208101612\\pblog', x=' Timestamp (epoch seconds)', y=' PC Battery Curr (A)', y2=' PC Load Dump Current (A)')
   # plot_data_runs(pblog_name='results_run_1_20251208101612\\pblog', x=' Timestamp (epoch seconds)', y=' PC RPM')

    #hack_heatmap_plot(b atch_name='batch_results_20251208124051', value='avg_tot_power')
    #hack_heatmap_plot(batch_name='batch_results_20251208191310', value='avg_tot_power')
    error_code_analysis_plot(batch_name='batch_results_20251217001004', batch_name2='batch_results_20251208124051', batch_name3='batch_results_20251208191310', batch_name4='batch_results_20251218153359')

    plt.show()
##################DONE TESTING##################

if __name__ == '__main__':
    main()