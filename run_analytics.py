##########
# run_analytics.py
# A module of functions that perform analytics on the run passed into the function. 
# TODO Write the analytics to use from main script
# TODO: Create a function that combines trim and get data
# TODO: Add in docstrings for functions


import pstats

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob
import warnings
import cProfile
import pstats
import multiprocessing as mp

import mainDF_management as mDF_mgmt 
import visualization #TODO: remove circular import if possible, added in specifcially for transient plot

class AnalyticWrapper:
    """Picklable wrapper for analytic functions"""
    def __init__(self, analytic_func):
        self.analytic_func = analytic_func
    
    def __call__(self, data):
        return self.analytic_func(data)
    
    @property
    def name(self):
        return self.analytic_func.__name__

_worker_mainDF = None
_worker_analytic = None

def worker_initializer(mainDF_read_data, analytic_wrapper):
    """Initialize worker process with shared data
    This function is called when each worker process starts. It sets global variables that can be accessed by the worker function.
    """
    global _worker_mainDF, _worker_analytic
    _worker_mainDF = mainDF_read_data  # Read-only copy
    _worker_analytic = analytic_wrapper


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
            print(f'the trim amount for {pblog_name} is {trim_amount}') #Debugging
            if trim_amount > 0:
                print('trimming in greater than 0') #Debugging
                pass
            else:
                trim_amount = (run_data[ ' Timestamp (epoch seconds)'].iloc[-1] - run_data[ ' Timestamp (epoch seconds)'].iloc[0])*0.1 ####TODO: CHANGE THIS TRIM TO BE DYNAMIC
                print('trimming in the else - is a #todo') #Debugging
        else:
            trim_amount = 0  # seconds
            warnings.warn(f"No trim amount specified for {pblog_name}. Proceeding without trimming.")

        if 'window_length' in kwargs:
            window_length = kwargs['window_length']
        else:
            window_length = 0

        #print(trim_amount)
        trimmed_data = trim(run_data, trim_amount, window_length)

        if analytic == 'sim_run_time':
            mainDF.at[index, analytic.__name__] = analytic(run_data)
            print('debugging- used run data not trimmed')
        else:
            mainDF.at[index, analytic.__name__] = analytic(trimmed_data)
        print(mainDF.at[index, analytic.__name__])
        mDF_mgmt.write_mainDF(mainDF)

        ######## HERE IS CODE TO TEMPORARILY PLOT AGAINST DIFFERENT TRIM AMOUNTS - MOVING WINDOW
        if 'transient_investigation' in kwargs and kwargs['transient_investigation'] == True: #TODO: generalize or refactor
            if kwargs['transient_investigation'] == True:
                columns = ['i', 'trimamount', 'avg_power']
                transient_data = pd.DataFrame(columns=columns) #create frame to hold transient data
                for i in range(50):
                    trim_amount = i*window_length
                    trimmed_data = trim(run_data, trim_amount, window_length)
                    analytictransient = mainDF.at[index, analytic.__name__] = analytic(trimmed_data)
                    transient_data.loc[len(transient_data)] = [i, trim_amount, analytictransient]
                visualization.transient_investigation_plot(transient_data, pblog_name)

def analytics_parallel(transient_invesigation=False, **kwargs):
    #First see if it is a batch, to get and pass each run individually
    if 'batch_name' in kwargs and not 'run_number' in kwargs:
        mainDF = mDF_mgmt.access_mainDF()
        analytics_data = mainDF[mainDF['batch_file_name'] == kwargs['batch_name']]
        print (analytics_data)
    #TODO: implement other non batch cases

    if transient_invesigation:
        raise NotImplementedError("Parallel transient investigation not implemented yet. Please run analytics function with transient_investigation=True for now rather than parallel.")
    
    #Get the analysis type and use class above to pass it
    analytic = kwargs['analytic']
    analytic_wrapper = AnalyticWrapper(analytic)

    # Prepare mainDF as read-only data for workers
    mainDF_read_data = mainDF.copy()
    
    #Start up the parallel processes and run the analytics in parallel, passing the mainDF as read only and analytic wrapper to each process
    with mp.Pool(
                processes=min(mp.cpu_count()-2), 
                #processes=4,
                initializer=worker_initializer, 
                initargs=(mainDF_read_data, analytic_wrapper) #MainDF here is read only
    ) as pool:
                results = pool.starmap(
                analytics_parallel_process, 
                analytics_data.iterrows()
        )
    
    #Now take the results returned by each process and write them back to the mainDF using the index passed in, then write the mainDF to csv
    for result in results:
        mainDF.at[result['index'], result['analytic']] = result['result']

     # Write updated mainDF once
    mDF_mgmt.write_mainDF(mainDF)
    
    print(f"\nCompleted {len(results)} runs:")
    for result in results:
        print(f"  {result['pblog']}: {result['result']:.2f} ({result['analytic']})")
    
    return results

