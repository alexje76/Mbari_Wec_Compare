import numpy as np
import math
import visualization
import controller_funcs
import spectrums

""" def sub():
        for i in range(75, 166, 15):
            print(i*.01, end=", ")

        print(' ')
        for i in range(75, 166, 15):
            print(5, end=", ")

g = 9.81
max = 5 #meters - for monterey bay based on recorded statistical wave height of 35 ft
d = 70 #meters
for i in range(4, 40, 1):
    i=i/2
    print(i, end="")
    print(', ', end="")
    print(i, end="")
    print(', ', end="")
    print(i, end="")
    print(', ', end="")

print(' ')
for i in range(4, 40, 1):
    i=i/2
    wavelength = (i ** 2)*g/(2*math.pi)

    # if d/wavelength > 0.5: #add in the deep water correction #TODO improve this approximation
    #     wavelength = wavelength * math.tanh(2*math.pi*d/wavelength)
    #     print('k = ', 2*math.pi/wavelength)
    #     wavelength = wavelength * math.tanh(2*math.pi*d/wavelength)
    #     wavelength = wavelength * math.tanh(2*math.pi*d/wavelength)
    #     print(wavelength, 'iterated')
        
    div = 1
    while round(wavelength* .142/div, 3)>max: #wavelength*.071 - adjusting to output amplitude instead of height
        div= div+1

    print(round(wavelength* .142/div, 3),', ', end="", sep='')
    print(round(wavelength* .142/(div*2), 3),', ', end="", sep='')
    print(round(wavelength* .142/(div*4), 3),', ', end="", sep='')
print('')

sub() """

def _134Error_Testing(tmin, tmax, t_delta, grid_size_y):
    # 1. Validation Logic
    if tmin >= tmax:
        raise ValueError("tmin must be less than tmax.")

    # 2. Check if the range crosses the 28s threshold
    if tmin < 28 and tmax > 28:
        # Segment 1: tmin to 28 (exclusive) with t_delta
        T1 = np.arange(tmin, 28, t_delta)
        # Segment 2: 28 to tmax with 2 * t_delta
        T2 = np.arange(28, tmax, 2 * t_delta)
        T = np.concatenate([T1, T2])
    else:
        # If the range doesn't cross 28, use standard single-step logic
        # (e.g., if everything is < 28, use t_delta; if everything is > 28, use 2*t_delta)
        step = t_delta if tmax <= 28 else 2 * t_delta
        T = np.arange(tmin, tmax, step)

    d = 80 #meters
    g = 9.81

    max_amp = np.minimum(5, (T**2 *0.22)/2) #height
    print(max_amp, 'max amp')

    
    max_rows = int(np.max(max_amp) / grid_size_y) + 1
    # 2. Initialize the matrix with NaN values
    A = np.full((max_rows, len(T)), np.nan)
    A[0, :] = T  # Set the first row to T values

    # 3. Fill the matrix column by column
    for i, t_val in enumerate(T):
        # Generate the sequence for this column
        column_vals = np.arange(grid_size_y, max_amp[i], grid_size_y)
        
        # Add the max_amp value at the top (or bottom)
        all_vals = np.concatenate([[max_amp[i]], column_vals])

        # Insert into the matrix (filling only the available height for this T)
        A[1:1+len(all_vals), i] = all_vals
   # with np.printoptions(threshold=np.inf):
    print(A)

        # --- STRING GENERATION START ---
    t_repeated_list = []
    row_values_list = []

    # Iterate column by column
    for i in range(len(T)):
        t_val = A[0, i]
        # Get all data below the T header for this column, excluding NaNs
        column_data = A[1:, i]
        valid_data = column_data[~np.isnan(column_data)]
        
        for val in valid_data:
            t_repeated_list.append(str(t_val))
            row_values_list.append(str(val))

    print(len(t_repeated_list), len(row_values_list))
    # 1) T values repeated for every row entry below them
    # Wrap the joined strings in brackets
    string_1 = f"[{', '.join(t_repeated_list)}]"
    string_2 = f"[{', '.join(row_values_list)}]"
    # --- STRING GENERATION END ---

    print("String 1 (Repeated T):", string_1)
    print("String 2 (Row Values):", string_2)
