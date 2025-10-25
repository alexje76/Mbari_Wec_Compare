import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob

data = [
    ['Alice', 25, 'New York'],
    ['Bob', 30, 'London'],
    ['Charlie', 35]
]
columns = ['Name', 'Age', 'City']
df = pd.DataFrame(data, columns=columns)
print(df)

print(df.iloc[2, 2])  # Accessing Charlie's city