def analytics_parallel_process(index, row):
    """
    Using global variables from initializer, calculate an analytic for a single run and return the result along with the index and analytic name to be written back to mainDF by the parent process.
    Inputs: index - index from main DF
            row - row containing information for the run (mainDF row)  
    Outputs: dictionary containing index, pblog name, analytic name, and result to be written back to mainDF by parent process
    WARNINGS: 
        - This function cannot handle window lengths other than 0
        - This function cannot handle transient investigation
        - Sim_run_time is the only analytic run on non-trimmed data. 
        - Trim amounts are set to be 10% of the total runtime if there is not a ['trim'] col in mainDF
    """
    global _worker_mainDF, _worker_analytic

    if _worker_mainDF is None or _worker_analytic is None: #Check if the parallel processs is correctly implemented and initialized
        raise RuntimeError("Worker not initialized properly")
    
    mainDF = _worker_mainDF  #Gather the necessary "arguments"
    analytic_func = _worker_analytic.analytic_func
    analytic_name = _worker_analytic.name

    pblog_name = row[' pblogFilename'].strip()
    run_data = get_data(pblog_name=pblog_name)
    #print(run_data)

    if row['trim']:
        trim_amount = row['trim']
        if trim_amount > 0:
            print('trimming in greater than 0') #Debugging
            pass
        else:
            trim_amount = (run_data[ ' Timestamp (epoch seconds)'].iloc[-1] - run_data[ ' Timestamp (epoch seconds)'].iloc[0])*0.1 ####TODO: CHANGE THIS TRIM TO BE DYNAMIC
            #print('trimming in the else - is a #todo') #Debugging
    else:
        trim_amount = 0  # seconds
        warnings.warn(f"No trim amount specified for {pblog_name}. Proceeding without trimming.")

    window_length = 0
    trimmed_data = trim(run_data, trim_amount, window_length)

    if analytic_name == 'sim_run_time':
        result = analytic_func(run_data)
        print(f'  {pblog_name}: using untrimmed data')
    else:
        result = analytic_func(trimmed_data)
    return {
        'index': index,
        'pblog': pblog_name,
        'result': result,
        'analytic': analytic_name
    }


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
    max_spring_range = trimmed_data[' SC Range Finder (in)'].max()  #Pandas Series has method .max
    #print(f'max spring range is {max_spring_range} at index {np.argmax(trimmed_data[" SC Range Finder (in)"])}') #Debugging

    if not np.isscalar(max_spring_range): raise TypeError(f"must be a scalar number, got {type(max_spring_range).name}")
    else:
        return max_spring_range

def percentile_95_spring_range(trimmed_data):
    percentile_95_spring_range = trimmed_data[' SC Range Finder (in)'].quantile(0.95)
    #print(f'max spring range is {max_spring_range} at index {np.argmax(trimmed_data[" SC Range Finder (in)"])}') #Debugging

    if not np.isscalar(percentile_95_spring_range): raise TypeError(f"must be a scalar number, got {type(percentile_95_spring_range).name}")
    else:
        return percentile_95_spring_range
######## END SPRING FUNCTIONS #############################s

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


