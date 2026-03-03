"""
Controller_functions
Functions that are primarily written for use with a controller
"""
import numpy as np
import mainDF_management as mDF_mgmt

def opt_emp_damp(amps, periods):
    """
    Docstring for opt_emp_damp
    returns the optimal empirical damping value
    Hardcoded damping batches
    """
    batches = 'batch_results_20260130133904' #'batch_results_20260130133904 is 0.9-1.3 damping range with spotter periods
    print(sum(amps))

    #Access the data
    mainDF = mDF_mgmt.access_mainDF() 
    #get mainDF indices from batch name
    data = mainDF[mainDF['batch_file_name'] == batches].copy()
    #gather A,T 
    data[['A', 'T']] = data[' IncWaveSpectrumType;IncWaveSpectrumParams'].str.extract(r'A:([0-9.]+);T:([0-9.]+)') #capture A,T all after that have a 0-9 or .
    data[['A', 'T']] = data[['A', 'T']].astype(float)

    
    #subset into each damping value
    damping = data[' ScaleFactor'].unique()
    damp_pwr_sgl = np.zeros(len(damping))
    damp_pwr_mul = np.zeros((len(damping), len(amps)))#code to have the averaged damp per freq, eg could be 1.345 damping value
    print(f"Finding opt_damp for damping values {min(damping)} to {max(damping)} \n From batches {batches}")
    
    for i, damp in enumerate(damping):
            damp_data = data[data[' ScaleFactor'] == damp]
            damp_pwr_sgl[i] = 0
            for j, amp in enumerate(amps):

                 same_per = damp_data[np.isclose(damp_data['T'], periods[j], atol=1e-4)] #find the period examples for each damping, here need isclose due to float precision
                 ##print(same_per[['A', 'avg_tot_power', 'T']])
                 if amp in same_per['A'].values:
                    pwr = same_per.loc[same_per['A'] == amp, 'avg_tot_power'].values[0]
                 else:
                 #interpolate if not found #TODO find the best interpolation technique
                    #sorted_amps = same_per.sort_values('A') #this appears to not be needed - same_per already sorted from least to most amplitude
                    ##print(sorted_amps)
                    #if amp < sorted_amps['A'].iloc[0] or amp > sorted_amps['A'].iloc[-1]:
                    #    print('Amplitude is out of bounds, using clamping')
                    ##print(f"i is {i}, j is {j}")
                    ##print(periods[j])
                    pwr = np.interp(amp, same_per['A'], same_per['avg_tot_power'])
                 damp_pwr_sgl[i] = damp_pwr_sgl[i] + pwr #add the damping power for this amplitude, period
                 damp_pwr_mul[i,j] = pwr
            ##print(f"amps, {amps}")

    max_idx = np.argmax(damp_pwr_sgl)
    #TODO: Here I could use damp_pwr_mul in theory to calculate a damping value that is best. 
    #print(damp_pwr_mul)

    print(f"\nDamping maximum singular {damping[max_idx]}, damping maximum currently not calculated:\nHere is the damp powers {damp_pwr_sgl}\n")

    return damping[max_idx]

def amp_transform (amps, szz):
    print(f"OG Amps: {amps}")
    amps_new = np.zeros(len(amps))
    for i, amp in enumerate(amps):
        if i < 2:
            # If we're at the beginning, use a simple transformation
            amps_new[i] = amps[i] * 5  # Transform by a factor of 5
        elif i >= len(amps) - 2:
            # If we're at the end, use simple transformation
            amps_new[i] = amps[i] * 5
        else:
            # If we're in the middle, use a sliding window of 5 elements
            amps_new[i] = sum(amps[i-2:i+3])
    amps_new = amps_new*3.5 #Scale up - hyperparameter
    print(f"Transformed amps: {amps_new}")
    return amps_new

##################TESTING##################
def main():
    print('Nothing in Controller Functions  main body just yet')

    
##################DONE TESTING##################

if __name__ == '__main__':
    main()