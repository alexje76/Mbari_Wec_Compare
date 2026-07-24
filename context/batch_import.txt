"""
Module to import the batch results into the main DataFrame for the MBARI WEC project

Functions:
- import_batch(batch_file_name): Import all runs from the specified batch into mainDF and datalog.
- add_to_mainDF(batch_file_path, batch_file_name): Helper function to add runs from a batch to mainDF.
- batch_filepath_sourcing(batch_file_name): Helper Function to locate the file path of the specified batch.
- add_datalog(file_name): Add an entry for the batch to the datalog CSV as a backup to re-create mainDF and record import timings.
"""
# Importing all the runs from a batch
# Take in the batchfolder - output the runs to the main DF and output
#   the batchfolder to datalog (designed to rebuild mainDF from)

# TODO: add in a print output option
# TODO: insert docstrings for functions
# TODO: add in when mainDF was created/last modified
# TODO: Check and create from datalog if mainDF does not exist
# TODO: add in check for exit code being 0, and update active column correspondingly
# TODO: update the 

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob
import sys
from collections import defaultdict

import mainDF_management as mDF_mgmt 


def import_batch(batch_file_name, batch_file_path=None):
    """
    Take the batch file name, find the file.
    Import the data to the mainDF, then import that file name to batchfolder log
    """
    if batch_file_path is None:
        batch_file_path = batch_filepath_sourcing(batch_file_name) #Find batch file path

    global mainDF
    mainDF = mDF_mgmt.access_mainDF()  # Get mainDF (returned) in scope
    if mainDF.empty or 'run_data_path' not in mainDF.columns or not (mainDF['run_data_path'].dropna().str.startswith(batch_file_path).any()):  # Check if mainDF has batch data or empty
        add_to_mainDF(batch_file_path, batch_file_name) #Import batch to main DF 
    else:
        print("mainDF already imported this batch:")
        user_input = input("Type 'N' to exit without importing, any other key will continue: ")
        if user_input.lower() == 'n':
            sys.exit(0)
        else:
            add_to_mainDF(batch_file_path, batch_file_name) #Import batch to main DF
        
    mDF_mgmt.write_mainDF(mainDF) #Write mainDF to csv

    add_datalog(batch_file_name) #Final step - add to log 

def add_to_mainDF(batch_file_path, batch_file_name):
    #Import all the run data from a batch to the main DataFrame
    #TODO: THIS DOES NOT HANDLE THE RUNS CORRECTLY YET
    batch_run_logs_path = os.path.join(batch_file_path, 'batch_runs.log')

    if os.path.exists(batch_run_logs_path):
        # skip comment lines (the file starts with a '# Generated X simulator runs' line) so pandas reads the true header
        batch_run_logs = pd.read_csv(batch_run_logs_path, comment='#')
    else:
        print(f"batch_runs.log not found at expected location: {batch_run_logs_path}")
    
    for run_idx, run_row in batch_run_logs.iterrows():  #Read each run from the batch_runs.log
        print() #A blank line for readability
        print(f"Processing run {run_idx} from batch_runs.log")
        # use the exact column name from the log header (case and whitespace sensitive), join to batchpath, replace backwards slashes for cross-platform compatibility 
        run_pblogdir_path = os.path.normpath(os.path.join(batch_file_path, str(run_row[' pblogFilename']).strip()))
        if not os.path.exists(run_pblogdir_path):
            print(f"  [SKIP] pblog directory not found, skipping run {run_idx}: {run_pblogdir_path}")
            input('Enter to continue')
            continue

        csv_files = [f for f in os.listdir(run_pblogdir_path) if f.endswith('.csv')]

        if not csv_files:
            print(f"  [SKIP] No CSV file found in pblog directory, skipping run {run_idx}: {run_pblogdir_path}")
            input('Enter to continue')
            continue

        run_data_path = os.path.join(run_pblogdir_path, csv_files[0])

        if os.path.exists(run_data_path):
            global mainDF
            # combine run metadata into a single Series, add path, and append as one new row to mainDF
            run_info = pd.concat([pd.Series({'batch_file_name': batch_file_name}), run_row]) 
            run_info['run_data_path'] = run_data_path
            run_info['active'] = True
            run_info['sim'] = True
            run_info['trim'] = None

            mainDF = pd.concat([mainDF, run_info.to_frame().T], ignore_index=True, sort=False)
            print(f"Appended run from {run_data_path} to mainDF.")
    
    if mainDF.dropna(subset=['run_data_path']).duplicated(subset='run_data_path').any(): #Checking for duplicates and asking for input to continue
        print("after appending these runs, mainDF has duplicate runs:")
        usr_input = input("Type; 'N' to exit without importing, 'R' to replace duplicates with new entries, if no entry defaults to keep original mainDF entries : ")
        if usr_input.lower() == 'n':
            sys.exit(0)
        elif usr_input.lower() == 'r':
            mainDF = mainDF.drop_duplicates(subset='run_data_path', keep='last')
        else:
            print('Defaulting to keeping original mainDF entries, new duplicates will be discarded.')
            mainDF = mainDF.drop_duplicates(subset='run_data_path', keep='first')
        return


