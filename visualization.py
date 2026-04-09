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
import textwrap
import math
import scipy.integrate as integrate

import mainDF_management as mDF_mgmt 
import run_analytics
import wave_operations
import spectrums

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
    
    #Plot the data
    plt.figure(figsize=(10, 6))
    plt.title(f"Data Plot for {plot_data_name}: {kwargs['y']} vs {kwargs['x']}")

    plt.scatter(x, y)
    #plt.xscale('log') #for physics step #TODO add toggle argument, for y as well
    plt.xlabel(kwargs['x'])
    plt.ylabel(kwargs['y'])
    plt.grid()
    plt.show()

def plot_data_runs_old(**kwargs):
    """
    Plot data for a run as a timeseries
    """
    #Access the data
    mainDF = mDF_mgmt.access_mainDF()    

    #Use function pass to get data indices
    run_data = run_analytics.get_data(**kwargs) #TODO: add in trim functionality
    plot_data_name = kwargs['batch_name'] if 'batch_name' in kwargs else kwargs['pblog_name'] #TODO: improve

    run_data_y = run_data[[kwargs['x'], kwargs['y']]]
    run_data_clean_y = y_data_to_float(run_data_y.dropna())
    y_name = kwargs['y']

    plt.figure(figsize=(15, 9))
    plt.scatter(run_data_clean_y[kwargs['x']], run_data_clean_y[kwargs['y']], label=kwargs['y'], s =2)

    if 'y2' in kwargs:
        run_data_y2 = run_data[[kwargs['x'], kwargs['y2']]]
        run_data_clean_y2 = y_data_to_float(run_data_y2.dropna())
        y_name += f" and {kwargs['y2']}"
        #print(run_data_clean_y2) # debugging
        plt.scatter(run_data_clean_y2[kwargs['x']], run_data_clean_y2[kwargs['y2']], label=kwargs['y2'], s=.2)

    if 'y3' in kwargs:
        run_data_y3 = run_data[[kwargs['x'], kwargs['y3']]]
        run_data_clean_y3 = y_data_to_float(run_data_y3.dropna())
        y_name += f", {kwargs['y3']}"
        plt.scatter(run_data_clean_y3[kwargs['x']], run_data_clean_y3[kwargs['y3']], label=kwargs['y3'], s=.2)

    if 'y4' in kwargs:
        run_data_y4 = run_data[[kwargs['x'], kwargs['y4']]]
        run_data_clean_y4 = y_data_to_float(run_data_y4.dropna())
        y_name += f", {kwargs['y4']}"
        plt.scatter(run_data_clean_y4[kwargs['x']], run_data_clean_y4[kwargs['y4']], label=kwargs['y4'], s=.2)

    #plt.xscale('log') #for physics step
    plt.xlabel(kwargs['x'])
    plt.ylabel('')

    plt.title(f"Data Plot for {plot_data_name}: {y_name} vs {kwargs['x']}")
    plt.legend(markerscale = 7)
    #plt.grid()
    #plt.gca().yaxis.set_major_locator(MaxNLocator(nbins=9))

    #plt.show()
