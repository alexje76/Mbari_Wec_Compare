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
import sys
import scipy


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
def spectrum_metric_single_value(spectrum_id, spectrum_type, metric):
    """
    returns the metric for a spectrum

    Parameters:
        spectrum_id: integer ID of the spectrum to retrieve
        spectrum_type: string type of the spectrum to retrieve ('spotter', 'bret...)
    Returns:
        metric: the metric value requested
    """
    read_spectrums_df = read_spectrums()
    spectrum_df = read_spectrums_df[(read_spectrums_df['spectrum_id'] == spectrum_id) & (read_spectrums_df['spectrum_type'] == spectrum_type)]
    
    if spectrum_df.empty:
        raise ValueError(f"Spectrum with ID {spectrum_id} and type {spectrum_type} not found.")
    
    if metric not in spectrum_df.columns:
        raise ValueError(f"Metric '{metric}' not found in spectrum data.")
    else:
        metric_value = spectrum_df[metric].iloc[0]
        return metric_value

def construct_bretschneider(spectrum_id, test = False, **kwargs):
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
            Hs = kwargs['Hs'].astype(float)
            Tp = kwargs['Tp'].astype(float)
        else:
            raise ValueError("Must provide Hs and Tp to construct a new Bretschneider spectrum.")
    else: #This is when I do not have a new spectrum and construct off of the 
        Hs, Tp = spectrum_df[(spectrum_df['spectrum_id']==spectrum_id) & (spectrum_df['spectrum_type']=='spotter')].iloc[0][['significantWaveHeight', 'peakPeriod']]
    print(f"Constructing Bretschneider spectrum for Hs={Hs} and Tp={Tp}")

    peak_freq = 1/Tp
    spotter_freq =np.array([0.0293, 0.03906, 0.04883, 0.05859, 0.06836, 0.07813, 0.08789, 0.09766, 0.10742, 0.11719, 0.12695, 0.13672, 0.14648, 0.15625, 0.16602, 0.17578, 0.18555, 0.19531, 0.20508, 0.21484, 0.22461, 0.23438, 0.24414, 0.25391, 0.26367, 0.27344, 0.2832, 0.29297, 0.30273, 0.3125, 0.32227, 0.33203, 0.35156, 0.38086, 0.41016, 0.43945, 0.46875, 0.49805, 0.6543])
    #interpolate to fill out the spectrum to be twice as dense
    x = np.arange(len(spotter_freq))
    x_new = np.linspace(0, len(spotter_freq) - 1, len(spotter_freq) * 3 - 2) #interpolate to have 3x the number of points, so 2 points between each original point
    spotter_freq_dense = np.interp(x_new, x, spotter_freq)

    bretschneider_szz = (5/16) * (Hs**2) * ((peak_freq**4) / (spotter_freq_dense**5)) * np.exp(-1.25 * (peak_freq/spotter_freq_dense)**4)

    if 'spec_type' in kwargs and kwargs.get('spec_type', True):
        temp_df = pd.DataFrame({
        'frequency': [spotter_freq_dense.tolist()], 
        'varianceDensity': [bretschneider_szz.tolist()], 
        'spectrum_id': [spectrum_id], 
        'spectrum_type': 'bretschneider',
        'peakPeriod': Tp,
        'significantWaveHeight': Hs
        })


    if not test: 
        write_spectrums(temp_df)
    if test: #TODO - fix this
        plt.plot(spotter_freq_dense, bretschneider_szz)
        plt.show()
        spotter_freq_dense.round(5)
        spot = np.array2string(spotter_freq_dense,  separator=', ', suppress_small=True)
        bretschneider_szz.round(5)
        bret = np.array2string(bretschneider_szz,  separator=', ', suppress_small=True)
        #print(f"-Custom:")
        #print(f"     f: {spot}")
        #print(f"     Szz = {bret}")

def construct_bretschneider_min(spectrum_id, **kwargs):
    """Constructing 

    Parameters
    ----------
    spectrum_id : string or int
        The ID of the spectrum to construct the Bretschneider spectrum for.
    **kwargs
        new_spectrum
    """     #TODO - fix this
    spectrum_id = spectrum_id
    spectrum_df = read_spectrums()
    f, szz = spectrum_df[(spectrum_df['spectrum_id']==spectrum_id) & (spectrum_df['spectrum_type']=='spotter')].iloc[0][['frequency', 'varianceDensity']]
    clean_szz = szz.strip('[]')
    szz_np = np.fromstring(clean_szz, dtype=float, sep=',')

    clean_f = f.strip('[]')
    f_np = np.fromstring(clean_f, dtype=float, sep=',')
    
    #print(szz_np)
    # 1. Find peaks (returns tuple: indices, properties)
    peak_indices, _ = scipy.signal.find_peaks(szz_np)

    # 2. Check if we found at least one peak
    if len(peak_indices) > 0:
        # If there are 2 or more peaks, take the second one [1]
        # Otherwise, take the first one [0]
        if len(peak_indices) >= 2:
            peak_idx = peak_indices[1]
        else:
            peak_idx = peak_indices[0]
        
        # Get the actual value from the array at that index
        peak_val = szz_np[peak_idx]
    else:
        peak_val = None
        print("No peaks found.")
    #print(peak_val)

    idx = np.where(szz_np == peak_val)
    f_peak = f_np[idx]
    Tp = 1/f_peak
    Hs = np.sqrt((16*peak_val*f_peak)/(5*np.exp(-1.25)))
    #print(f"Tp = {Tp}")
    #print(f"Hs = {Hs}")
    construct_bretschneider(spectrum_id, test = True, new_spectrum=True, Hs = Hs, Tp = Tp)

