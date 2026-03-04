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
import ast


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
    read_spectrums_df = read_spectrums()
    spectrum_df = read_spectrums_df[(read_spectrums_df['spectrum_id'] == spectrum_id) & (read_spectrums_df['spectrum_type'] == spectrum_type)]
    
    if spectrum_df.empty:
        raise ValueError(f"Spectrum with ID {spectrum_id} and type {spectrum_type} not found.")
    
    f = spectrum_df['frequency'].iloc[0]
    szz = spectrum_df['varianceDensity'].iloc[0]

    f = np.array(ast.literal_eval(f))
    szz = np.array(ast.literal_eval(szz))
    
    return f, szz

def construct_bretschneider(spectrum_id, **kwargs):
    """_summary_

    Parameters
    ----------
    spectrum_id : string or int
        The ID of the spectrum to construct the Bretschneider spectrum for.
    **kwargs
        new_spectrum
    """    
    spectrum_df = read_spectrums()
    if 'new_spectrum' in kwargs and kwargs.get('new_spectrum', True):
        if kwargs.get('Hs') is not None and kwargs.get('Tp') is not None:
            Hs = kwargs['Hs']
            Tp = kwargs['Tp']
        else:
            raise ValueError("Must provide Hs and Tp to construct a new Bretschneider spectrum.")
    else: #This is when I do not have a new spectrum and construct off of the 
        Hs, Tp = spectrum_df[(spectrum_df['spectrum_id']==spectrum_id) & (spectrum_df['spectrum_type']=='spotter')].iloc[0][['significantWaveHeight', 'peakPeriod']]
    print(f"Constructing Bretschneider spectrum for Hs={Hs} and Tp={Tp}")

    peak_freq = 1/Tp
    spotter_freq =np.array([0.0293, 0.03906, 0.04883, 0.05859, 0.06836, 0.07813, 0.08789, 0.09766, 0.10742, 0.11719, 0.12695, 0.13672, 0.14648, 0.15625, 0.16602, 0.17578, 0.18555, 0.19531, 0.20508, 0.21484, 0.22461, 0.23438, 0.24414, 0.25391, 0.26367, 0.27344, 0.2832, 0.29297, 0.30273, 0.3125, 0.32227, 0.33203, 0.35156, 0.38086, 0.41016, 0.43945, 0.46875, 0.49805, 0.6543])
    #interpolate to fill out the spectrum to be twice as dense
    x = np.arange(len(spotter_freq))
    x_new = np.linspace(0, len(spotter_freq) - 1, len(spotter_freq) * 3 - 2)
    spotter_freq_dense = np.interp(x_new, x, spotter_freq)

    bretschneider_szz = (5/16) * (Hs**2) * ((peak_freq**4) / (spotter_freq_dense**5)) * np.exp(-1.25 * (peak_freq/spotter_freq_dense)**4)

    temp_df = pd.DataFrame({
    'frequency': [spotter_freq_dense.tolist()], 
    'varianceDensity': [bretschneider_szz.tolist()], 
    'spectrum_id': [spectrum_id], 
    'spectrum_type': 'bretschneider'
    })

    write_spectrums(temp_df)
     

def read_spectrums():
    """
    Reads the spectrums csv file 
        ----------
        Parameters:
            None
        ----------
        Returns:
            spectrums_df: DataFrame containing the spectrums data
    """
    spectrums_csv = r'C:\Users\Alex Eagan\Documents\GitHub\Mbari_Wec_Compare\spectrums.csv'  # Path to your spectrums CSV file
    if os.path.exists(spectrums_csv):
        spectrums_df = pd.read_csv(spectrums_csv)
        #print(f"Spectrums data loaded with {len(spectrums_df)} rows and {len(spectrums_df.columns)} columns.")
    else:
        raise FileNotFoundError(f"{spectrums_csv} not found. Please ensure the file exists in the correct location.")
    
    return spectrums_df

def write_spectrums(df):
    """
    Writes the spectrums DataFrame to a CSV file
    
        Parameters
        ----------
        df: DataFrame containing the spectrums data to write
        Returns
        None
    """
    spectrums_df = read_spectrums()
    combined_df = pd.concat([spectrums_df, df], ignore_index=True).drop_duplicates(subset=['spectrum_id', 'spectrum_type']).reset_index(drop=True)

    spectrums_csv = r'C:\Users\Alex Eagan\Documents\GitHub\Mbari_Wec_Compare\spectrums.csv'  # Path to your spectrums CSV file
    combined_df.to_csv(spectrums_csv, index=False)
    print(f"Spectrums data written to {spectrums_csv} with {len(combined_df)} rows and {len(combined_df.columns)} columns.")

def remove_spectrum(spectrum_id, spectrum_type):
    """
    Removes a spectrum from the spectrums CSV file based on its ID and type
    
        Parameters
        ----------
        spectrum_id: The ID of the spectrum to remove
        spectrum_type: The type of the spectrum to remove (e.g., 'spotter', 'bretschneider')
        Returns
        None
    """
    spectrums_df = read_spectrums()
    updated_df = spectrums_df.drop(spectrums_df[(spectrums_df['spectrum_id'] == spectrum_id) & (spectrums_df['spectrum_type'] == spectrum_type)].index)
    spectrums_csv = r'C:\Users\Alex Eagan\Documents\GitHub\Mbari_Wec_Compare\spectrums.csv'  # Path to your spectrums CSV file
    
    updated_df.to_csv(spectrums_csv, index=False)
    print(f"Spectrums data written to {spectrums_csv} with {len(updated_df)} rows and {len(updated_df.columns)} columns, following dropping of spectrum ID {spectrum_id} and type {spectrum_type}.")

def main():
    for i, num in enumerate(spectrum_list()):
        construct_bretschneider(num)

    #print('It appears you are running spectrums.py directly. This module is intended to be imported and used by other scripts.')

if __name__ == '__main__':
    main()