def CustomSpectrumMultiplier(f, Szz, multiplier, **kwargs):
    """
    f = frequency array
    Szz = spectral density array
    multiplier = value to multiply Szz by
    kwargs:
        frequency_alteration: if not None, multiply f by multiplier as well #this is likely never going to be used but added it anyways
    """
    if kwargs["frequency_alteration"] is not None:
        f_new = [item * multiplier for item in f]
    else:
        f_new = f
    Szz_new = [item * multiplier for item in Szz]
    return (f_new, Szz_new)

def print_custom_spectrum(f, Szz):
    print(" - Custom: \n" \
    "     f: " + str(f) + "\n" \
    "     Szz: " + str(Szz) + "\n")

def spectrum114():
    fMbari2022_114= [0.0293, 0.03906, 0.04883, 0.05859, 0.06836, 0.07813, 0.08789, 0.09766, 0.10742, 0.11719, 0.12695, 0.13672, 0.14648, 0.15625, 0.16602, 0.17578, 0.18555, 0.19531, 0.20508, 0.21484, 0.22461, 0.23438, 0.24414, 0.25391, 0.26367, 0.27344, 0.2832, 0.29297, 0.30273, 0.3125, 0.32227, 0.33203, 0.35156, 0.38086, 0.41016, 0.43945, 0.46875, 0.49805, 0.6543]
    SzzMbari2022_114 = [0.001000448, 0.005751808, 0.051762176, 0.377341952, 0.526379008, 0.36083814399999997, 0.161289216, 0.15978905599999998, 0.38759424, 0.515625984, 0.7389306880000001, 0.7264276479999999, 0.701170688, 0.5663887360000001, 0.441107456, 0.35608678400000005, 0.265064448, 0.25006079999999997, 0.2015488, 0.17079193599999998, 0.15328767999999998, 0.12127948799999999, 0.14303539199999998, 0.14278451200000003, 0.117778432, 0.10852659199999999, 0.10377523200000001, 0.088020992, 0.060264448000000005, 0.050762752, 0.043760639999999996, 0.040509439999999994, 0.043010047999999995, 0.029256703999999998, 0.023005184, 0.020504576, 0.014003199999999999, 0.00950272, 0.0055009279999999995]
    return (fMbari2022_114, SzzMbari2022_114)
def spectrum198():
    fMbari2022_198 = [0.0293, 0.03906, 0.04883, 0.05859, 0.06836, 0.07813, 0.08789, 0.09766, 0.10742, 0.11719, 0.12695, 0.13672, 0.14648, 0.15625, 0.16602, 0.17578, 0.18555, 0.19531, 0.20508, 0.21484, 0.22461, 0.23438, 0.24414, 0.25391, 0.26367, 0.27344, 0.2832, 0.29297, 0.30273, 0.3125, 0.32227, 0.33203, 0.35156, 0.38086, 0.41016, 0.43945, 0.46875, 0.49805, 0.6543]
    SzzMbari2022_198= [0.0014991359999999999, 0.0037509120000000003, 0.081770496, 1.14402816, 1.522870272, 1.148531712, 2.14777344, 1.7869363200000001, 1.029252096, 0.523628544, 0.297071616, 0.181542912, 0.16278835200000003, 0.147035136, 0.086270976, 0.06601728, 0.05326233599999999, 0.055514112000000004, 0.052512768, 0.034507776, 0.024757248, 0.01875456, 0.01425408, 0.012002304, 0.011252736000000001, 0.010503168, 0.010503168, 0.011252736000000001, 0.010503168, 0.007501824000000001, 0.008251392, 0.006752255999999999, 0.007501824000000001, 0.006002688, 0.005250047999999999, 0.004500479999999999, 0.006002688, 0.007501824000000001, 0.003001344]
    return (fMbari2022_198, SzzMbari2022_198)
