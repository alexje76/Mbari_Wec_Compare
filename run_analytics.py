##########
# run_analytics.py
# A module of functions that perform analytics on the run passed into the function. 
# TODO Write the analytics to use from main script
# TODO: Create a function that combines trim and get data
# TODO: Add in docstrings for functions


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob
import warnings

import mainDF_management as mDF_mgmt 


def analytics(**kwargs):
    #First see if it is a batch, to get and pass each run individually
    if 'batch_name' in kwargs and not 'run_number' in kwargs:
        mainDF = mDF_mgmt.access_mainDF()
        analytics_data = mainDF[mainDF['batch_file_name'] == kwargs['batch_name']]
        print (analytics_data)
    #TODO: implement other non batch cases

    #Get the analysis type
    analytic = kwargs['analytic']
    #Second run analytic function for each run 
    for index, row in analytics_data.iterrows():
        pblog_name = row[' pblogFilename'].strip()
        run_data = get_data(pblog_name=pblog_name)
        #print(run_data)

        if row['trim']:
            trim_amount = row['trim']
            if trim_amount > 0:
                pass
                print('trimming in greater than 0') #Debugging
            else:
                trim_amount = 0 ####TODO: CHANGE THIS TRIM TO BE DYNAMIC
               # print('trimming in the else - is a #todo') #Debugging
        else:
            trim_amount = 0  # seconds
            warnings.warn(f"No trim amount specified for {pblog_name}. Proceeding without trimming.")

        if kwargs['window_length']:
            window_length = kwargs['window_length']
        else:
            window_length = 0

        trimmed_data = trim(run_data, trim_amount, window_length)

        mainDF.at[index, analytic.__name__] = analytic(trimmed_data)
        print(mainDF.at[index, analytic.__name__])
        mDF_mgmt.write_mainDF(mainDF)

        ######## HERE IS CODE TO TEMPORARILY PLOT AGAINST DIFFERENT TRIM AMOUNTS - MOVING WINDOW
        columns = ['i', 'trimamount', 'avg_power']
        transient_data = pd.DataFrame(columns=columns)
        for i in range(62):
            trim_amount = i*8
            trimmed_data = trim(run_data, trim_amount, window_length)
            analytictransient = mainDF.at[index, analytic.__name__] = analytic(trimmed_data)
            transient_data.loc[len(transient_data)] = [i, trim_amount, analytictransient]
    transient_data.to_csv('transient.csv', index=False)

######## POWER FUNCTIONS ##########
def avg_tot_power(trimmed_data):
    #Calculate average total power from a run
    PC_voltage = trimmed_data[' PC Bus Voltage (V)']
    #print(PC_voltage)
    PC_batt_current = trimmed_data[' PC Battery Curr (A)']
    PC_load_current = trimmed_data[' PC Load Dump Current (A)']

    avg_total_power_list = (PC_voltage * (PC_batt_current + PC_load_current))
   # print (avg_total_power_list)
    avg_total_power = np.mean(avg_total_power_list)
    #print(avg_total_power)

    if not np.isscalar(avg_total_power): raise TypeError(f"avg_total_power must be a scalar number, got {type(avg_total_power).name}")
    else:
        return avg_total_power


######## END POWER FUNCTIONS #############################

def trim(data, trim_amount, window_length):
    """
    Trim the data by the specified amount from start and end
    """
    start_time = data[' Timestamp (epoch seconds)'].iloc[0] #TODO:Make sure this is not an off by 1 error
    trim_start_time = start_time + trim_amount

    trim_idx_start = data.index[data[' Timestamp (epoch seconds)'] >= trim_start_time][0]

    if window_length != 0:
        trim_end_time = trim_start_time + int(window_length)
        #print('trim end time, debugging') #debugging
        trim_idx_end = data.index[data[' Timestamp (epoch seconds)'] <= trim_end_time][-1]

        return data.iloc[trim_idx_start:trim_idx_end]

    else: 
        return data.iloc[trim_idx_start:]


def get_data(**kwargs): #deciding how to access data - batchname and run number, mainDF index, pblogname (closest to run name) ##probably use kwargs
    """
    Accessing the data using the mainDF path
    """
    if 'batch_name' in kwargs and 'run_number' in kwargs:
        #get mainDF index from batch name and run number
        #TODO: implement
        pass
    elif 'mainDF_index' in kwargs:
        #get pblog name from mainDF index
        #TODO: implement
        pass
    elif 'pblog_name' in kwargs:
        #get pblog name directly
        pblog_name = kwargs['pblog_name']
    else:
        raise ValueError("Must provide either batch_name and run_number, mainDF_index, or pblog_name to access data.")    

    run_data_path = glob.glob(os.path.join(r"C:\Users\Alex Eagan\MREL Dropbox\Alex James Eagan\RcloneData", "**", pblog_name, "*"), recursive=True) #TODO: change TestingData to batches
    #print(glob.glob(f"Convergence_MCWaves/*", recursive=True))
    if run_data_path:
        run_data_path = run_data_path[0]
        #print (run_data_path) #Debugging
    else:
        raise FileNotFoundError(f"{pblog_name} not found")

    run_data = pd.read_csv(run_data_path)
    return run_data

##################TESTING##################
def main():
    analytics(batch_name='batch_results_20251102162055', analytic=avg_tot_power, window_length='8')

    
##################DONE TESTING##################

if __name__ == '__main__':
    main()