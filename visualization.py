import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob

import mainDF_management as mDF_mgmt 

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

    print(x)
    
    #Plot the data
    plt.figure(figsize=(10, 6))
    plt.title(f"Data Plot for {plot_data_name}: {kwargs['y']} vs {kwargs['x']}")

    plt.scatter(x, y)
   # plt.xscale('log') #for physics step
    plt.xlabel(kwargs['x'])
    plt.ylabel(kwargs['y'])
    plt.grid()
    plt.show()

##################TESTING##################
def main():
   plot_data(batch_name='batch_results_20251027105926', x=' PhysicsStep', y='avg_tot_power')

    
##################DONE TESTING##################

if __name__ == '__main__':
    main()