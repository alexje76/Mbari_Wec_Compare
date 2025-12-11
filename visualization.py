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
        print (heatmap_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].head())
        heatmap_data_name = kwargs['batch_name']

    heatmap_data[['A', 'T']] = heatmap_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.extract(r'A:([0-9.]+);T:([0-9.]+)') #capture A,T all after that have a 0-9 or .
    heatmap_data[['A', 'T']] = heatmap_data[['A', 'T']].astype(float)

    heatmap_data['intensity'] = (heatmap_data['A']**2) * (heatmap_data['T'])  # Simplified intensity calculation  TODO: implememnt the non simplified version
    heatmap_data['avg_pwr_eff'] = heatmap_data[kwargs['value']] / heatmap_data['intensity']

    cmap = mpl.colormaps['PiYG'] # Choose a colormap
    print(heatmap_data.head())
    norm = mpl.colors.CenteredNorm(vcenter=0) #vmin=heatmap_data['avg_pwr_eff'].min(), vmax=heatmap_data['avg_pwr_eff'].max(), 
    #heatmap_data['color'] = heatmap_data['avg_pwr_eff'].map(lambda v: cmap(norm(v))) #Used for average power efficiency
    heatmap_data['color'] = heatmap_data[kwargs['value']].map(lambda v: cmap(norm(v))) #Used for simple power average

    #sc = plt.scatter(heatmap_data['T'], heatmap_data['A'], c=heatmap_data['color'], norm = norm, edgecolors='black', linewidths=0.5, s=100)
    heatmap_data['edgecolor'] = heatmap_data['avg_pwr_eff'].apply(lambda v: 'purple' if v < 0 else 'green')  # Example condition for edge color
    sc = plt.scatter(heatmap_data['T'], heatmap_data['A'], c=heatmap_data['avg_pwr_eff'], cmap = cmap, norm = norm, edgecolors=heatmap_data['edgecolor'], linewidths=0.5, s=100)

    cbar = plt.colorbar(sc)
    cbar.set_label("Power efficiency of incident wave")  # label for the color scale

    plt.title(f"Heatmap for {heatmap_data_name}: Avg power efficiency vs Wave Period and Amplitude")
    plt.xlabel('Period (s)')
    plt.ylabel('Amplitude (m)')
    plt.grid()
    plt.show()
##################TESTING##################
def main():
    #plot_data(batch_name='batch_results_20251102162754_1', x=' PhysicsStep', y='max_spring_range', remove_end_runs=2)
    #plot_data_runs(pblog_name='results_run_2_20251121161212\\pblog', x=' Timestamp (epoch seconds)', y=' XB X Rate', y2=' XB Y Rate', y3=' XB Z Rate')
    #plot_data_runs(pblog_name='results_run_2_20251121161212\\pblog', x=' Timestamp (epoch seconds)', y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')
    #plot_data_runs(pblog_name='results_run_4_20251121162305', x=' Timestamp (epoch seconds)', y=' XB North Vel', y2=' XB East Vel', y3=' XB Down Vel')
    plot_data_runs(pblog_name='results_run_9_20251208125330\\pblog', x=' Timestamp (epoch seconds)', y=' SC Range Finder (in)')
    #plot_data_runs(pblog_name='results_run_0_20251104192421\\pblog', x=' Timestamp (epoch seconds)', y=' XB North Vel', y2=' XB East Vel', y3=' XB X Rate', y4=' XB Z Rate')
    plot_data_runs(pblog_name='results_run_1_20251208101612\\pblog', x=' Timestamp (epoch seconds)', y=' PC Battery Curr (A)', y2=' PC Load Dump Current (A)')
   # plot_data_runs(pblog_name='results_run_1_20251208101612\\pblog', x=' Timestamp (epoch seconds)', y=' PC RPM')
    hack_heatmap_plot(batch_name='batch_results_20251208191310', value='avg_tot_power')
##################DONE TESTING##################

if __name__ == '__main__':
    main()