"""
This module handles all the sectrum info
Functions:
- full_spectrums(): Reads JSON files for all segments and combines them into one DataFrame.
- spectrum_list(): Simple function to gather all the custom spectrums
"""
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob
import json


def full_spectrums():
    """
    Reads JSON files for all segments and combines them into one DataFrame.
    """
    spectrums = spectrum_list()
    print(f"Gathering spectrums for segments: {spectrums}")
    base_path = r"C:\Users\Alex Eagan\MREL Dropbox\Alex James Eagan\MBARI Data"
    
    df_list = []
    
    for segment_id in spectrums:
        matches = glob.glob(os.path.join(base_path, "**", f"spotter_data_{segment_id}.json"), recursive=True)

        if matches:
            file_path = matches[0]  # Use the first match found
            with open(file_path, 'r') as f:
                try:
                    # Option 1: Directly read if JSON is a standard table format
                    #temp_df = pd.read_json(file_path)
                    
                    # Option 2: Use json_normalize if the JSON is deeply nested
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        temp_df = pd.json_normalize(data)
                    
                    # Add a column to track which segment the data came from
                    temp_df['spectrum_id'] = segment_id
                    temp_df['spectrum_type'] = "spotter"
                    df_list.append(temp_df)
                    
                except Exception as e:
                    print(f"Skipping Spectrum {segment_id} due to error: {e}")
            
    # Concatenate all individual DataFrames into one
    if not df_list:
        raise ValueError("The list of DataFrames is empty. Process halted.")
        
    combined_df = pd.concat(df_list, ignore_index=True)
    return combined_df


def spectrum_list():
    """
    Simple function to gather all the custom spectrums
    #TODO add in the keywords to gather a subset
    """
    mbari_2022 = np.array([114, 198, 260, 384, 532, 597])
    spectrum_list = mbari_2022
    return spectrum_list

def spectrum(spectrum_id, spectrum_type):
    """
    returns the f and szz for a spectrum

    Parameters:
        spectrum_id: integer ID of the spectrum to retrieve
    Returns:
        f: frequency array
        szz: spectral density array
    """
    full_df = full_spectrums() ##TODO: this will be replaced when I have the spectrums in a csv or other format
    spectrum_df = full_df[(full_df['spectrum_id'] == spectrum_id) & (full_df['spectrum_type'] == spectrum_type)]
    
    if spectrum_df.empty:
        raise ValueError(f"Spectrum with ID {spectrum_id} and type {spectrum_type} not found.")
    
    f = np.array(spectrum_df['frequency'].iloc[0])
    szz = np.array(spectrum_df['varianceDensity'].iloc[0])
    
    return f, szz

def main():
    full_spectrums_df = full_spectrums()
    print(full_spectrums_df)

    #print('It appears you are running spectrums.py directly. This module is intended to be imported and used by other scripts.')

if __name__ == '__main__':
    main()