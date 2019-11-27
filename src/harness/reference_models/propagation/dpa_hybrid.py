# This software was developed by employees of the National Institute
# of Standards and Technology (NIST), an agency of the Federal
# Government. Pursuant to title 17 United States Code Section 105, works
# of NIST employees are not subject to copyright protection in the United
# States and are considered to be in the public domain. Permission to freely
# use, copy, modify, and distribute this software and its documentation
# without fee is hereby granted, provided that this notice and disclaimer
# of warranty appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND,
# EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION
# WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE
# ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING,
# BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES,
# ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS
# SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR
# OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY
# OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT
# OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
#
# Distributions of NIST software should also include copyright and licensing
# statements of any third-party software that are legally bundled with
# the code in compliance with the conditions of those licenses.

#==================================================================================

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

#==================================================================================

""" Hybrid Propagation Model for DPAs based on NTIA TR 15-517.

The Hybrid DPA propagation model performs a hybrid of Extended-Hata and
Irregular Terrain Model (ITM) similar to NTIA TR 15-517.

NOTE: A random clutter factor, uniformly distributed in [0-15] dB, is applied to 
rural paths only when the CBSD antenna is below 18 m.

# The main routine is 'CalcHybridPropLoss()'

Typical usage:
  # Reconfigure the terrain driver
   #  - reset the terrain tile directory
  ConfigureTerrainDriver(terrain_dir=my_ned_path)
   #  - reset the cache size. Memory use is: cache_size * 50MB
  ConfigureTerrainDriver(cache_size=8)

  # Get the path loss and incidence angles
  db_loss, incidence_angles, internals = CalcHybridPropLoss(
              lat_cbsd, lon_cbsd, height_cbsd,
              lat_rx, lon_rx, height_rx,
              cbsd_indoor,
              reliability=0.5,
              freq_mhz=3625.)
"""
#==================================================================================

from collections import namedtuple
import math
from scipy.stats import norm
import numpy as np

from reference_models.geo import terrain
from reference_models.geo import nlcd
from reference_models.geo import vincenty
# from reference_models.propagation.itm import itm
from reference_models.propagation.ehata import ehata
from reference_models.propagation import wf_itm

# Initialize terrain driver
terrainDriver = terrain.TerrainDriver()
nlcdDriver = nlcd.NlcdDriver()

def ConfigureTerrainDriver(terrain_dir=None, cache_size=None):
  """Configure the NED terrain driver.

  Note that memory usage is about cache_size * 50MB.

  Inputs:
    terrain_dir: if specified, modify the terrain directory.
    cache_size:  if specified, change the terrain tile cache size.
  """
  if terrain_dir is not None:
    terrainDriver.SetTerrainDirectory(terrain_dir)
  if cache_size is not None:
    terrainDriver.SetCacheSize(cache_size)

def ConfigureNLCDDriver(nlcd_dir=None, cache_size=None):
  """Configure the NLCD driver.

  Note that memory usage is about cache_size * 50MB.

    Inputs:
      nlcd_dir: if specified, modify the nlcd directory.
      cache_size:  if specified, change the nlcd tile cache size.
  """
  if nlcd_dir is not None:
      nlcdDriver.SetNlcdDirectory(nlcd_dir)
  if cache_size is not None:
      nlcdDriver.SetCacheSize(cache_size)

# eHata standard deviation calculation parameters
# according to WinnForum R2-SGN-22, and NTIA Technical Report
# TR-15-517, equation A18(a),(b),(c)
_ALPHA_U = 4.0976291
_BETA_U = -1.2255656
_GAMMA_U = 0.68350345

# Defined namedtuple for nice output packing
_PropagResult = namedtuple('_PropagResult',
                           ['db_loss', 'incidence_angles'])
_IncidenceAngles = namedtuple('_IncidenceAngles',
                              ['hor_tx', 'ver_tx', 'hor_cbsd', 'ver_cbsd'])

def GetEHataLocationVar(freq_mhz, region_code, reliability):
  """Gets ehata location variablibity of the median propagation loss.

  Inputs:
    freq_mhz:       the frequency in MHz. Used to compute the eHata stdev.
    region_code:    region code (22:'SUBURBAN'; 23/24:'URBAN'; others: 'RURAL')
    reliability:    reliability value in [0,1]

  Returns:
    the offset in dB to apply to the median
  """

  # Get standard deviation of the location variability
  std = (_ALPHA_U + _BETA_U * math.log10(freq_mhz)
           + _GAMMA_U * math.log10(freq_mhz) ** 2)

  if region_code != 22 and region_code != 23 and region_code != 24:
    std += 2

  # print 'std: ' + str(std)
  offset = norm(0, std).ppf(reliability)

  return offset

