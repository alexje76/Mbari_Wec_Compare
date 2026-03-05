# Mbari_Wec_Compare
A data pipeline to handle all simulation and experimental runs of the MBARI WEC controlls project

## File Directory
batch_import.py: Module that handles all steps to adding to the mainDF when given a batch file
batch_writing.py: Script to generate output to be used in batch files - such as period and amplitude for regular waves
datalog.csv: CSV that contains the batch upload and timestamps of data uploaded to mainDF - for tracing purposes
mainDF_management.py: Module that handles the mainDF - compartmentalizes access, writing, ect.
mbari_data_processing.py: Script to handle sequential chunks of the data processing pipeline at once - currently unused.
run_analytics.py: Script to process data from raw - calculating scalar values and currently some visualization (to be phased out)
testing.py: Script acting as a temporary testing ground for in development code when direct testing would carry undue risk
visualization.py: Module to visualize different graphs and metrics 
spectrums.py: Module to handle the spectrums
spectrums.csv: CSV file tha stores all of the spectrums

## Contributing
Alex Eagan

# License
GNU AFFERO GENERAL PUBLIC LICENSE