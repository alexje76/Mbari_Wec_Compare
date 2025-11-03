import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob
pblog_name = "2025.10.06T11.20.26.csv"
run_data_path = glob.glob(f"TestingData/**/{pblog_name}", recursive=True)
if run_data_path:
    # print the first match (full relative path)
    run_data_path = run_data_path[0]
else:
    raise FileNotFoundError(f"{pblog_name} not found under TestingData")

print("--------------")
# search recursively under TestingData for the pblog file name
matches = glob.glob(os.path.join('TestingData', '**', pblog_name), recursive=True)
if matches:
	# print the first match (full relative path)
	print(matches[0])
else:
	print(f"{pblog_name} not found under TestingData")

St = np.array[]