def ComputeEffectiveHeights(its_elev, height_tx, height_rx):
  """Get effective heights of transmitter and receiver.
  Based on Paul McKenna's letter to Andy Clegg on April 11, 2017.  to
  revise effective height calculation.

  Inputs:
    its_elev:  terrain profile in ITS format.
    height_tx: height of the transmitter above terrain (meters).
    height_rx: height of the receiver above terrain (meters).

  Returns:
    eff_height_tx: effective height of the transmitter (meters).
    eff_height_rx: effective height of the receiver (meters).
  """

  npts = int(its_elev[0])
  xi = its_elev[1] / 1000   # step size of the profile points, in km
  dist_km = npts * xi       # path distance, in km

  if dist_km < 3.0:         # Use terminals' structural height
    eff_height_tx = height_tx
    eff_height_rx = height_rx
    return eff_height_tx, eff_height_rx

  else: # dist_km >= 3 km

    # Compute effective height of the transmitter
    i_start = 2 + int(math.ceil(3.0 / xi))
    i_end = npts + 2
    if dist_km > 15:
      i_end = 2 + int(math.floor(15.0 / xi))
      dist_km = 15.0

    elev_tx = its_elev[2]
    avg_height_tx = sum(its_elev[i_start:i_end+1]) / float(i_end - i_start + 1)
    eff_height_tx = height_tx + (dist_km - 3.0) / 12.0 * (elev_tx - avg_height_tx)

    # Limit the transmitter effective height to [30, 200] m
    if eff_height_tx < 30:
      eff_height_tx = 30
    elif eff_height_tx > 200:
      eff_height_tx = 200

    # Compute effective height of the receiver
    i_start = 2
    i_end = npts + 2 - int(math.ceil(3.0 / xi))
    if dist_km > 15:
      i_start = npts + 2 - int(math.floor(15.0 /xi))
      dist_km = 15.0

    elev_rx = its_elev[-1]
    avg_height_rx = sum(its_elev[i_start:i_end+1]) / float(i_end - i_start + 1)
    eff_height_rx = height_rx + (dist_km - 3.0) / 12.0 * (elev_rx - avg_height_rx)

    # Limit the effective height to [1, 10] m
    if eff_height_rx < 1:
      eff_height_rx = 1
    elif eff_height_rx > 10:
      eff_height_rx = 10

    return eff_height_tx, eff_height_rx


# Main entry point of the Hybrid model
def CalcHybridPropLoss(lat_cbsd, lon_cbsd, height_cbsd,
                       lat_rx, lon_rx, height_rx,
                       cbsd_indoor=False,
                       reliability=0.5, freq_mhz=3625.):

  """Implements the Hybrid ITM/eHata DPA propagation model.

  Inputs:
    lat_cbsd, lon_cbsd, height_cbsd: Lat/lon (deg) and height AGL (m) of CBSD
    lat_rx, lon_rx, height_rx:       Lat/lon (deg) and height AGL (m) of Rx point
    cbsd_indoor:        CBSD indoor status - Default=False.
    reliability:        Reliability value in [0.001, 0.999). Default is 0.5 (median value).
    freq_mhz:           Frequency (MHz). Default is mid-point of band.
  Returns:
    A namedtuple of:
      db_loss:          Path Loss in dB.

      incidence_angles: A namedtuple of angles (degrees)
          hor_cbsd:       Horizontal departure angle (bearing) from CBSD to Rx
          ver_cbsd:       Vertical departure angle at CBSD
          hor_rx:         Horizontal incidence angle (bearing) from Rx to CBSD
          ver_rx:         Vertical incidence angle at Rx

  Raises:
    Exception if input parameters invalid or out of range.
  """

  # Sanity checks on input parameters
  if height_cbsd < 1 or height_rx < 1:
    raise Exception('End-point height less than 1m.')
  if height_cbsd > 1000 or height_rx > 1000:
    raise Exception('End-point height greater than 1000m.')
  if freq_mhz < 40 or freq_mhz > 10000:
    raise Exception('Frequency outside range [40MHz - 10GHz].')

  # Get land use region at the CBSD location
  region_code = nlcdDriver.GetLandCoverCodes(lat_cbsd, lon_cbsd)

  # Get the terrain profile, using Vincenty great circle route, and WF
  # standard (bilinear interp; 1501 pts for all distances over 45 km)
  its_elev = terrainDriver.TerrainProfile(lat1=lat_cbsd, lon1=lon_cbsd,
                                          lat2=lat_rx, lon2=lon_rx,
                                          target_res_meter=30.,
                                          do_interp=True, max_points=1501)

  # Calculate the median and basic ITM losses
  reliabilities = np.append(reliability, [0.5])  # add 0.5 (for median loss) as
                                                 # a last value to reliabilities array

  # Use WINNF ITM model
  db_loss_itm, incidence_angles_itm, _ = wf_itm.CalcItmPropagationLoss(lat_cbsd, lon_cbsd, height_cbsd,
                                            lat_rx, lon_rx, height_rx,
                                            False, reliabilities, freq_mhz, its_elev)

  # Median ITM loss
  db_loss_itm_median = db_loss_itm[-1]

  # Determine loss based on CBSD height and region_code
  if region_code == 22 or region_code == 23 or region_code == 24 :# 22:'SUBURBAN'; 23/24:'URBAN'
    if height_cbsd > 18:     # Use ITM if CBSD height greater than 18 m
      db_loss = db_loss_itm[0:-1]
    else:                    # Use max of ehata/ITM
      # CBSD is the "mobile" and incumbent is the "base" in eHata.  Swap them and reverse
      # the elevation profile (but preserving the order of the first two elements, number of
      # intervals and interval distance).
      db_loss_ehata_median = ehata.ExtendedHata(its_elev[0:2] + its_elev[:1:-1], freq_mhz, height_rx, height_cbsd,
                                         region_code)
      if db_loss_ehata_median > db_loss_itm_median:
        db_loss = (db_loss_ehata_median + GetEHataLocationVar(freq_mhz, region_code, reliability)).tolist()
      else:
        db_loss = db_loss_itm[0:-1]
  else:  # 'RURAL' or other regions: use ITM  
    db_loss = db_loss_itm[0:-1]	  
    if height_cbsd <= 18: # Add an additional clutter factor
      clutter_loss = np.random.uniform(0, 15) # uniformly distributed in 0-15 dB
      if np.isscalar(db_loss):
        db_loss += clutter_loss
      else:
        db_loss = [loss + clutter_loss for loss in db_loss]

  if cbsd_indoor:
    # Add indoor losses:  20 dB, 15 dB, or 10 dB,
    # with probabilities 0.2, 0.6, and 0.2, respectively
    indoor_loss = np.random.choice([20, 15, 10], p=[0.2, 0.6, 0.2])
    if np.isscalar(db_loss):
      db_loss += indoor_loss
    else:
      db_loss = [loss + indoor_loss for loss in db_loss]

  return _PropagResult(
      db_loss = db_loss,
      incidence_angles = incidence_angles_itm)


