"""
Module that handles plotting for multiple spectrum. 

get_MBARI_2022: Gets all spectrum from MBARI 2022 data IDs
get_MBARI_2023: Gets all spectrum from MBARI 2023 data IDs
get_damping_swept_data: Gets the spectrums that have been run with a swept damping ratio
get_all_data: Gets all the data
plot_hs_tp: Plots the spectra with Hs and Tp
"""
import spectrums.py
import pandas as pd
import numpy as np
########################################Start Spectrum Gathering#################################################
def get_all_data ():
    df = spectrums.read_spectrums()
    return df
########################################End Spectrum Gathering#################################################

def plot_hs_tp ():
    """
    Plots the spectra as a function of Hs and Tp

    ----------------
    Parameters:
        Year: Which years are gathered if not all

    ----------------
    Returns:
    """

