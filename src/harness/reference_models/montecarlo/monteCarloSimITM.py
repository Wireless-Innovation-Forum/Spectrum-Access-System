#    Copyright 2017 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# this function runs the Monte Carlo aggregation Simulation and computes the
# distribution of the aggregate received power.
# The transmitter CBSD profile is omni 
# For the power computation, the Receiver is assumed to be flat 0dB over
# the band and hence the Rx Power is simply equal to (Transmit power-PL)
# Inputs:
# device structure contains following fields:
    #     txEIRP
    #     AntHtMeters
    #     cntrFreq
    #     Location Longitude (Lon)
    #     Location Latitude (Lat)
# This can be relaxed easily if need be.
# rx structure contains following fields:
    #     Lat,lon
    #     AntHtMeters

# Outputs:
# mc50thp - 50th percentile of teh aggregate monte carlo power
# mc95thp - 95th percentile of teh aggregate monte carlo power

# Mayowa Aregbesola, Ananth Kalenahalli, Sep 2017

import os,sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from reference_models.geo import tropoclim
from reference_models.geo import refractivity
from reference_models.geo import terrain
from reference_models.geo import vincenty
from reference_models.propagation.itm import itm


# Initialize tropoclim and refractivity drivers
climateDriver = tropoclim.ClimateIndexer()
refractDriver = refractivity.RefractivityIndexer()

def ConfigureItuDrivers(itu_dir=None):
    """Configure the ITU climate and refractivity drivers."""
    if itu_dir is not None:
        climateDriver.ConfigureDataFile(itu_dir)
        refractDriver.ConfigureDataFile(itu_dir)


# Initialize terrain driver
terrainDriver = terrain.TerrainDriver()
def ConfigureTerrainDriver(terrain_dir=None, cache_size=None):
    """Configure the NED terrain driver.

      Note that memory usage is about cache_size * 50MB.
    
      Inputs:
        terrain_dir: if specified, change the terrain directory.
        cache_size:  if specified, change the terrain tile cache size.
      """
    if terrain_dir is not None:
        terrainDriver.SetTerrainDirectory(terrain_dir)
    if cache_size is not None:
        terrainDriver.SetCacheSize(cache_size)
  
def aggregate(rx, devices, N = 2000, res = 0.001):

    numdevice= 0;
    sampAggregateRxPowLin =  np.zeros(N)
    sampMedian_all_distributions_dBm =  np.zeros(N)
    
    #error check
    # resolution should not cause sample space to be more than N
    if (1/res) > N :
        print 'The resolution %f is too small using %f' % (res, 2./N)
        res = 2/N;
    

    # resolution should be less than 1
    if res > 1 :
        print 'The resolution %f should be greater than 1 using 0.001' % res
        res = 0.001;
          
    for device in devices:        
        # generate the reliability vector that we want to sweep in order to
        # generate the distribution for this CBSD if non is provided
        if 'reliabilities' not in device:
            setreliabilities =  np.arange(0.001, 1, res)
            reliabilitiesidx = np.random.choice(len(setreliabilities), N)
            reliabilities = setreliabilities[reliabilitiesidx];
        else:
            reliabilities = device['reliabilities']


        # Internal ITM parameters are always set to following values in WF version:
        confidence = 0.5     # Confidence (always 0.5)
        dielec = 25.         # Dielectric constant (always 25.)
        conductivity = 0.02  # Conductivity (always 0.02)
        polarization = 1     # Polarization (always vertical = 1)
        mdvar = 13
        refractivity_final=False
                
        # Find the midpoint of the great circle path
        dist_km, bearing_cbsd, _ = vincenty.GeodesicDistanceBearing(device['Lat'], device['Lon'], rx['Lat'], rx['Lon'])
        latmid, lonmid, _ = vincenty.GeodesicPoint(device['Lat'], device['Lon'], dist_km/2., bearing_cbsd)
        
        climate = climateDriver.TropoClim(latmid, lonmid)
        # If the common volume lies over the sea, the climate value to use depends
        # on the climate values at either end. A simple min() function should
        # properly implement the logic, since water is the max.
        if climate == 7:
            climate = min(climateDriver.TropoClim(device['Lat'], device['Lon']),
                        climateDriver.TropoClim(rx['Lat'], rx['Lon']))
          
        refractivity = refractDriver.Refractivity(latmid, lonmid)

        # Get the terrain profile, using Vincenty great circle route, and WF
        # standard (bilinear interp; 1501 pts for all distances over 45 km)
        its_elev = terrainDriver.TerrainProfile(lat1=device['Lat'], lon1=device['Lon'], lat2=rx['Lat'], lon2=rx['Lon'], target_res_meter=30., do_interp=True, max_points=1501)
      
        PL_dB_vectorized, _, _ = itm.point_to_point(its_elev, device['AntHeight'], rx['AntHeight'],
                                             dielec, conductivity, refractivity,
                                             rx['cntrFreq'], climate, polarization,
                                             confidence, reliabilities,
                                             mdvar, refractivity_final)       
        
        # compute the Rx power assuming a flat 0dB filter response for the
        # Receiver AND transmit CBSD is assumed to be omni anyway

        i = 0
        sampReceivedPwrLin =  np.zeros(N)
        for  PL in PL_dB_vectorized:
            sampRxPow = device['maxEIRP'] - PL;
            sampReceivedPwrLin[i] = 10.0**(sampRxPow/10.0);

            # aggregate the Rx Power as we go (in the linear scale)
            sampAggregateRxPowLin[i] = sampAggregateRxPowLin[i] + sampReceivedPwrLin[i];  
            i +=1       
        
        sampMedian_all_distributions_dBm[numdevice] = 10.0*np.log10(np.median(sampReceivedPwrLin));
        numdevice += 1
    
    mc50thp = 10.0*np.percentile(np.log10(sampAggregateRxPowLin),50)
    mc95thp = 10.0*np.percentile(np.log10(sampAggregateRxPowLin),95)

    return mc50thp, mc95thp