def spectrum260():
    fMbari2022_260 = [0.0293, 0.03906, 0.04883, 0.05859, 0.06836, 0.07813, 0.08789, 0.09766, 0.10742, 0.11719, 0.12695, 0.13672, 0.14648, 0.15625, 0.16602, 0.17578, 0.18555, 0.19531, 0.20508, 0.21484, 0.22461, 0.23438, 0.24414, 0.25391, 0.26367, 0.27344, 0.2832, 0.29297, 0.30273, 0.3125, 0.32227, 0.33203, 0.35156, 0.38086, 0.41016, 0.43945, 0.46875, 0.49805, 0.6543]
    SzzMbari2022_260 = [0.000499712, 0.001501184, 0.013002752, 0.060514304000000005, 0.11602739200000001, 0.164040704, 0.146536448, 0.18254438400000003, 0.432105472, 1.2172963840000002, 1.8024407040000001, 1.607892992, 1.2373012479999999, 0.7911935999999999, 0.49762099200000004, 0.40459878400000004, 0.33708236799999997, 0.298072064, 0.23705804800000002, 0.20755046400000002, 0.166541312, 0.168040448, 0.1530368, 0.13303193600000002, 0.096524288, 0.07551795199999999, 0.06151577600000001, 0.06351462399999999, 0.054513663999999996, 0.045510656, 0.033507328, 0.027506688, 0.027006976000000002, 0.017504256000000003, 0.012503040000000002, 0.010002432, 0.008501248, 0.006502399999999999, 0.002000896]
    return (fMbari2022_260, SzzMbari2022_260)
def spectrum384():
    fMbari2022_532 = [0.0293, 0.03906, 0.04883, 0.05859, 0.06836, 0.07813, 0.08789, 0.09766, 0.10742, 0.11719, 0.12695, 0.13672, 0.14648, 0.15625, 0.16602, 0.17578, 0.18555, 0.19531, 0.20508, 0.21484, 0.22461, 0.23438, 0.24414, 0.25391, 0.26367, 0.27344, 0.2832, 0.29297, 0.30273, 0.3125, 0.32227, 0.33203, 0.35156, 0.38086, 0.41016, 0.43945, 0.46875, 0.49805, 0.6543]
    SzzMbari2022_532 = [0.000750592, 0.001250304, 0.002250752, 0.011252736000000001, 0.067766272, 0.07551795199999999, 0.125280256, 0.466363392, 0.8597094399999999, 0.616650752, 0.421853184, 0.42335334399999996, 0.37209088, 0.23730790400000001, 0.16403968, 0.117778432, 0.08477081599999998, 0.061514752, 0.06451609600000001, 0.06751641600000001, 0.067016704, 0.06351564800000001, 0.055763968000000004, 0.04701184, 0.048011264, 0.043760639999999996, 0.03275776, 0.02175488, 0.018254847999999997, 0.016753664, 0.019505151999999998, 0.01550336, 0.012752896000000001, 0.011252736000000001, 0.008502271999999998, 0.0060016639999999994, 0.005751808, 0.004000768, 0.002000896]
    return (fMbari2022_532, SzzMbari2022_532)
