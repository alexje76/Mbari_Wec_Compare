###
#TODO: add in delete_mainDF

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob

def write_mainDF(df: pd.DataFrame):
    """Write the provided DataFrame to CSV."""
    mainDF_csv = 'mainDF.csv'  # Path to your main DataFrame CSV file
    df.to_csv(mainDF_csv, index=False)
    print(f"mainDF written to {mainDF_csv} with {len(df)} rows and {len(df.columns)} columns.")


def access_mainDF() -> pd.DataFrame:
    """Return the main DataFrame (read from CSV if present, otherwise create empty DataFrame)."""
    mainDF_csv = 'mainDF.csv'  # Path to your main DataFrame CSV file
    if os.path.exists(mainDF_csv):
        df = pd.read_csv(mainDF_csv)
        print(f"mainDF loaded with {len(df)} rows and {len(df.columns)} columns.")
    else:
        df = pd.DataFrame()
        print("mainDF does not exist. Created new empty DataFrame.*****************")
    return df