def plot_data_runs(**kwargs):
    """
    Plot data for a run as a timeseries
    """
    # Access the data
    mainDF = mDF_mgmt.access_mainDF()    

    # Use function pass to get data indices
    run_data = run_analytics.get_data(**kwargs) #TODO: add in trim functionality
    plot_data_name = kwargs.get('batch_name', kwargs.get('pblog_name')) #TODO: improve

    plt.figure(figsize=(15, 9))
    
    # Define the keys to check in order
    y_keys = ['y', 'y2', 'y3', 'y4']
    active_y_names = []

    for i, key in enumerate(y_keys):
        if key in kwargs:
            y_col = kwargs[key]
            active_y_names.append(y_col)
            
            # Process and clean data
            subset = run_data[[kwargs['x'], y_col]].dropna()
            clean_data = y_data_to_float(subset)
            
            point_size = .5
            
            # Plot the specific series
            plt.scatter(clean_data[kwargs['x']], clean_data[y_col], label=y_col, s=point_size)

    # Dynamically build the title/label string
    if len(active_y_names) > 1:
        y_name = ", ".join(active_y_names[:-1]) + f" and {active_y_names[-1]}"
    else:
        y_name = active_y_names[0] if active_y_names else ""

    #plt.xscale('log') #for physics step
    plt.xlabel(kwargs['x'])
    plt.ylabel('')

    title = f"Data Plot for {plot_data_name}: {y_name} vs {kwargs['x']}"
    plt.title(wrap_title(title))
    plt.legend(markerscale = 7)
    #plt.grid()
    #plt.gca().yaxis.set_major_locator(MaxNLocator(nbins=9))

    #plt.show()

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
    Plot a heatmap using the specified parameters. #TODO make sure it will not try to handle other spectrum types beyond monochromatic
    """
    #Access the data
    mainDF = mDF_mgmt.access_mainDF()    

    if 'batch_name' in kwargs and 'run_number' not in kwargs:
        # Define keys to check in order (batch_name, batch_name2, batch_name3, etc.)
        batch_keys = [k for k in kwargs if k.startswith('batch_name')]
    
        # List to collect individual DataFrames before final concatenation
        frames_to_concat = []

        for key in batch_keys:
            if key in kwargs:
                # Filter and copy the relevant data
                temp_df = mainDF[mainDF['batch_file_name'] == kwargs[key]].copy()
                frames_to_concat.append(temp_df)
            
                # Dynamically set variables like heatmap_data_name, heatmap_data_name2, etc.
                # Note: Using a dictionary is often cleaner than dynamic variable names
                suffix = key.replace('batch_name', '')
                globals()[f'heatmap_data_name{suffix}'] = kwargs[key]

        # Efficiently combine all collected data at once
        if frames_to_concat:
            function_data = pd.concat(frames_to_concat, ignore_index=True)
        heatmap_data = function_data.copy() #TODO: Might be better to change all future calls of heatmap data to function instead of this.

    if 'one_physics_step' in kwargs and kwargs['one_physics_step'] is not None:
        heatmap_data = heatmap_data[heatmap_data[' PhysicsStep'] == kwargs['one_physics_step']]

    heatmap_data[['A', 'T']] = heatmap_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.extract(r'A:([0-9.]+);T:([0-9.]+)') #capture A,T all after that have a 0-9 or .
    heatmap_data[['A', 'T']] = heatmap_data[['A', 'T']].astype(float)
    g = 9.81
    row = 1020
    wec_diameter = 2.64 #meters

    heatmap_data['flux'] = (((g**2)*row/8)*wec_diameter*(heatmap_data['A']**2) * (heatmap_data['T']))  # Flux, munltiplied by wec area to just get watts  TODO: implememnt the non simplified version
    heatmap_data['avg_pwr_eff'] = heatmap_data[kwargs['value']] / heatmap_data['flux']
    #print(heatmap_data[['A', 'T', 'flux', kwargs['value'], 'avg_pwr_eff']]) 

    if 'error_removal' in kwargs and kwargs['error_removal'] == True:
        heatmap_data = heatmap_data[heatmap_data[' SimReturnCode'] == 0] #remove error

    cmap = mpl.colormaps['PiYG'] # Choose a colormap
    norm = mpl.colors.CenteredNorm(vcenter=0) #center the colormap at 0
    norm.autoscale(heatmap_data['avg_pwr_eff']) #autoscale based on data, matching color map endpoints to data

    heatmap_data['edgecolor'] = heatmap_data['avg_pwr_eff'].apply(lambda v: 'purple' if v <= 0 else 'green')  # Example condition for edge color
    #print(heatmap_data['avg_pwr_eff'].max())
    #print(heatmap_data['avg_pwr_eff'].min())

    if 'damping_values' in kwargs and kwargs['damping_values'] is True:
        damping = heatmap_data[' ScaleFactor'].unique()
        print(damping)
        markers = ['o', 'd', '^', 's', 'D', 'v', 'P', '*']  # Extend this list if you have more damping values
        sc = {} 
        damp_spread = {}
        for i, damp in enumerate(damping):
            damp_data = heatmap_data[heatmap_data[' ScaleFactor'] == damp]
            #print(damp_data)
            print(f'Damping Scale {damp}: max avg power eff {damp_data["avg_pwr_eff"].max()}, min avg power eff {damp_data["avg_pwr_eff"].min()}')
            damp_spread[damp] = damp_data['avg_pwr_eff'].max() - damp_data['avg_pwr_eff'].min()
            sc[f'sc{i}'] = plt.scatter(damp_data['T'] + (i*0.1)-0.1, damp_data['A'], c=damp_data['avg_pwr_eff'], cmap = cmap, norm = norm, edgecolors=damp_data['edgecolor'], linewidths=0.5, s=50, label=f'Damping Scale {damp}', marker=markers[i], alpha=0.7)
        max_spread_damp = max(damp_spread, key=damp_spread.get)
        cbar = plt.colorbar(sc[f'sc{int(max_spread_damp)}']) #TODO: make sure this works with multiple scatters
        cbar.set_label("Power efficiency of incident wave")  # label for the color scale
    else:
        sc = plt.scatter(heatmap_data['T'], heatmap_data['A'], c=heatmap_data['avg_pwr_eff'], cmap = cmap, norm = norm, edgecolors=heatmap_data['edgecolor'], linewidths=0.5, s=200)
        cbar = plt.colorbar(sc) #TODO: make sure this works with multiple scatters
        cbar.set_label("Power efficiency of incident wave")  # label for the color scale

    if 'val_plotted' in kwargs and kwargs['val_plotted'] is True:
        cmap2 = mpl.colormaps['gist_rainbow'] # Choose a colormap for power #TODO:Cmasher -cool is another good option
    #print(heatmap_data[kwargs['value']].max())
    #print(heatmap_data[kwargs['value']].min())
        #norm2 = mpl.colors.LogNorm(vmin = 1, vmax=heatmap_data[kwargs['value']].max()) #log colormap with negative values clipped
        #norm2 = mpl.colors.Normalize(vmin=1, vmax=heatmap_data[kwargs['value']].max()) #Non-log colormap with negative values clipped
        norm2 = mpl.colors.Normalize(vmin=1, vmax=heatmap_data[kwargs['value']].max()/3) #Non-log colormap with negative values clipped -divided by 2 for more color resolution
    #norm2 = mpl.colors.TwoSlopeNorm(vmin = heatmap_data[kwargs['value']].min(), vmax=heatmap_data[kwargs['value']].max(), vcenter=0) #center the colormap at 0
    #norm2.autoscale(heatmap_data[kwargs['value']]) #autoscale based on data, matching color map endpoints to data
        sc2 = plt.scatter(heatmap_data['T'], heatmap_data['A']+0.05, c=heatmap_data[kwargs['value']], cmap = cmap2, norm = norm2, edgecolors='black', linewidths=0.5, s=75, marker='p')

        cbar2 = plt.colorbar(sc2)
        cbar2.set_label(f"{kwargs['value']}")  # label for the color scale


    plt.title(f"Heatmap for {heatmap_data_name} and {heatmap_data_name2 if 'batch_name2' in kwargs else ''}: Avg power efficiency vs Wave Period and Amplitude")
    plt.xlabel('Period (s)')
    plt.ylabel('Amplitude (m)')
    plt.grid()

    if 'REO' in kwargs and kwargs['REO'] is not None: #Code to output the REO, for damping 1, using the amplitude as the number given
        # Filter for damping factor 1.0
        d_one = heatmap_data[heatmap_data[' ScaleFactor'] == 1.0]
        
        # If a specific amplitude (float/int) was passed, filter by it
        target_amp = kwargs['REO']
        if isinstance(target_amp, (int, float)):
            d_one = d_one[d_one['A'] == target_amp]
            print(f"\n--- Efficiency for Amplitude {target_amp} (Damping = 1) ---")
        else:
            print("\n--- Efficiency for All Amplitudes (Damping = 1) ---")

        # Sort by Period (T) and display
        output = d_one[['T', 'avg_pwr_eff']].sort_values(['T'])
        output['T'] = 1 / output['T']
        output.rename(columns={'T': 'F'}, inplace=True)
        print(output.to_string(index=False))
        return output #TODO: have this better suited for the optional return
def heatmap_RXO(**kwargs):
    """
    Plot a heatmap and/or return an RXO table for regular wave runs, using the specified parameters. #TODO make sure it will not try to handle other spectrum types beyond monochromatic
    
    -------
    Parameters:

    ------
    Returns:

    """
    #Access the data
    mainDF = mDF_mgmt.access_mainDF()    

    if 'batch_name' in kwargs and 'run_number' not in kwargs:
        # Define keys to check in order (batch_name, batch_name2, batch_name3, etc.)
        batch_keys = [k for k in kwargs if k.startswith('batch_name')]
    
        # List to collect individual DataFrames before final concatenation
        frames_to_concat = []

        for key in batch_keys:
            if key in kwargs:
                # Filter and copy the relevant data
                temp_df = mainDF[mainDF['batch_file_name'] == kwargs[key]].copy()
                frames_to_concat.append(temp_df)
            
                # Dynamically set variables like heatmap_data_name, heatmap_data_name2, etc.
                # Note: Using a dictionary is often cleaner than dynamic variable names
                suffix = key.replace('batch_name', '')
                globals()[f'heatmap_data_name{suffix}'] = kwargs[key]

        # Efficiently combine all collected data at once
        if frames_to_concat:
            function_data = pd.concat(frames_to_concat, ignore_index=True)
        heatmap_data = function_data.copy() #TODO: Might be better to change all future calls of heatmap data to function instead of this.

    if 'one_physics_step' in kwargs and kwargs['one_physics_step'] is not None:
        heatmap_data = heatmap_data[heatmap_data[' PhysicsStep'] == kwargs['one_physics_step']]

    heatmap_data[['A', 'T']] = heatmap_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.extract(r'A:([0-9.]+);T:([0-9.]+)') #capture A,T all after that have a 0-9 or .
    heatmap_data[['A', 'T']] = heatmap_data[['A', 'T']].astype(float)
    g = 9.81
    row = 1020
    wec_diameter = 2.64 #meters

    heatmap_data['flux'] = (((g**2)*row/8)*wec_diameter*(heatmap_data['A']**2) * (heatmap_data['T']))  # Flux, munltiplied by wec area to just get watts  TODO: implememnt the non simplified version
    heatmap_data['avg_pwr_eff'] = heatmap_data[kwargs['value']] / heatmap_data['flux']
    #print(heatmap_data[['A', 'T', 'flux', kwargs['value'], 'avg_pwr_eff']]) 

    if 'error_removal' in kwargs and kwargs['error_removal'] == True:
        heatmap_data = heatmap_data[heatmap_data[' SimReturnCode'] == 0] #remove error

    cmap = mpl.colormaps['PiYG'] # Choose a colormap
    norm = mpl.colors.CenteredNorm(vcenter=0) #center the colormap at 0
    norm.autoscale(heatmap_data['avg_pwr_eff']) #autoscale based on data, matching color map endpoints to data

    heatmap_data['edgecolor'] = heatmap_data['avg_pwr_eff'].apply(lambda v: 'purple' if v <= 0 else 'green')  # Example condition for edge color
    #print(heatmap_data['avg_pwr_eff'].max())
    #print(heatmap_data['avg_pwr_eff'].min())

    if 'damping_values' in kwargs and kwargs['damping_values'] is True:
        damping = heatmap_data[' ScaleFactor'].unique()
        print(damping)
        markers = ['o', 'd', '^', 's', 'D', 'v', 'P', '*']  # Extend this list if you have more damping values
        sc = {} 
        damp_spread = {}
        for i, damp in enumerate(damping):
            damp_data = heatmap_data[heatmap_data[' ScaleFactor'] == damp]
            #print(damp_data)
            print(f'Damping Scale {damp}: max avg power eff {damp_data["avg_pwr_eff"].max()}, min avg power eff {damp_data["avg_pwr_eff"].min()}')
            damp_spread[damp] = damp_data['avg_pwr_eff'].max() - damp_data['avg_pwr_eff'].min()
            sc[f'sc{i}'] = plt.scatter(damp_data['T'] + (i*0.1)-0.1, damp_data['A'], c=damp_data['avg_pwr_eff'], cmap = cmap, norm = norm, edgecolors=damp_data['edgecolor'], linewidths=0.5, s=50, label=f'Damping Scale {damp}', marker=markers[i], alpha=0.7)
        max_spread_damp = max(damp_spread, key=damp_spread.get)
        cbar = plt.colorbar(sc[f'sc{int(max_spread_damp)}']) #TODO: make sure this works with multiple scatters
        cbar.set_label("Power efficiency of incident wave")  # label for the color scale
    else:
        sc = plt.scatter(heatmap_data['T'], heatmap_data['A'], c=heatmap_data['avg_pwr_eff'], cmap = cmap, norm = norm, edgecolors=heatmap_data['edgecolor'], linewidths=0.5, s=200)
        cbar = plt.colorbar(sc) #TODO: make sure this works with multiple scatters
        cbar.set_label("Power efficiency of incident wave")  # label for the color scale

    if 'val_plotted' in kwargs and kwargs['val_plotted'] is True:
        cmap2 = mpl.colormaps['gist_rainbow'] # Choose a colormap for power #TODO:Cmasher -cool is another good option
    #print(heatmap_data[kwargs['value']].max())
    #print(heatmap_data[kwargs['value']].min())
        #norm2 = mpl.colors.LogNorm(vmin = 1, vmax=heatmap_data[kwargs['value']].max()) #log colormap with negative values clipped
        #norm2 = mpl.colors.Normalize(vmin=1, vmax=heatmap_data[kwargs['value']].max()) #Non-log colormap with negative values clipped
        norm2 = mpl.colors.Normalize(vmin=1, vmax=heatmap_data[kwargs['value']].max()/3) #Non-log colormap with negative values clipped -divided by 2 for more color resolution
    #norm2 = mpl.colors.TwoSlopeNorm(vmin = heatmap_data[kwargs['value']].min(), vmax=heatmap_data[kwargs['value']].max(), vcenter=0) #center the colormap at 0
    #norm2.autoscale(heatmap_data[kwargs['value']]) #autoscale based on data, matching color map endpoints to data
        sc2 = plt.scatter(heatmap_data['T'], heatmap_data['A']+0.05, c=heatmap_data[kwargs['value']], cmap = cmap2, norm = norm2, edgecolors='black', linewidths=0.5, s=75, marker='p')

        cbar2 = plt.colorbar(sc2)
        cbar2.set_label(f"{kwargs['value']}")  # label for the color scale


    plt.title(f"Heatmap for {heatmap_data_name} and {heatmap_data_name2 if 'batch_name2' in kwargs else ''}: Avg power efficiency vs Wave Period and Amplitude")
    plt.xlabel('Period (s)')
    plt.ylabel('Amplitude (m)')
    plt.grid()

    if 'REO' in kwargs and kwargs['REO'] is not None: #Code to output the REO, for damping 1, using the amplitude as the number given
        # Filter for damping factor 1.0
        d_one = heatmap_data[heatmap_data[' ScaleFactor'] == 1.0]
        
        # If a specific amplitude (float/int) was passed, filter by it
        target_amp = kwargs['REO']
        if isinstance(target_amp, (int, float)):
            d_one = d_one[d_one['A'] == target_amp]
            print(f"\n--- Efficiency for Amplitude {target_amp} (Damping = 1) ---")
        else:
            print("\n--- Efficiency for All Amplitudes (Damping = 1) ---")

        # Sort by Period (T) and display
        output = d_one[['T', 'avg_pwr_eff']].sort_values(['T'])
        output['T'] = 1 / output['T']
        output.rename(columns={'T': 'F'}, inplace=True)
        print(output.to_string(index=False))
        return output #TODO: have this better suited for the optional return
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

    #Extract A and T from wave spectrum params
    heatmap_data['RegularWaves'] = heatmap_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.contains('MonoChromatic')
    heatmap_data.loc[heatmap_data['RegularWaves'], ['A', 'T']] = heatmap_data.loc[heatmap_data['RegularWaves'], ' IncWaveSpectrumType;IncWaveSpectrumParams'].str.extract(r'A:([0-9.]+);T:([0-9.]+)').values #capture A,T all after that have a 0-9 or .
    heatmap_data[['A', 'T']] = heatmap_data[['A', 'T']].astype(float)

    heatmap_data['simcode color'] = heatmap_data[' SimReturnCode'].apply(lambda v: 'red' if v == 134 else 'green' if v == 0 else 'blue')

    if 'physics_step_compare' in kwargs and kwargs['physics_step_compare'] is True:
        #heatmap_data['marker'] = heatmap_data[' PhysicsStep'].apply(lambda v: 'o' if v == 0.007 else 'd' if v == 0.01 else '^' if v == 0.015 else 'D')#TODO: believe this is no longer working
        print('in physics step compare')

        phystep1 = heatmap_data[heatmap_data[' PhysicsStep'] == 0.007]
        phystep2 = heatmap_data[heatmap_data[' PhysicsStep'] == 0.01]
        phystep3 = heatmap_data[heatmap_data[' PhysicsStep'] == 0.015]
        phystep4 = heatmap_data[heatmap_data[' PhysicsStep'] == 0.02]
        sc1 = plt.scatter(phystep1['T']-0.1, phystep1['A'], c=phystep1['simcode color'], edgecolors=phystep1['simcode color'], linewidths=0.5, s=100, marker='o', label='Physics Step 0.007s')
        sc2 = plt.scatter(phystep2['T'], phystep2['A'], c=phystep2['simcode color'], edgecolors=phystep2['simcode color'], linewidths=0.5, s=100, marker='d', label='Physics Step 0.01s')
        sc3 = plt.scatter(phystep3['T']+0.1, phystep3['A'], c=phystep3['simcode color'], edgecolors=phystep3['simcode color'], linewidths=0.5, s=100, marker='^', label='Physics Step 0.015s')
        sc4 = plt.scatter(phystep4['T']+0.2, phystep4['A'], c=phystep4['simcode color'], edgecolors=phystep4['simcode color'], linewidths=0.5, s=100, marker='D', label='Physics Step 0.02')
        #sc2 = plt.scatter(heatmap_data['T'], heatmap_data['A'], c=heatmap_data['simcode color'], edgecolors=heatmap_data['simcode color'], linewidths=0.5, s=100, marker='D')

    if 'damping_altered' in kwargs and kwargs['damping_altered'] == True:
        if 'physics_step_only' in kwargs:
            heatmap_data = heatmap_data[heatmap_data[' PhysicsStep'] == kwargs['physics_step_only']] #the only physics step used in this batch should be filtered
        else:
            raise ValueError("When using damping_altered=True, must provide physics_step_only=value to filter by physics step")
         
        heatmap_data['marker'] = heatmap_data[' ScaleFactor'].apply(lambda v: 'o' if v == 0.75 else 's' if v == 1.25 else '^' if v == 0.015 else 'd')

        damp1 = heatmap_data[heatmap_data[' ScaleFactor'] == 0.75]
        damp2 = heatmap_data[heatmap_data[' ScaleFactor'] == 1.0]
        damp3 = heatmap_data[heatmap_data[' ScaleFactor'] == 1.25]
        sc1 = plt.scatter(damp1['T']-0.05, damp1['A'], c=damp1['simcode color'], edgecolors=damp1['simcode color'], linewidths=0.5, s=100, marker='o', label='Damping Scale 0.75')
        sc2 = plt.scatter(damp2['T'], damp2['A'], c=damp2['simcode color'], edgecolors=damp2['simcode color'], linewidths=0.5, s=100, marker='s', label='Damping Scale 1.0')
        sc3 = plt.scatter(damp3['T']+0.05, damp3['A'], c=damp3['simcode color'], edgecolors=damp3['simcode color'], linewidths=0.5, s=100, marker='^', label='Damping Scale 1.25')

    plt.title(f"Simcode map for {heatmap_data_name} and {heatmap_data_name2 if 'batch_name2' in kwargs else ''} and {heatmap_data_name3 if 'batch_name3' in kwargs else ''}: Simcode 0=green, 134=red, else=blue")
    plt.xlabel('Period (s)')
    plt.ylabel('Amplitude (m)')
    plt.grid()

    if 'breaking_line' in kwargs and kwargs['breaking_line'] == True:
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
        #print(bounding_breaking.to_string())
        plt.plot(bounding_breaking['T'], bounding_breaking['amp_b'], color='blue', label='Breaking Wave Limit')

        #Pre-transitional relic
        T = np.linspace(heatmap_data['T'].min(), heatmap_data['T'].max() if heatmap_data['T'].max() < 11 else 8, 1000)
        Ab = (T**2 *0.22)/2 #Height (H = .142*g/(pi*2)) divided by 2 to get amplitude
        plt.plot(T, Ab, color='black', linestyle='--', label='Breaking Wave Limit Approximation - deep water')
        #Pre-transitional relic

        #plt.plot (T, A*4, color='orange', linestyle='--', label='Breaking Wave Limit Approximation (Ho multiplied by 2)')
        #plt.plot(T, A*2, color='blue', linestyle='--', label='Breaking Wave Limit Approximation (Ho not divided by 2)')
    plt.legend()
def plot_overlayed_spectrums(spectrum_nums, plots_per_page=6, types=None, n_cols=2, cumsum=False, **kwargs):
    """
    Plots multiple spectrums on the same axes for comparison, with dynamic styling based on the type of spectrum and other parameters.

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
            #TODO: change/add in the 
    ------
    Returns:
        None (displays the plots)
    """
    period = kwargs.get('period', False)
    reo_df = kwargs.get('reo_df')
    total_plots = len(spectrum_nums)
    
    # Define available models and their plotting styles
    models = {
        "spotter": {"label": "Spotter", "color": spectrums.get_color_for_spectrum_type("spotter"), "fmt": "scatter", "alpha": 0.7, "marker": "o"},
        "bretschneider": {"label": "Bretschneider", "color": spectrums.get_color_for_spectrum_type("bretschneider"), "fmt": "plot"},
        "BretHFP": {"label": "BretHFP", "color": spectrums.get_color_for_spectrum_type("BretHFP"), "fmt": "plot"},
        "jonswap": {"label": "Jonswap", "color": spectrums.get_color_for_spectrum_type("jonswap"), "fmt": "plot", "marker": "x"},
        "regular": {"label": "Regular", "color": spectrums.get_color_for_spectrum_type("regular"), "fmt": "vline", "alpha": 0.65},
        "regularHFP": {"label": "RegularHFP", "color": spectrums.get_color_for_spectrum_type("regularHFP"), "fmt": "vline", "alpha": 0.65}
    }
    
    # If types is None or 'all', use all keys in the models dict
    selected_types = list(models.keys()) if (types is None or types == 'all') else types

    for start_idx in range(0, total_plots, plots_per_page):
        batch = spectrum_nums[start_idx : start_idx + plots_per_page]
        n_rows = (len(batch) + 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows), sharey=True)
        axes = axes.flatten()

        for idx, i in enumerate(batch):
            ax = axes[idx]
            xlabel = 'Period (s)' if period else 'Frequency (Hz)'


            if reo_df is not None:
                # Assuming 'f' is frequency and the other column is amplitude
                amp_col = [c for c in reo_df.columns if c != 'F'][0]
                x_reo = 1/reo_df['F'] if period else reo_df['F']
                ax.plot(x_reo, reo_df[amp_col]*5, label="RAO", color="black", linestyle="-", linewidth=1.0)

            # Dynamic plotting based on selection
            for model_name in selected_types:
                if model_name not in models: continue
                  
                style = models[model_name]
                f, szz = spectrums.spectrum(i, model_name)
                metric_sv = spectrums.spectrum_metric_single_value(i, model_name, kwargs.get('metric_sv')) if kwargs.get('metric_sv') else None
                x = 1/np.array(f) if period else np.array(f)
                szz = np.array(szz)*(np.array(f)**2) if period else np.array(szz)
                ## TODO: I do not think this is currently working
                # if cumsum:
                #     # Calculate cumulative trapezoidal integral (Energy)
                #     # Use np.cumsum(szz_sorted * np.diff(f_sorted)) or simple cumsum:
                #     y_cumsum = integrate.cumulative_trapezoid(szz, x, initial=0 ) / integrate.trapezoid(szz, x) # Normalized 
                #     # Or use actual energy: 
                #     # y_cumsum = np.cumsum(szz_sorted) * (f_sorted[1]-f_sorted[0])
                    
                #     # Create secondary axis for cumulative plot
                #     ax2 = ax.twinx()
                #     ax2.plot(x, y_cumsum, color=style["color"], linestyle='--', alpha=0.5)
                #     ax2.set_ylabel('Cumulative Energy (%)') if idx % n_cols == (n_cols - 1) else None
                # ##
                label = style["label"]
                if metric_sv is not None:
                    label += f" ({kwargs.get('metric_sv')}: {metric_sv:.4f})" # Format to 2 decimal places

                if style.get("fmt") == "scatter":
                    ax.plot(x, szz, label=label, color=style["color"], alpha=style.get("alpha", 1), marker=style.get("marker"), ms = 1.5)
                elif style.get("fmt") == "vline":
                    ax.axvline(x, color=style["color"], alpha=style.get("alpha", 1), label=label)
                else:
                    ax.plot(x, szz, label=label, color=style["color"], marker=style.get("marker"))

            # --- Styling ---
            ax.set_title(f"Spectrum {i}")
            ax.set_xlabel(xlabel)
            if idx % 2 == 0: 
                ax.set_ylabel('Spectral Density (m^2/Hz)')
            ax.grid(True)
            ax.legend()

        for j in range(len(batch), len(axes)):
            fig.delaxes(axes[j])

        plt.tight_layout()
        #plt.show()
def damping_seed_comparison_plot(col_org = False, plot_type = 'spectrumindividual', **kwargs):
    """
    Plot a comparison of damping seed values and power metrics, to investigate the impact of damping seed on simulation outcomes.
    Designed to plot a variety of different seeds for each of a set of different wave spectra
    
    :param kwargs: Description
    'kwargs'
    'run_number'
    metric: the metric to plot on the y axis
    cols: the number of columns to use in the subplot grid (default 2)
    plot_type: the type of plot to create - listed below
        -spectrumindividual: plots the spectrum for each run, with the damping seed value included in the title, to investigate how the damping seed may be impacting the spectrum itself
        -avg_on_one: For all root spectrum and derived spectrums plot on the same axes - can manually change to semilogy
        -avg_by_spec
        -cor_max_diff_by_spec: #For each root spectrum, plot the difference in energy between the derived "max damping" and the root max energy
            -damping_ref: Also plots a reference damping value - if all_scales, plots all damping scales, if not, just plots the reference damping scale specified by the user

    """
    #Access the data
    mainDF = mDF_mgmt.access_mainDF()    
    metric = kwargs.get('metric') #default to avg power if not specified

    if 'batch_name' in kwargs and 'run_number' not in kwargs:
        # Define keys to check in order (batch_name, batch_name2, batch_name3, etc.)
        batch_keys = [k for k in kwargs if k.startswith('batch_name')]
    
        # List to collect individual DataFrames before final concatenation
        frames_to_concat = []

        for key in batch_keys:
            if key in kwargs:
                # Filter and copy the relevant data
                temp_df = mainDF[mainDF['batch_file_name'] == kwargs[key]].copy()
                frames_to_concat.append(temp_df)
            
                # Dynamically set variables like heatmap_data_name, heatmap_data_name2, etc.
                # Note: Using a dictionary is often cleaner than dynamic variable names
                suffix = key.replace('batch_name', '')
                globals()[f'heatmap_data_name{suffix}'] = kwargs[key]

        # Efficiently combine all collected data at once
        if frames_to_concat:
            function_data = pd.concat(frames_to_concat, ignore_index=True)

    spectrum = function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].unique()
    full_names_spectrums_here = spectrums.read_spectrums()

    for i, spec in enumerate(spectrum): #Adding the titles for the plots
        spec_data = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]

        #Adding the code to create the titles for the plots
        # Clean the target string of the simulator wave input
        target_str = str(spec_data[' IncWaveSpectrumType;IncWaveSpectrumParams'].iloc[0]).strip()
        f_val1, *szz_vals1 = [round(float(x), 4) for part in target_str.split(';') if ':' in part for x in part.split(':')[1:(2 if part.startswith('f') else 4)]]

        # Extract and round the comparison values for the whole reference DataFrame
        # We split the string column, extract the values, and expand them into new temporary columns
        ref_parts = full_names_spectrums_here[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.strip().str.split(';')
        #print(f"ref parts{ref_parts}")

        def extract_rounded(row_parts):
            # Extracts 1 'f' and 3 'Szz' values, returning a flat list
            vals = [round(float(x), 4) for part in row_parts if ':' in part 
                    for x in part.split(':')[1:(2 if part.startswith('f') else 4)]]
            return vals

        # Apply extraction to the whole column
        extracted_data = ref_parts.apply(extract_rounded)
        #print(f"extracted data{extracted_data}")

        # Filter the DataFrame
        #Compare the entire extracted list to our target list [f, szz1, szz2, szz3]
        matches = full_names_spectrums_here[extracted_data.apply(lambda x: x == [f_val1] + szz_vals1)]

        #Safely extract the first (and presumably only) match
        if not matches.empty:
            matching_row = matches.iloc[0]

            match matching_row['spectrum_type']:
                case "bretschneider":
                    display_title = f"{matching_row['spectrum_id']}, {matching_row['spectrum_type'][:4]}, Hs = {matching_row['significantWaveHeight'].astype(str)[:4]}, Tp = {matching_row['peakPeriod'].astype(str)[:4]}"
                case "BretHFP":
                    display_title = f"{matching_row['spectrum_id']}, {matching_row['spectrum_type'][:7]}, Hs = {matching_row['significantWaveHeight'].astype(str)[:4]}, Tp = {matching_row['peakPeriod'].astype(str)[:4]}"
                case "spotter":
                    display_title = f"{matching_row['spectrum_id']}, {matching_row['spectrum_type']}"
                case "regular":
                    display_title = f"{matching_row['spectrum_id']}, Mono, Hs = {matching_row['significantWaveHeight'].astype(str)[:4]}, T = {matching_row['peakPeriod'].astype(str)[:4]}"
                case "regularHFP":
                    display_title = f"{matching_row['spectrum_id']}, MonoHFP, Hs = {matching_row['significantWaveHeight'].astype(str)[:4]}, T = {matching_row['peakPeriod'].astype(str)[:4]}"
                case _:
                    display_title = f"{matching_row['spectrum_id']}, Wildcard Spectrum"
            spectrum_type = matching_row['spectrum_type']
        else:
            # This block runs if the string search found nothing
            print(f"ERROR: No row found for {target_str}")
            display_title = target_str
            print(f'disp tit {display_title}')
            # Optional: print the first few reference strings to see why they don't match
            #print("Sample References:", full_names_spectrums_here[' IncWaveSpectrumType;IncWaveSpectrumParams'].head().tolist())
        #print(f"print disp title{display_title}")
        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'display_title'] = str(display_title)
        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'spectrum_id'] = matching_row['spectrum_id']
        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'spectrum_type'] = spectrum_type
        #End of the code section for adding the titles
        function_data.loc[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec, 'color'] = spectrums.get_color_for_spectrum_type(matching_row['spectrum_type'])

    # Create a mapping of the unique spectrum values to their display titles
    title_map = function_data.set_index(' IncWaveSpectrumType;IncWaveSpectrumParams')['display_title'].to_dict()
    # Re-order the spectrum list based on the values in the title_map
    spectrum = sorted(spectrum, key=lambda x: title_map[x])

    if plot_type == 'spectrumindividual':
        # Begin Subplotting
        n_specs = len(spectrum)
        cols = kwargs.get('cols', 2) #default to 2 columns if not specified
        rows = math.ceil(n_specs / cols)

        # Create Figure with axes and grid of subplots
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4), constrained_layout=True)
        axes_flat = axes.flatten() # Flatten to 1D for easy iteration
        if col_org:
            axes_flat = axes.flatten('F')

        markers = ['o', 'd', '^', 's', 'D', 'v', 'P', '*']
        sc = {}
        
        for i, spec in enumerate(spectrum):
            ax = axes_flat[i]
            spec_data = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]

            # Perform the scatter on the specific subplot axis
            scatter_kwargs = {
                'marker': markers[i % len(markers)],
                'label': spec
            }
            
            if not ('seed_coloration' in kwargs and kwargs['seed_coloration'] is False):
                scatter_kwargs['c'] = spec_data[' Seed']
                scatter_kwargs['cmap'] = 'tab20'
            
            sc[i] = ax.scatter(
                spec_data[' ScaleFactor'], 
                spec_data[metric], 
                **scatter_kwargs
            )
            
            if 'damping_values_avg' in kwargs and kwargs['damping_values_avg'] is True:
                #Find and then plot the average for each damping scale as a red x
                avg_data = spec_data.groupby(' ScaleFactor')[metric].mean().reset_index()
                ax.plot(
                    avg_data[' ScaleFactor'], 
                    avg_data[metric], 
                    color='red', 
                    marker='x', 
                    linestyle='-', 
                    linewidth=1.5,
                    label='Average'
                )

            # Subplot styling
            ax.set_title(f"Spec:{spec_data['display_title'].iloc[0]}") # Truncate long names for title #TODO: figure out why I need an iloc[0] here
            ax.set_xlabel('Scale Factor')
            ax.set_ylabel(metric)
            ax.grid(True, linestyle='--', alpha=0.6)

        # Hide any unused subplot axes
        for j in range(i + 1, len(axes_flat)):
            axes_flat[j].axis('off')
    elif plot_type == 'avg_on_one': #TODO:Make the color per root spectrum the same with each derived spectrum having a separate marker:: #For all spectrums (root and derived), plots the average of the seeds for each damping value.
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Determine grouping based on optional argument
        color_by_spec = kwargs.get('color_by_spec', True)
        
        # Setup colors: either per-spectrum or per-spec group
        color_map = plt.get_cmap('tab10')
        spec_colors = {}
        color_idx = 0

        for i, spec in enumerate(spectrum):
            spec_data = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]
            display_name = str(spec_data['display_title'].iloc[0])
            
            # Calculate the spec/group key
            spec = display_name[:5] if color_by_spec else spec
            
            # Assign a consistent color to this group
            if spec not in spec_colors:
                spec_colors[spec] = color_map(color_idx % 10)
                color_idx += 1
            
            # Calculate averages
            avg_data = spec_data.groupby(' ScaleFactor')[metric].mean().reset_index()
            
            # Plot #sometimes use semilogy for easier readability
            ax.semilogy(
                avg_data[' ScaleFactor'], 
                avg_data[metric], 
                label=display_name,
                color=spec_colors[spec],
                marker='o',
                linestyle='-',
                alpha=0.8
            )

        ax.set_title(f'Averages for {metric}')
        ax.set_xlabel('Scale Factor')
        ax.set_ylabel(metric)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize='small')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
    elif plot_type == 'avg_by_spec': #For each root spectrum, plot the average of the seeds for each damping value, each derived spectrum has it's own color
        # Group spectrum strings by their first 5 characters
        from collections import defaultdict
        groups = defaultdict(list)
        for spec in spectrum:
            # We fetch the display name once to get the prefix key
            sample_name = str(function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]['display_title'].iloc[0])
            groups[sample_name[:5]].append(spec)
        
        n_groups = len(groups)
        cols = kwargs.get('cols', 2)
        rows = math.ceil(n_groups / cols)
        
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4), constrained_layout=True)
        axes_flat = axes.flatten() if n_groups > 1 else [axes]
        
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
                    color=spec_data['color'].iloc[0]
                )
            
            ax.set_title(f"Spec: {prefix}")
            ax.set_xlabel('Scale Factor')
            ax.set_ylabel(metric)
            ax.legend(fontsize='x-small')
            ax.grid(True, alpha=0.3)

        # Cleanup unused axes
        for j in range(i + 1, len(axes_flat)):
            axes_flat[j].axis('off')
    elif plot_type == 'cor_max_diff_by_spec': #For each root spectrum, plot the difference in energy between the derived "max damping" and the root max energy
        # Group spectrum strings by their first 5 characters
        from collections import defaultdict
        groups = defaultdict(list)
        for spec in spectrum:
            # We fetch the display name once to get the prefix key
            sample_name = str(function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]['display_title'].iloc[0])
            groups[sample_name[:5]].append(spec)
        

        n_groups = len(groups)
        cols = kwargs.get('cols', 2)
        rows = math.ceil(n_groups / cols)
        
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4), constrained_layout=True) #TODO: separate out the figures
        axes_flat = axes.flatten() if n_groups > 1 else [axes]
        ymax = {}
        for i, (prefix, spec_list) in enumerate(groups.items()):
            ax = axes_flat[i]
            max_energy_rows = []

            #Find the max energy and corresponding scale factor for spotter buoy
            spec_spot = [s for s in spec_list if 'custom' in s.lower()][0]
            spec_dat_spot = function_data[(function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec_spot) & (function_data['spectrum_type'].str.contains('spotter'))]
            avg_data_spot = spec_dat_spot.groupby(' ScaleFactor')[metric].mean().reset_index()
            max_energy_row_spot = avg_data_spot.nlargest(1, columns=[metric])

            if 'damping_ref' in kwargs and kwargs['damping_ref'] == 'all_scales': #Plot all the damping scales as references, not just the reference damping scale specified by the user
                all_scale_rows = avg_data_spot.to_dict('records')
                for row in all_scale_rows:
                    sf = row[' ScaleFactor']
                    row['display_title'] = f'Damping {sf}' 
                    row['color'] = 'gray'
            elif 'damping_ref' in kwargs: #Plot the reference damping scale specified by the user as a reference line in the plot
                all_scale_rows = avg_data_spot[avg_data_spot[' ScaleFactor'] == kwargs['damping_ref']].iloc[0]
                all_scale_rows['display_title'] = f'Ref: Scale {kwargs['damping_ref']}'
                all_scale_rows['color'] = 'k'
            else:
                pass

            print(f"max energy row spot {max_energy_row_spot}")
            
            for j, spec in enumerate(spec_list):
                spec_data = function_data[function_data[' IncWaveSpectrumType;IncWaveSpectrumParams'] == spec]
                avg_data = spec_data.groupby(' ScaleFactor')[metric].mean().reset_index()
                max_energy_damp =avg_data.nlargest(1, columns=[metric])[' ScaleFactor'].iloc[0] #Max energy row for the current spectrum, we want to find the scale factor for this row to compare to the spotter max energy row

                max_energy_row = avg_data_spot[avg_data_spot[' ScaleFactor'] == max_energy_damp].copy() # Find the spotter row with the same scale factor as the spotter max energy row

                #Add on the display title and color for the max energy row
                sf_val = max_energy_row[' ScaleFactor'].iloc[0]
                new_vals = spec_data.loc[spec_data[' ScaleFactor'] == sf_val, ['display_title', 'color']].iloc[0]
                max_energy_row[['display_title', 'color']] = new_vals.values

                #Add the max energy row to the list for plotting
                max_energy_rows.append(max_energy_row.iloc[0].to_dict())

            # for row in max_energy_rows:
            #     print(f"for each case: {row['display_title']}: {row[metric]}, {max_energy_row_spot[metric].iloc[0]}, {(row[metric]-max_energy_row_spot[metric].iloc[0])/max_energy_row_spot[metric].iloc[0]}")

            #ymax[prefix] = max(((row[metric]-max_energy_row_spot[metric].iloc[0])/max_energy_row_spot[metric].iloc[0]) for row in max_energy_rows) #TODO: Use ymax to change limits of chart
            all_rows = []
            if locals().get('all_scale_rows') is not None:
                raw_all_scale_rows = locals().get('all_scale_rows')
                if isinstance(raw_all_scale_rows, list):
                    all_rows.extend(raw_all_scale_rows)
                else:
                    all_rows.append(raw_all_scale_rows)
            all_rows.extend(max_energy_rows) #Add the damping reference if added previously

            y_vals = [((row[metric]-max_energy_row_spot[metric].iloc[0])/max_energy_row_spot[metric].iloc[0])*100 for row in all_rows]
            bars = ax.bar([row['display_title'][5:] for row in all_rows], y_vals, color=[row['color'] for row in all_rows])
            ax.bar_label(bars, fmt='%.1f%%', padding=3)
            ax.set_title(f"Spectrum {prefix[:3]}")
            ax.set_xticks(range(len(all_rows)))
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
            ax.set_ylabel('Percent Difference in Energy')
            ax.grid(True, alpha=0.3)

            # dynamic ylim based on actual plotted values for this subplot
            min_y, max_y = min(y_vals), max(y_vals)
            buffer = max(0.1 * (max_y - min_y), 1.0)
            ax.set_ylim(min_y - buffer, max_y + buffer)
            ax.axhline(y=0, linewidth=1, color='k')
            print(f'ax: {ax}')

        #ymax_global = max(ymax.values())
        print(f'ymax: {ymax}')
    fig.suptitle(wrap_title(f"Informed Optimal Damping vs {metric} across Spectrums"), fontsize=16)
    fig.supxlabel('Spectrum used', fontsize =12)
    

def y_data_to_float(y_data): ##TODO
    """
    Convert y_data to float, handling errors.
    """
    print(y_data.dtypes, ' before conversion to float')
    print(y_data, ' before conversion to float')
    y_data = y_data.apply(pd.to_numeric, errors='coerce')#TODO:Figure out why these errors must be coerced
    #print(y_data['SC Load Cell (lbs)'], ' before conversion to float')
    print(y_data.dtypes, 'after conversion to float')
    return y_data
    # print(y_data.dtypes, ' before conversion to float')
    # try:
    #     y_data_float = y_data.astype(float)
    #     print(y_data_float, ' converted to float')
    #     print(y_data.dtypes, ' before conversion to float')
    #      return y_data_float
    # except ValueError:
    #     print(f"Error converting y_data to float: {y_data}")
    #     return None
def wrap_title(*args):
    """
    args: title_test, width
    Wraps title text to a specified width."""
    # textwrap.wrap returns a list of strings, so we join them with \n
    if len(args) < 2:
        width = 60  # default width
    else:
        width = args[1]
    return '\n'.join(textwrap.wrap(args[0], width))
##################TESTING##################
def main():
    spectrum_nums = spectrums.spectrum_list()
    out = hack_heatmap_plot(batch_name='batch_results_20260114105529', batch_name2='batch_results_20260110154141', value='avg_tot_power', error_removal=True, one_physics_step   =0.01, val_plotted=False, damping_values=True, REO = 0.5)
    plot_overlayed_spectrums((spectrum_nums), plots_per_page=6, period=False, types=['spotter', 'bretschneider', 'BretHFP', 'regular'], n_cols=3, metric_sv='energy', cumsum=False, reo_df = out)

    damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339', batch_name5='batch_results_20260327142504', metric='max_spring_range', cols=6, damping_values_avg=True, col_org = True, plot_type='avg_by_spec')
    damping_seed_comparison_plot(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339', batch_name5='batch_results_20260327142504', metric='max_spring_range', cols=6, damping_values_avg=True, col_org = True, plot_type='cor_max_diff_by_spec', damping_ref='all_scales')
    plt.show()
    print("This was a direct call of visualization.py, which should be used sparingly")
##################DONE TESTING##################
if __name__ == '__main__':
    main() 