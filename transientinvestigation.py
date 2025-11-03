import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import glob

import mainDF_management as mDF_mgmt    

transient = pd.read_csv('transient.csv')
#print(transient)



x = transient['i']
y = transient['avg_power']

x = x[2:]
y = y[2:]

    
    #Plot the data
plt.figure(figsize=(10, 6))
plt.title(f"Data Plot for 500s Transient test .5A 8T: power vs trim")

plt.scatter(x, y)
   # plt.xscale('log') #for physics step
plt.xlabel('trim(periods)')
plt.ylabel('power')
plt.grid()
plt.show()