def ClutterLoss(lat_cbsd, lon_cbsd, height_cbsd,
                lat_rx, lon_rx,
                reliability=0.5, freq_mhz=3625.):

  """Returns the clutter loss using the ITU-R P.2108 statistical clutter loss model for
     terrestrial paths.

  Inputs:
    lat_cbsd, lon_cbsd, height_cbsd: Lat/lon (deg) and height AGL (m) of CBSD
    lat_rx, lon_rx:     Lat/lon (deg) of Rx point
    reliability:        Reliability values in [0.001, 0.999). Default is 0.5 (median value).
    freq_mhz:           Frequency (MHz). Default is mid-point of band.
  Returns:
    clutter loss in dB, same length as input 'reliability'

  Raises:
    Exception if input parameters invalid or out of range.
  """

  # Sanity checks on input parameters
  if height_cbsd < 1:
    raise Exception('End-point height less than 1m.')
  if height_cbsd > 1000:
    raise Exception('End-point height greater than 1000m.')
  if freq_mhz < 2000 or freq_mhz > 67000:
    raise Exception('Frequency outside range [2 GHz - 67 GHz].')

  # Get land use region at the CBSD location
  region_code = nlcdDriver.GetLandCoverCodes(lat_cbsd, lon_cbsd)

  # Calculate clutter loss only if CBSD height is at or below clutter height.
  # Use default clutter heights in ITU-R P.2108 Table 3.
  if region_code == 22 and height_cbsd > 10: return 0.0   # 'SUBURBAN'
  if region_code in [23, 41, 42, 43] and height_cbsd > 15: return 0.0   # 'URBAN' or '*_FOREST'
  if region_code == 24 and height_cbsd > 20: return 0.0   # 'DENSE URBAN'
  if region_code not in [22, 23, 24, 41, 42, 43] and height_cbsd > 10: return 0.0   # treat all others as 'RURAL'

  # Compute distance from CBSD location to receiver location
  dist_km, _, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd, lat_rx, lon_rx)

  # Calculate the median clutter loss in dB using equations (3)-(5) in ITU-R P.2108-0
  f_GHz = freq_mhz / 1000.
  L_l = 23.5 + 9.6 * np.log10(f_GHz)
  L_s = 32.98 + 23.9 * np.log10(dist_km) + 3 * np.log10(f_GHz)
  median_clutter_loss_db = -5 * np.log10(10.**(-0.2 * L_l) + 10.**(-0.2 * L_s))

  # Calculate samples of the clutter loss distribution, one for each given reliability
  clutter_loss_db = median_clutter_loss_db - 6 * norm.ppf(1. - reliability)

  return clutter_loss_db
