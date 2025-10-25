import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob

data = [
    ['Alice', 25, 'New York'],
    ['Bob', 30, 'London'],
    ['Charlie', 35, 'here']
]
columns = ['Name', 'Age', 'City']
df = pd.DataFrame(data, columns=columns)
print(df)

df['trim'] = None
df.at[2, 'trim'] = 5  # Set trim value for Charlie

print(df.iloc[1:])  # Accessing Charlie's city