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
import visualization #TODO: remove circular import if possible, added in specifcially for transient plot


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
                trim_amount =0 ####TODO: CHANGE THIS TRIM TO BE DYNAMIC
               # print('trimming in the else - is a #todo') #Debugging
        else:
            trim_amount = 0  # seconds
            warnings.warn(f"No trim amount specified for {pblog_name}. Proceeding without trimming.")

        if 'window_length' in kwargs:
            window_length = kwargs['window_length']
        else:
            window_length = 0

        trimmed_data = trim(run_data, trim_amount, window_length)

        if analytic == 'sim_run_time':
            mainDF.at[index, analytic.__name__] = analytic(run_data)
            print('debugging- used run data not trimmed')
        else:
            mainDF.at[index, analytic.__name__] = analytic(trimmed_data)
        print(mainDF.at[index, analytic.__name__])
        mDF_mgmt.write_mainDF(mainDF)

        ######## HERE IS CODE TO TEMPORARILY PLOT AGAINST DIFFERENT TRIM AMOUNTS - MOVING WINDOW
        if 'transient_investigation' in kwargs:
            if kwargs['transient_investigation'] == True:
                columns = ['i', 'trimamount', 'avg_power']
                transient_data = pd.DataFrame(columns=columns)
                for i in range(62):
                    trim_amount = i*8
                    trimmed_data = trim(run_data, trim_amount, window_length)
                    analytictransient = mainDF.at[index, analytic.__name__] = analytic(trimmed_data)
                    transient_data.loc[len(transient_data)] = [i, trim_amount, analytictransient]
                visualization.transient_investigation_plot(transient_data)

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

def max_timestep_power(trimmed_data): #TODO change to be consistent naming
        #Calculate max instant total power from a run
    PC_voltage = trimmed_data[' PC Bus Voltage (V)']
    #print(PC_voltage)
    PC_batt_current = trimmed_data[' PC Battery Curr (A)']
    PC_load_current = trimmed_data[' PC Load Dump Current (A)']

    avg_total_power_list = (PC_voltage * (PC_batt_current + PC_load_current))
   # print (avg_total_power_list)
    max_total_power_instant = np.max(avg_total_power_list)
    #print(avg_total_power)

    if not np.isscalar(max_total_power_instant): raise TypeError(f"must be a scalar number, got {type(max_total_power_instant).name}")
    else:
        return max_total_power_instant

######## END POWER FUNCTIONS #############################
######## START SPRING FUNCTIONS #############################
def max_spring_range(trimmed_data):
    spring_range = trimmed_data[' SC Range Finder (in)']
    max_spring_range = np.max(spring_range)

    if not np.isscalar(max_spring_range): raise TypeError(f"must be a scalar number, got {type(max_spring_range).name}")
    else:
        return max_spring_range

######## END SPRING FUNCTIONS #############################

####### START UNGROUPED FUNCTIONS ###########################
# ##Not doing what I hoped atm #TODO
# def sim_run_time(run_data):  
#     start_time = run_data[' Timestamp (epoch seconds)'].iloc[0]
#     end_time = run_data[' Timestamp (epoch seconds)'].iloc[-1]
#     sim_run_time = start_time-end_time

#     if not np.isscalar(sim_run_time): raise TypeError(f"must be a scalar number, got {type(sim_run_time).name}")
#     else:
#         return sim_run_time
####### END UNGROUPED FUNCTIONS ############################

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


        print(trim_idx_start)
        print(trim_idx_end)
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

    print(os.path.join(r"C:\Users\Alex Eagan\MREL Dropbox\Alex James Eagan\RcloneData", "**", pblog_name, "*"))
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
    analytics(batch_name='batch_results_20251121160129', analytic=avg_tot_power, window_length=8, transient_investigation=True)

    
##################DONE TESTING##################

if __name__ == '__main__':
    main()