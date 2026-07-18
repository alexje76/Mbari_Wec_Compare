# Mbari_Wec_Compare
A data pipeline to handle all simulation and experimental runs of the MBARI WEC controlls project

## Folders
- [X]MbariSandiaDamping: Folder that contains the MbariSandiaDamping data from MBARI. 6/30/26
- [] runFeathers: 6/30/26
- [] tests: File for tests to make sure code doesn't break - barely used for now. 6/30/26 

## File Directory
- [X] batch_import.py: Module that handles all steps to adding to the mainDF when given a batch file. 6/30/26
- [X] batch_writing.py: Script to generate output to be used in batch files - such as period and amplitude for regular waves. 6/30/26
- [X] datalog.csv: CSV that contains the batch upload and timestamps of data uploaded to mainDF - for tracing purposes. 6/30/26
- [X] mainDF_management.py: Module that handles the mainDF - compartmentalizes access, writing, ect. 6/30/26
- [ ] mbari_data_processing.py: Script to handle sequential chunks of the data processing pipeline at once - currently unused. 6/30/26
- [X] run_analytics.py: Script to process data from raw - calculating scalar values and currently some visualization (to be phased out)
- [ ] testing.py: Script acting as a temporary testing ground for in development code when direct testing would carry undue risk - Currently not often used. 6/30/26
- [X] visualization.py: Module to visualize different graphs and metrics 
- [X] spectrums.py: Module to handle the spectrums
- [X] spectrums.csv: CSV file tha stores all of the spectrums

## Contributing
Alex Eagan

# License
GNU AFFERO GENERAL PUBLIC LICENSE