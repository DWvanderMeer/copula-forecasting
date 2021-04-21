'''
Some observations:
- Only the first two ensemble members go all the way to the 67th forecast horizon.
- Now there are 30 ensemble members. In 2019 there were 10 and GHI often only has 1.
- The deadline for Nord Pool is 12:00 CET, so we require forecasts t+k where
  k \in {12, 14, ..., 36}.
- I could store the data as greenlytics do: everything in one dataframe where the
  first column is the reference datetime and the second column the forecast valid
  time. --> This is done now.
  Make sure the reference time is indeed correct. Verify with Greenlytics--> Fixed
  now with datetime.datetime.utcfromtimestamp(ref_time).
- Check https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.interp2d.html
  for 2D interpolation.
'''

import netCDF4 # Requires v1.3.1 (pip3 install netCDF4==1.3.1). Newer throws error 68
import pyproj
import numpy as np
import datetime
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Helpful link from metno: https://github.com/metno/NWPdocs/wiki/Python

PATH_TEMP = "~/Desktop/temperature"
PATH_WIND = "~/Desktop/wind"
PATH_GHI = "~/Desktop/ghi"
PATH = "~/Desktop"

start = 12 # Lead time of the forecast from 12Z.
end = 36 # End of the forecast period from 12Z.

year = 2019
month = 6
day = 1
# Filename as url:
#filename = "https://thredds.met.no/thredds/dodsC/mepslatest/meps_lagged_6_h_latest_2_5km_latest.nc"
#filename = "https://thredds.met.no/thredds/dodsC/meps25epsarchive/2019/06/01/meps_subset_2_5km_20190601T12Z.nc"
filename = "https://thredds.met.no/thredds/dodsC/meps25epsarchive/" + str(year) + "/" + '{:02d}'.format(month) + "/" + '{:02d}'.format(day) + "/meps_subset_2_5km_" + str(year) + '{:02d}'.format(month) + '{:02d}'.format(day) +"T12Z.nc"
file = netCDF4.Dataset(filename,"r")

ref_time = file.variables["forecast_reference_time"][:]
ref_time = pd.to_datetime(datetime.datetime.utcfromtimestamp(ref_time), utc=True) # .tz_convert('Europe/Stockholm')
ref_times = [ref_time]*(end-start)
df_ref_times = pd.DataFrame(data=ref_times,columns=['ref_time'])

# Uppsala coordinates
lat = 59.853079
lon = 17.623989
# Varberg coordinates
lat = 57.035807
lon = 12.379479
proj = pyproj.Proj(file.variables["projection_lambert"].proj4)

# Compute projected coordinates of lat/lon point
X,Y = proj(lon,lat)

# Find nearest neighbour
x = file.variables["x"][:]
y = file.variables["y"][:]

Ix = np.argmin(np.abs(x - X))
Iy = np.argmin(np.abs(y - Y))

# Forecast valid times:
valid_time = file.variables["time"][start:end]
valid_time = np.vstack([pd.to_datetime(datetime.datetime.utcfromtimestamp(np.asarray(i)), utc=True) for i in valid_time]) # .tz_convert('Europe/Stockholm')
df_valid_time = pd.DataFrame(data=valid_time,columns=['valid_time'])

# Temperature:
temperatures = file.variables["air_temperature_2m"][start:end,0,:,Iy,Ix] - 273.15 # K to C
#df_temp = pd.DataFrame(data=temperatures,index=times).round(2)
df_temp = pd.DataFrame(data=temperatures,columns=['temp_'+str(i) for i in range(temperatures.shape[1])]).round(2)
#fname = os.path.join(PATH_TEMP, fc_ref_time.strftime("%Y%m%dT%H%M")+".txt")
#df.to_csv(fname, sep="\t")

# Wind:
x_wind = file.variables["x_wind_10m"][start:end,0,:,Iy,Ix]
y_wind = file.variables["y_wind_10m"][start:end,0,:,Iy,Ix]
wind_speed = np.sqrt(x_wind**2 + y_wind**2)
#df_wind = pd.DataFrame(data=wind_speed,index=times).round(2)
df_wind = pd.DataFrame(data=wind_speed,columns=['wind_'+str(i) for i in range(wind_speed.shape[1])]).round(2)
#print(df.head())
#fname = os.path.join(PATH_WIND, fc_ref_time.strftime("%Y%m%dT%H%M")+".txt")
#df.to_csv(fname, sep="\t")

# GHI (units: Ws/m2):
ghi_accumulated = file.variables['integral_of_surface_downwelling_shortwave_flux_in_air_wrt_time'][:,0,:,Iy,Ix] / 3600
ghi = np.diff(ghi_accumulated,axis=0,prepend=0) # Prepend with 0 because it is the integral of shortwave flux.
ghi = ghi[start:end,:] # Select the forecast period.
#df_ghi = pd.DataFrame(data=ghi,index=times).round(2)
df_ghi = pd.DataFrame(data=ghi,columns=['ghi_'+str(i) for i in range(ghi.shape[1])]).round(2)
#print(df.head())
#fname = os.path.join(PATH_GHI, fc_ref_time.strftime("%Y%m%dT%H%M")+".txt")
#df.to_csv(fname, sep="\t")

df = pd.concat([df_ref_times,df_valid_time,df_temp,df_wind,df_ghi],axis=1)
# print(df.head())
fname = os.path.join(PATH, "meps.txt")
df.to_csv(fname, sep="\t")