def spectrum532():
    fMbari2022_532= [0.0293, 0.03906, 0.04883, 0.05859, 0.06836, 0.07813, 0.08789, 0.09766, 0.10742, 0.11719, 0.12695, 0.13672, 0.14648, 0.15625, 0.16602, 0.17578, 0.18555, 0.19531, 0.20508, 0.21484, 0.22461, 0.23438, 0.24414, 0.25391, 0.26367, 0.27344, 0.2832, 0.29297, 0.30273, 0.3125, 0.32227, 0.33203, 0.35156, 0.38086, 0.41016, 0.43945, 0.46875, 0.49805, 0.6543]
    SzzMbari2022_532 = [0.013004799999999999, 0.020004864, 0.020004864, 0.024006655999999998, 0.042008576, 0.24105779200000002, 1.8884608, 3.6628930559999997, 2.2885580799999996, 1.292316672, 0.9062195200000001, 0.622153728, 0.45911244799999995, 0.487120896, 0.5431336959999999, 0.699170816, 0.893218816, 1.1982929919999998, 1.3803356160000002, 1.1332771840000002, 0.86921216, 0.5551349760000001, 0.49912217600000003, 0.428105728, 0.318078976, 0.28006809600000004, 0.251060224, 0.25406259200000003, 0.214052864, 0.174043136, 0.13503283200000002, 0.10202316800000001, 0.089022464, 0.067014656, 0.048013311999999995, 0.027004928, 0.027004928, 0.021004288, 0.007000064]
    return (fMbari2022_532, SzzMbari2022_532)
def spectrum597():
    fMbari2022_597 = [0.0293, 0.03906, 0.04883, 0.05859, 0.06836, 0.07813, 0.08789, 0.09766, 0.10742, 0.11719, 0.12695, 0.13672, 0.14648, 0.15625, 0.16602, 0.17578, 0.18555, 0.19531, 0.20508, 0.21484, 0.22461, 0.23438, 0.24414, 0.25391, 0.26367, 0.27344, 0.2832, 0.29297, 0.30273, 0.3125, 0.32227, 0.33203, 0.35156, 0.38086, 0.41016, 0.43945, 0.46875, 0.49805, 0.6543]
    SzzMbari2022_597 = [0.002500608, 0.007501824, 0.054513663999999996, 0.19004620800000002, 0.954732544, 1.0617589760000001, 0.29857382400000004, 0.401098752, 0.488118272, 0.615651328, 0.6571601920000001, 0.560635904, 0.401098752, 0.33458175999999995, 0.25356288, 0.22505472, 0.17504255999999999, 0.16103833599999998, 0.188045312, 0.16053862400000002, 0.11152793600000001, 0.098023424, 0.085020672, 0.082520064, 0.07201792, 0.054513663999999996, 0.045510656, 0.034508800000000006, 0.032008192000000005, 0.029007872, 0.026507264, 0.020004864, 0.020004864, 0.012003327999999999, 0.00950272, 0.008501248, 0.0055009279999999995, 0.004001792, 0.001501184]
    return(fMbari2022_597, SzzMbari2022_597)

def szz2amp(f, szz):
    """
    Docstring for szz2amp
    Takes the f and szz from the spotter buoy and uses a hardcoded df to re-create amplitudes
    #TODO dynamically code the df values
    returns amps
    """
    df =np.array([ 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.00977, 0.0293, 0.0293, 0.0293, 0.0293, 0.0293, 0.0293, 0.2832 ])
    f = np.array(f)
    szz = np.array(szz)

    amps = np.zeros(len(f))
    print(amps)
    for i, fx in enumerate(f):
        amps[i] = np.sqrt(2*szz[i]*df[i])
    return amps

def _134_custom_spectrums():
    f, Szz = spectrum114()
    for i in range(1, 5):
        f_mult, Szz_mult = CustomSpectrumMultiplier(f, Szz, i, frequency_alteration=None)
        print_custom_spectrum(f_mult, Szz_mult)
    f, Szz = spectrum198()
    for i in range(1, 5):
        f_mult, Szz_mult = CustomSpectrumMultiplier(f, Szz, i, frequency_alteration=None)
        print_custom_spectrum(f_mult, Szz_mult)
    f, Szz = spectrum532()
    for i in range(1, 5):
        f_mult, Szz_mult = CustomSpectrumMultiplier(f, Szz, i, frequency_alteration=None)
        print_custom_spectrum(f_mult, Szz_mult)