def batch_filepath_sourcing(batch_file_name):
    """
    Take the batch file name and return the file path
    This function searches through all of my dropbox folder RcloneData
    """
    import os
    found_paths = []
    search_path_starting = r'C:\Users\Alex Eagan\MREL Dropbox\Alex James Eagan\RcloneData' #starting search path

    # Walk through the directory, checking both directories and files for a match
    for root, dirs, files in os.walk(search_path_starting):
        for d in dirs:
            if d == batch_file_name:
                found_paths.append(os.path.join(root, d))
                print(f"Found batch_file_path at: {found_paths[-1]}")

    if not found_paths:
        raise FileNotFoundError(f"'{batch_file_name}' not found under {search_path_starting}")

    if len(found_paths) == 1:
        return found_paths[0]
    print(f"Multiple paths found for '{batch_file_name}':")
    for i, p in enumerate(found_paths):
        print(f"  [{i}] {p}")
    while True:
        user_input = input(f"Enter index [0-{len(found_paths)-1}] to select: ").strip()
        if user_input.isdigit() and 0 <= int(user_input) < len(found_paths):
            return found_paths[int(user_input)]
        print("Invalid input, please enter a valid index.") 

def add_datalog(file_name):
    """
        Reads a CSV created from a pandas DataFrame, adds a row with file_name and date, writes back to CSV
    """
    #TODO: adjust the function so that it reports if the file_name is from a batch or sim
    #TODO: add in a check to see if the file_name is already in the datalog, if so, skip adding it again.
    import os
    from datetime import datetime

    datalog_csv = 'datalog.csv'  # Path to your datalog CSV file
    # If the file exists, read it; otherwise, raise an error
    if os.path.exists(datalog_csv):
        df = pd.read_csv(datalog_csv)
        # Print last modified time of the datalog CSV
        last_modified = os.path.getmtime(datalog_csv)
        print(f"Datalog last modified: {datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        raise FileNotFoundError(f"Datalog file '{datalog_csv}' does not exist.")

    # Add new row
    # Avoid adding duplicates
    if 'file_name' in df.columns and file_name in df['file_name'].values:
        print(f"'{file_name}' already present in datalog; skipping add.")
        return

    new_row = {'file_name': file_name, 'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.to_csv(datalog_csv, index=False) #Writes df back to CSV without keeping the index values

def get_sub_batches_paths(batch_names, base_path):
    """
    Takes a list of batch names and returns all sub-batch names with no duplicates.
    If multiple sub-batches exist in the same task folder, keeps the most recent one.
    
    Args:
        batch_names (list): List of batch folder names.
        base_path (str): Base directory containing the batch folders.

    Returns:
        list: List of unique sub-batch paths.
    """
    sub_batches_paths = []
    seen_paths = set()
    most_recent_batches = defaultdict(list)
    
    for batch_name in batch_names:
        batch_path = os.path.join(base_path, batch_name)
        if not os.path.exists(batch_path):
            print(f"Batch path not found: {batch_path}")
            continue
        
        # Traverse task folders within the batch
        for root, dirs, files in os.walk(batch_path):
            for dir_name in dirs:
                if dir_name.startswith("task_"):  # Look for task directories
                    task_path = os.path.join(root, dir_name)
                    
                    # Look for sub-batch directories inside the task directory
                    for sub_batch in os.listdir(task_path):
                        sub_batch_path = os.path.join(task_path, sub_batch)
                        if os.path.isdir(sub_batch_path):  # Ensure it's a directory
                            timestamp = int(sub_batch.split('_')[-1])  # Convert timestamp to integer
                            most_recent_batches[task_path].append((timestamp, sub_batch_path))
    
    # Process each task folder's sub-batches to select the most recent one
    for task_path, sub_batch_list in most_recent_batches.items():
        # Sort by timestamp and take the most recent
        sub_batch_list.sort(key=lambda x: x[0], reverse=True)
        most_recent_path = sub_batch_list[0][1]  # Get the path of the most recent sub-batch
        
        # Add to results if not already seen
        if most_recent_path not in seen_paths:
            sub_batches_paths.append(most_recent_path)
            seen_paths.add(most_recent_path)
    
    return sub_batches_paths

def check_hyak_overlaps(sub_batches_paths):
    """
    Reports any naming collisions across three levels for a resolved list of HYAK sub-batch paths:
      Level 1 - batch_results folder names  (basename of each sub_batch_path)
      Level 2 - pblogFilename values        (relative run dir, from batch_runs.log)
      Level 3 - CSV filenames               (the actual .csv file inside each pblog dir)
    Only reports; does not block importing.
    """
    # --- Level 1: batch_results folder name overlaps ---
    batch_results_map = defaultdict(list)
    for sub_batch_path in sub_batches_paths:
        folder_name = os.path.basename(sub_batch_path)
        batch_results_map[folder_name].append(sub_batch_path)

    batch_results_overlaps = {k: v for k, v in batch_results_map.items() if len(v) > 1}
    if batch_results_overlaps:
        print(f"\n[overlap check] WARNING: {len(batch_results_overlaps)} overlapping batch_results folder name(s) found:\n")
        for folder_name, paths in batch_results_overlaps.items():
            print(f"  '{folder_name}' appears in {len(paths)} locations:")
            for p in paths:
                print(f"    {p}")
    else:
        print("\n[overlap check] No batch_results folder name overlaps found.")

    # --- Level 2 & 3: pblogFilename and CSV filename overlaps ---
    # Both are collected in a single pass over the logs to avoid reading files twice
    pblog_map = defaultdict(list)   # pblogFilename  -> [sub_batch_paths]
    csv_map   = defaultdict(list)   # csv filename   -> [full pblog dir paths]

    for sub_batch_path in sub_batches_paths:
        batch_run_logs_path = os.path.join(sub_batch_path, 'batch_runs.log')
        if not os.path.exists(batch_run_logs_path):
            print(f"[overlap check] WARNING: batch_runs.log not found at {batch_run_logs_path}, skipping.")
            continue

        batch_run_logs = pd.read_csv(batch_run_logs_path, comment='#')
        for _, run_row in batch_run_logs.iterrows():
            pblog_name = str(run_row[' pblogFilename']).strip()
            pblog_map[pblog_name].append(sub_batch_path)

            # Level 3: inspect the actual pblog directory for CSV filenames
            run_pblogdir_path = os.path.normpath(os.path.join(sub_batch_path, pblog_name))
            if os.path.exists(run_pblogdir_path):
                csv_files = [f for f in os.listdir(run_pblogdir_path) if f.endswith('.csv')]
                for csv_file in csv_files:
                    csv_map[csv_file].append(run_pblogdir_path)

    # Report Level 2
    pblog_overlaps = {k: v for k, v in pblog_map.items() if len(v) > 1}
    if pblog_overlaps:
        print(f"\n[overlap check] WARNING: {len(pblog_overlaps)} overlapping pblogFilename(s) found across sub-batches:\n")
        # for pblog_name, paths in pblog_overlaps.items():
        #     print(f"  '{pblog_name}' appears in {len(paths)} sub-batches:")
        #     for p in paths:
        #         print(f"    {p}")
    else:
        print("\n[overlap check] No pblogFilename overlaps found across sub-batches.")

    # Report Level 3
    csv_overlaps = {k: v for k, v in csv_map.items() if len(v) > 1}
    if csv_overlaps:
        print(f"\n[overlap check] WARNING: {len(csv_overlaps)} overlapping CSV filename(s) found:\n")
        # for csv_name, paths in csv_overlaps.items():
        #     print(f"  '{csv_name}' appears in {len(paths)} pblog directories:")
        #     for p in paths:
        #         print(f"    {p}")
    else:
        print("\n[overlap check] No CSV filename overlaps found.")
    print(f"\n[overlap check] Total runs analyzed: {len(pblog_map)}")

def import_hyak_batches(batch_names, base_path=r"C:\Users\Alex Eagan\MREL Dropbox\Alex James Eagan\RcloneData\HYAK2\wec_logs\batches"):
    sub_batches_paths = get_sub_batches_paths(batch_names, base_path)
    check_hyak_overlaps(sub_batches_paths)  # Report overlaps before any importing begins
    input("Press Enter to acknowledge overlaps and continue on...")
    for batch in sub_batches_paths:
        import_batch(os.path.basename(batch), batch_file_path=batch)

    
##################TESTING##################
def main():
#HYAK BATCHES
    batch_names = ['batch_spotter_bret_30_37374379_20260720', 'batch_spotter_bret_SFP_30+_37450154_20260721', 'batch_spotter_bret_SFP_30+_37450154_20260722']
    import_hyak_batches(batch_names)
#Single batch
    # batch_file_name = 'batch_results_20260518185853'
    # import_batch(batch_file_name)
##################DONE TESTING##################

if __name__ == '__main__': 
    main()