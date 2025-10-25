##########
# run_analytics.py
# A module of functions that perform analytics on the run passed into the function. 
# TODO parse in run data


######## POWER FUNCCTIONS ##########
def avg_tot_power(trimmed_data):
    #Calculate average total power from a run
    
    if not np.isscalar(avg_total_power): raise TypeError(f"avg_total_power must be a scalar number, got {type(avg_total_power).name}")


######## END POWER FUNCTIONS #############################

def trim(data, trim_amount):
    """
    Trim the data by the specified amount from start and end
    """
    start_time = data['Timestamp (epoch seconds)'].iloc[0]
    trim_start_time = start_time + trim_amount

    trim_idx_start = data.index[data['Timestamp (epoch seconds)'] >= trim_start_time][0]

    return data.iloc[trim_idx_start:]


def get_data(): #deciding how to access data - batchname and run number, mainDF index, pblogname (closest to run name) ##probably use kwargs
    """
    Accessing the data using the mainDF path
    """
    

##################TESTING##################
def main():
    
##################DONE TESTING##################

if __name__ == '__main__':
    main()