def damping_ranges_spotter(grid_size_y, largest_amp):
    """
    Given the sampling range of the spotter buoys, calculate the damping map
    largest_amp gives the max amplitude for any period

    """
    f, szz = spectrum114() #1: gather periods
    T = 1/np.array(f)

    d = 80 #2: Set constants 
    g = 9.81

    max_amp = np.minimum(largest_amp, (T**2 *0.22)/2).round(4) #3: find maximum amplitude, and create matrix
    max_rows = int(np.max(max_amp) / grid_size_y) + 1
    
    A = np.full((max_rows, len(T)), np.nan) # 4: Initialize the matrix with NaN values
    A[0, :] = T  # Set the first row to T values

    for i, t_val in enumerate(T): #Fill the matrix col by col
        # Generate the sequence for this column
        column_vals = np.arange(grid_size_y, max_amp[i], grid_size_y)
        div = 1
        while len(column_vals) < min(4, max_rows):
            div = div+1
            column_vals = np.linspace(grid_size_y/div, max_amp[i], div+1, endpoint=False).round(4)

        
        # Add the max_amp value at the top (or bottom)
        all_vals = np.concatenate([column_vals, [max_amp[i]]])

        # Insert into the matrix (filling only the available height for this T)
        A[1:1+len(all_vals), i] = all_vals

    #print(A)

        #5: --- STRING GENERATION START ---
    t_repeated_list = []
    row_values_list = []

    # Iterate column by column
    for i in range(len(T)):
        t_val = A[0, i]
        # Get all data below the T header for this column, excluding NaNs
        column_data = A[1:, i]
        valid_data = column_data[~np.isnan(column_data)]
        
        for val in valid_data:
            t_repeated_list.append(str(t_val))
            row_values_list.append(str(val))

    t_repeated_list = np.array(t_repeated_list)
    print(type(t_repeated_list))
    t_repeated_list = (t_repeated_list.astype(float).round(4)).astype(str)

    print(len(t_repeated_list), len(row_values_list))
    # 1) T values repeated for every row entry below them
    # Wrap the joined strings in brackets
    string_1 = f"[{', '.join(t_repeated_list)}]"
    string_2 = f"[{', '.join(row_values_list)}]"
    # --- STRING GENERATION END ---

   
    print("     A:", string_2)
    print("     T:", string_1)

def custom_damping(f, szz):
    """
    Docstring for custom_damping
    Takes the f and szz, and gathers the amplitudes, then maps the amp, period pairs onto each damping value in test set, and returns the damping value that would generate the highest energy.
    """
    f = np.array(f)
    T = 1/f
    amps = szz2amp(f,szz)

    amps = controller_funcs.amp_transform(amps, szz)
    custom_damping = controller_funcs.opt_emp_damp(amps, T)

    print(f"Scale Factor: [{custom_damping}]")
    print_custom_spectrum(f, szz)
def seeds(start, end):
    seeds = np.arange(start, end+1, 1)
    print(f"seed: {seeds.tolist()}")
def damping(start, end, step):
    damp_vals = np.arange(start, end+step, step).round(3)
    print(f"scale_factor: {damp_vals.tolist()}")
def main():
    # _134Error_Testing(0.5, 14, 0.5, 0.5)
    #_134_custom_spectrums()
    # ###
    #damping_ranges_spotter(0.5, 3)
    # seeds(1,20)
    # damping(0.5, 1.4, 0.1)
    # f, szz = spectrum198()
    # print_custom_spectrum(f,szz)
    ###
    spectrum_nums = spectrums.spectrum_list()
    visualization.plot_overlayed_spectrums(spectrum_nums, plots_per_page=6, period=False, types=['spotter', 'bretschneider'], n_cols=2, metric_sv='energy', cumsum=True)
    ###



if __name__ == '__main__': 
    main()