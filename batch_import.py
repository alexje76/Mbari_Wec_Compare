# Importing all the runs from a batch
# Take in the batchfolder - output the runs to the main DF and output
#   the batchfolder to datalog (designed to rebuild mainDF from)

# TODO: check main DF for batch before inserting
# TODO: insert docstrings for functions
# TODO: add in when mainDF was created/last modified
# TODO: Check and create from datalog if mainDF does not exist
# TODO: port out write and access mainDF to a separate module for reuse
# TODO: add in check for exit code being 0, and update active column correspondingly
# TODO: add in comparison for if ALL the batch files have been read in
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob

import mainDF_management as mDF_mgmt 


def import_batch(batch_file_name):
    #Take the batch file name, find the file.
    #Import the data to the mainDF, then import that file name to batchfolder log
    batch_file_path = batch_filepath_sourcing(batch_file_name) #Find batch file path

    global mainDF
    mainDF = mDF_mgmt.access_mainDF()  # Get mainDF (returned) in scope
    if mainDF.empty or not (mainDF['batch_file_name'].str.contains(batch_file_name).any()):  # Check if mainDF has batch data or empty
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
        #print(batch_run_logs)#Debugging
    else:
        print(f"batch_runs.log not found at expected location: {batch_run_logs_path}")
    
    for run_idx, run_row in batch_run_logs.iterrows():  # Read each run from the batch_runs.log
        print()
        print(f"Processing run {run_idx} from batch_runs.log")
        # use the exact column name from the log header (case and whitespace sensitive),join to batchpath, replace backwards slashes for cross-platform compatibility 
        run_pblogdir_path = os.path.normpath(os.path.join(batch_file_path, str(run_row[' pblogFilename']).strip()))
        run_data_path = [f for f in os.listdir(run_pblogdir_path) if f.endswith('.csv')]
        run_data_path = os.path.join(run_pblogdir_path, run_data_path[0])

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
    
    if mainDF.duplicated(subset=' pblogFilename').any() : #Checking for duplicates and asking for input to continue
        print("after appending these runs, mainDF has duplicate runs:")
        usr_input = input("Type; 'N' to exit without importing, 'R' to replace duplicates with new entries, if no entry defaults to keep original mainDF entries : ")
        if usr_input.lower() == 'n':
            sys.exit(0)
        elif usr_input.lower() == 'r':
            mainDF.drop_duplicates(subset=' pblogFilename', keep='last')
        else:
            print('Defaulting to keeping original mainDF entries, new duplicates will be discarded.')
            mainDF.drop_duplicates(subset=' pblogFilename', keep='first')
        return
              

def batch_filepath_sourcing(batch_file_name):
    #Take the batch file name and return the file path
    #TODO: Change search path to be inclusive of dropbox without having dropbox authentication saved
    import os
    found_paths = []
    search_path_starting = r'C:\Users\Alex Eagan\MREL Dropbox\Alex James Eagan\RcloneData'     
    #search_path_starting = r'C:\Users\Alex Eagan\Documents\GitHub\Mbari_Wec_Compare\TestingData'

    # Walk through the directory, checking both directories and files for a match
    for root, dirs, files in os.walk(search_path_starting):
        for d in dirs:
            if d == batch_file_name:
                found_paths.append(os.path.join(root, d))
                print(f"Found batch_file_path at: {found_paths[-1]}")
        #for f in files:
        #    if f == batch_file_name:
        #        found_paths.append(os.path.join(root, f))
        #        print(f"Found file at: {found_paths[-1]}")
        #^ Batches should be folders, not files - not sure if I was a directory back if it would gather a folder path.
        # TODO: Investigate the above behavior

    if not found_paths:
        raise FileNotFoundError(f"'{batch_file_name}' not found under {search_path_starting}")

    return found_paths[-1]

def add_datalog(file_name):

    # Reads a CSV created from a pandas DataFrame, adds a row with file_name and date, writes back to CSV
    #TODO: Add in a check that writes the old csv to a backup dropbox folder. *before, check if it is needed with versioning
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

    # Write back to CSV
    df.to_csv(datalog_csv, index=False)
    
##################TESTING##################
def main():
    batch_file_name = 'batch_results_20251121160129'

    import_batch(batch_file_name)
##################DONE TESTING##################

if __name__ == '__main__':
    main()