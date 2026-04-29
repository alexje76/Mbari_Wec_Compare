import xarray as xr
ds = xr.open_dataset('MbariSandiaDamping\damping_schedule.nc')
df = ds.to_dataframe()
df.to_csv('MbariSandiaDamping\damping_schedule.csv', index=False)