def calculate_energy(spectrum_id, spectrum_type):
    """
    Calculates the energy of a spectrum by integrating the spectral density over frequency.
    
    Parameters:
        spectrum_id: The ID of the spectrum to calculate energy for
        spectrum_type: The type of the spectrum (e.g., 'spotter', 'bretschneider')
    Returns:
        energy: The calculated energy of the spectrum
    """
    f, szz = spectrum(spectrum_id, spectrum_type)
    energy = np.trapezoid(szz, f)
    return energy

def calculate_all(metric, spectrum_type=None):
    """
    Calculates a specified metric for all spectrums of a given type.
    
    Parameters:
        metric: The metric to calculate (e.g., 'energy')
        spectrum_type: The type of spectrums to calculate the metric for (e.g., 'spotter', 'bretschneider')
    """
    df = read_spectrums()
    if spectrum_type is not None:
        df = df[df['spectrum_type'] == spectrum_type]
    for _, row in df.iterrows():
        df.loc[(df['spectrum_id'] == row['spectrum_id']) & (df['spectrum_type'] == row['spectrum_type']), metric] = globals()[f'calculate_{metric}'](row['spectrum_id'], row['spectrum_type'])
    overwrite_spectrums(df)

def calculate_sim_incidentspectrumtype(spectrum_type = None):
    """Generates the Incidentwave height to have easier plotting names elsewhere

    Parameters
    ----------
    spectrum_type : _type_, optional
        If you only want to calculate one s, by default None
    """    
    df = read_spectrums()
    if spectrum_type is not None:
        df = df[df['spectrum_type'] == spectrum_type]
    print(df[['spectrum_id', 'spectrum_type', 'significantWaveHeight', 'peakPeriod']])
    for i, row in df.iterrows():
        if row['spectrum_type'] == 'spotter':
            f_arr = np.fromstring(df.at[i, 'frequency'].strip('[]'), sep=',')
            szz_arr = np.fromstring(df.at[i, 'varianceDensity'].strip('[]'), sep=',')
            df.at[i, ' IncWaveSpectrumType;IncWaveSpectrumParams'] = f"Custom;f:{':'.join(map('{:g}'.format, f_arr))};Szz:{':'.join(map('{:g}'.format, szz_arr.astype(float)))}"
        elif row['spectrum_type'] == 'bretschneider':
            print(df.at[i, 'significantWaveHeight'])
            df.at[i, ' IncWaveSpectrumType;IncWaveSpectrumParams'] = f"Bretschneider;Hs:{df.at[i, 'significantWaveHeight']};Tp:{df.at[i, 'peakPeriod']}"
        else:
            print(f"Unknown spectrum type {row['spectrum_type']} for spectrum ID {row['spectrum_id']}. Skipping incident spectrum type calculation.")

    print (df[['spectrum_id', 'spectrum_type', ' IncWaveSpectrumType;IncWaveSpectrumParams']])
    overwrite_spectrums(df)

    #CSV handling



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
def overwrite_spectrums(df):
    """
    Writes the spectrums DataFrame to a CSV file
    
        Parameters
        ----------
        df: DataFrame containing the spectrums data to write
        Returns
        None
    """
    old_specs_df = read_spectrums()
    usr_input = input("Type; 'Y' to overwrite old spectrums, if no entry defaults to keep original spectrums entries : ")
    if usr_input.lower() == 'y':
        spectrums_csv = r'C:\Users\Alex Eagan\Documents\GitHub\Mbari_Wec_Compare\spectrums.csv'  # Path to your spectrums CSV file
        df.to_csv(spectrums_csv, index=False)
        print(f"Spectrums data overwritten to {spectrums_csv} with {len(df)} rows and {len(df.columns)} columns - old spectrums was {len(old_specs_df)} rows and {len(old_specs_df.columns)} columns.")
    else:
        print('Discarding new spectrums data, keeping original spectrums entries.')
        return
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
def recreate_fully():
    """fully recreates all spectrums"""
    df = full_spectrums()
    write_spectrums(df)
    list = spectrum_list()
    for i, spectrum_id in enumerate(list):
        construct_bretschneider(spectrum_id)
    calculate_all('energy')
    calculate_sim_incidentspectrumtype()
def main():
    #calculate_all('energy')
    #calculate_sim_incidentspectrumtype()
    spec_list = spectrum_list()
    for spec in spec_list:
        construct_bretschneider_min(spec)

    #print('It appears you are running spectrums.py directly. This module is intended to be imported and used by other scripts.')

if __name__ == '__main__':
    main()