def get_data(feather=True, **kwargs): #deciding how to access data - batchname and run number, mainDF index, pblogname (closest to run name) ##probably use kwargs
    """
    Accessing the data using the mainDF path

    ---------
    Parameters:
        feather: bool, optional: Whether to use feather files for faster access if available, by default True
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
    
    # Define the feather directory path
    feather_dir = r"F:\MBARI\runFeathers"
    # Ensure the directory exists
    os.makedirs(feather_dir, exist_ok=True)
    pblog_name_feather = pblog_name[:-6]

    if f"{pblog_name_feather}.feather" in os.listdir(feather_dir): # TODO
        run_data = pd.read_feather(f"{feather_dir}\\{pblog_name_feather}.feather")
    else:
        print(os.path.join(r"C:\Users\Alex Eagan\MREL Dropbox\Alex James Eagan\RcloneData", "**", pblog_name, "*"))
        run_data_path = glob.glob(os.path.join(r"C:\Users\Alex Eagan\MREL Dropbox\Alex James Eagan\RcloneData", "**", pblog_name, "*"), recursive=True) #TODO: change TestingData to batches
        #print(glob.glob(f"Convergence_MCWaves/*", recursive=True))
        if run_data_path:
            run_data_path = run_data_path[0]
            #print (run_data_path) #Debugging
        else:
            raise FileNotFoundError(f"{pblog_name} not found")

        run_data = pd.read_csv(run_data_path)
        if feather == True: #TODO: change to be more dynamic
           run_data.to_feather(f"{feather_dir}\\{pblog_name_feather}.feather")
            
        #run_data = run_data.str.replace("\U00002013", "-").str.replace(r'^-$', '0', regex=True).astype(float) #this line is an attempt to fix dashes converting to objects instead of floats - not working currently

    return run_data

def batch_names(**kwargs):
    if 'batch_name' in kwargs and 'run_number' not in kwargs:
        # Define keys to check in order (batch_name, batch_name2, batch_name3, etc.)
        batch_keys = [kwargs[k] for k in kwargs if k.startswith('batch_name')]
        return batch_keys
    else:
        raise ValueError("Must provide batch_name(s) without run_number to get batch names.")
    
def run_all_except(analytic, copies=False, **kwargs):
    """Calculates the analytic given for all simulations that were previously run and recorded in the mainDF,
        Those batches explicity excluded by batch name in kwargs will not be run,
        Copies changes if there it does so for any copies. 

    Parameters
    ----------
    analytic : variable(I think?)
        _description_
    copies : bool, optional
        set to be True if you want copies to be included, by default False

    Warnings:
        - The copies parameter would not remove past the 10th copy of the same batch. 
    """    
    if 'batch_name' in kwargs and 'run_number' not in kwargs:
        # Define keys to check in order (batch_name, batch_name2, batch_name3, etc.)
        batch_keys_ex = [kwargs[k] for k in kwargs if k.startswith('batch_name')]
    else:
        batch_keys_ex = []
        pass #TODO add back in

    mainDF = mDF_mgmt.access_mainDF()
    batch_names = mainDF['batch_file_name'].unique()
    
    if not copies: #Removes all batch names that are copies - eg end in _* 
        batch_names = [batch for batch in batch_names if not any(batch.endswith(f"_{i}") for i in range(1, 10))]
    else:
        pass
    
    for batch_name in batch_names:
        if batch_name not in batch_keys_ex:
            print(f"Running analytics for batch: {batch_name}")
            analytics_parallel(batch_name=batch_name, analytic=analytic)
    

##################TESTING##################
def main():

    #run_all_except(analytic=max_spring_range, batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339') 
    #analytics_parallel(batch_name="batch_results_20260130133904", analytic=max_spring_range)
    # analytics_parallel(batch_name="batch_results_20260304113810", analytic=max_spring_range)
    # analytics_parallel(batch_name="batch_results_20260315141339", analytic=max_spring_range)

    #cProfile.run('analytics(batch_name="batch_results_20260220105054", analytic=max_spring_range)') 
    # for batch_name_idv in batch_names(batch_name='batch_results_20260213182532', batch_name2='batch_results_20260211181904', batch_name3='batch_results_20260304113810', batch_name4='batch_results_20260315141339'):
    #     print(batch_name_idv)
    #     analytics(batch_name=batch_name_idv, analytic=max_spring_range)

    #run_all_except(analytic=percentile_95_spring_range)

    analytics(batch_name="batch_results_20260421161054", analytic=avg_tot_power, transient_investigation=False)
    
##################DONE TESTING##################

if __name__ == '__main__':
    main()