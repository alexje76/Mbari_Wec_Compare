import math

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
    import numpy as np

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
def main():
     _134Error_Testing(0.5, 14, 0.5, 0.5)

if __name__ == '__main__':
    main()