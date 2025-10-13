# Importing all the runs from a batch
# Take in the batchfolder - output the runs to the main DF and output
#   the batchfolder to a rebuild batchfolder log
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def import_batch(batch_file_name):
    #Take the batch file name, find the file, import that file name to batchfolder log

    add_datalog(batch_file_name) #Final step - add to log
##################################################################################


def batch_filepath_sourcing():
    #Take the batch file name and return the file path

def add_datalog(file_name):
    # Reads a CSV created from a pandas DataFrame, adds a row with file_name and date, writes back to CSV
    #TODO: Add in a check that writes the old csv to a backup dropbox folder.
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
    new_row = {'file_name': file_name, 'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Write back to CSV
    df.to_csv(datalog_csv, index=False)
    