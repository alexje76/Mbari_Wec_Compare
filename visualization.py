import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
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
    #plt.xscale('log') #for physics step
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
    plt.ylabel('m/s (untitled)')

    plt.title(f"Data Plot for {plot_data_name}: {y_name} vs {kwargs['x']}")
    plt.legend(markerscale = 7)
    #plt.grid()
    plt.gca().yaxis.set_major_locator(MaxNLocator(nbins=9))

    plt.show()

##################TESTING##################
def main():
    #plot_data(batch_name='batch_results_20251102162754_1', x=' PhysicsStep', y='max_spring_range', remove_end_runs=2)
    #plot_data_runs(pblog_name='results_run_0_20251104192421\\pblog', x=' Timestamp (epoch seconds)', y=' XB X Rate', y2=' XB Y Rate', y3=' XB Z Rate')
    #plot_data_runs(pblog_name='results_run_0_20251104192421\\pblog', x=' Timestamp (epoch seconds)', y=' XB Pitch Angle (deg)', y2='  XB Roll XB Angle (deg)', y3=' XB Yaw Angle (deg)')
    plot_data_runs(pblog_name='results_run_0_20251104192421\\pblog', x=' Timestamp (epoch seconds)', y=' XB North Vel', y2=' XB East Vel', y3=' XB Down Vel')
    #plot_data_runs(pblog_name='results_run_0_20251104192421\\pblog', x=' Timestamp (epoch seconds)', y=' XB Long')

##################DONE TESTING##################

if __name__ == '__main__':
    main()