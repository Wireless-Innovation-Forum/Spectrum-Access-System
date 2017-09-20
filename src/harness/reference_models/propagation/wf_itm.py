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

"""WinnForum-specific version of ITM propagation model.

This version differs slightly from the ITM propagation model in some
input parameters. It also automatically manages Climate, Refractivity
and Terrain databases.

Typical usage:
  # Reconfigure the terrain driver
   #  - reset the terrain tile directory
  ConfigureTerrainDriver(terrain_dir=my_ned_path)
   #  - reset the cache size. Memory use is: cache_size * 50MB
  ConfigureTerrainDriver(cache_size=8)

  # Get the path loss and incidence angles
  db_loss, incidence_angles, internals = CalcItmPropagationLoss(
              lat_cbsd, lon_cbsd, height_cbsd,
              lat_rx, lon_rx, height_rx,
              reliability=0.5,
              freq_mhz=3625.)
"""

from collections import namedtuple
import logging
import numpy as np

from reference_models.geo import refractivity
from reference_models.geo import tropoclim
from reference_models.geo import vincenty
from reference_models.geo import terrain
from reference_models.propagation.itm import itm

# Initialize tropoclim and refractivity drivers
climateDriver = tropoclim.ClimateIndexer()
refractDriver = refractivity.RefractivityIndexer()
def ConfigureItuDrivers(itu_dir=None):
  """Configure the ITU climate and refractivity drivers.
  """
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


# ITM warning codes
class ItmErrorCode:
  NONE = 0
  CAUTION = 1
  NOTE = 2
  WARNING = 3
  OTHER = 4

_ITM_ERROR_MODES = {
    ItmErrorCode.NONE: 'No Error.',
    ItmErrorCode.CAUTION: ('Caution: Some parameters are nearly out of range.'
                           '  Results should be used with caution.'),
    ItmErrorCode.NOTE: ('Note: Default parameters have been substituted for impossible ones.'),
    ItmErrorCode.WARNING: ('Warning: A combination of parameters is out of range.'
                           '  Results are probably invalid.'),
    ItmErrorCode.OTHER: ('Warning: Some parameters are out of range.'
                         '  Results are probably invalid.')
}


def GetInfoOnItmCode(code):
  """Get description of ITM error code."""
  return _ITM_ERROR_MODES(code)

# Defined namedtuple for nice output packing
_PropagResult = namedtuple('_PropagResult',
                           ['db_loss', 'incidence_angles', 'internals'])
_IncidenceAngles = namedtuple('_IncidenceAngles',
                              ['hor_cbsd', 'ver_cbsd', 'hor_rx', 'ver_rx'])


# Main entry point for the Winnforum compliant ITM propagation model
def CalcItmPropagationLoss(lat_cbsd, lon_cbsd, height_cbsd,
                           lat_rx, lon_rx, height_rx,
                           cbsd_indoor=False,
                           reliability=0.5, freq_mhz=3625.,
                           its_elev=None):
  """Implements the WinnForum-compliant ITM point-to-point propagation model.

  According to WinnForum spec R2-SGN-17, R2-SGN-22 and R2-SGN-5 to 10.

  One can use this routine in 3 ways:
    reliability = -1 : to get the average path loss
    reliability in [0,1] : to get a pathloss for given quantile
    sequence of reliabilities: to get an array of pathloss. Used to obtain
      inverse CDF of the pathloss.

  Inputs:
    lat_cbsd, lon_cbsd, height_cbsd: Lat/lon (deg) and height AGL (m) of CBSD
    lat_rx, lon_rx, height_rx:       Lat/lon (deg) and height AGL (m) of Rx point
    cbsd_indoor:         CBSD indoor status - Default=False.
    reliability:         Reliability. Default is 0.5 (median value)
                         Different options:
                           value in [0,1]: returns the CDF quantile
                           -1: returns the mean path loss
                           iterable sequence: returns a list of path losses
    freq_mhz:            Frequency (MHz). Default is mid-point of band.
    its_elev:            Optional profile to use (in ITM format). Default=None
                           If not specified, it is extracted from the terrain.

  Returns:
    A namedtuple of:
      db_loss            Path Loss in dB, either a scalar if reliability is scalar
                           or a list of path losses if reliability is an iterable.

      incidence_angles:  A namedtuple of
          hor_cbsd:        Horizontal departure angle (bearing) from CBSD to Rx
          ver_cbsd:        Vertical departure angle at CBSD
          hor_rx:          Horizontal incidence angle (bearing) from Rx to CBSD
          ver_rx:          Vertical incidence angle at Rx

      internals:         A dictionary of internal data for advanced analysis:
          itm_err_num:     ITM error code from ItmErrorCode (see GetInfoOnItmCode).
          itm_str_mode:    String containing description of dominant prop mode.
          dist_km:         Distance between end points (km).
          prof_d_km        ndarray of distances (km) - x values to plot terrain.
          prof_elev        ndarray of terrain heightsheights (m) - y values to plot terrain,

  Raises:
    Exception if input parameters invalid or out of range.
  """
  # Sanity checks on input parameters
  if height_cbsd < 1 or height_rx < 1:
    raise Exception('Endpoint height less than 1m')
  if height_cbsd > 1000 or height_rx > 1000:
    raise Exception('Endpoint height greater than 1000m')
  if freq_mhz < 40.0 or freq_mhz > 10000:
    raise Exception('Frequency outside range [40MHz - 10GHz]')

  # Internal ITM parameters are always set to following values in WF version:
  confidence = 0.5     # Confidence (always 0.5)
  dielec = 25.         # Dielectric constant (always 25.)
  conductivity = 0.02  # Conductivity (always 0.02)
  polarization = 1     # Polarization (always vertical = 1)
  mdvar = 13

  # Get the terrain profile, using Vincenty great circle route, and WF
  # standard (bilinear interp; 1500 pts for all distances over 45 km)
  if its_elev is None:
    its_elev = terrainDriver.TerrainProfile(lat1=lat_cbsd, lon1=lon_cbsd,
                                           lat2=lat_rx, lon2=lon_rx,
                                           target_res_meter=30.,
                                           do_interp=True, max_points=1501)

  # Find the midpoint of the great circle path
  dist_km, bearing_cbsd, bearing_rx = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd, lat_rx, lon_rx)
  latmid, lonmid, _ = vincenty.GeodesicPoint(lat_cbsd, lon_cbsd, dist_km/2., bearing_cbsd)

  # Determine climate value, based on ITU-R P.617 method:
  climate = climateDriver.TropoClim(latmid, lonmid)
  # If the common volume lies over the sea, the climate value to use depends
  # on the climate values at either end. A simple min() function should
  # properly implement the logic, since water is the max.
  if climate == 7:
    climate = min(climateDriver.TropoClim(lat_cbsd, lon_cbsd),
                  climateDriver.TropoClim(lat_rx, lon_rx))

  # Look up the refractivity at the path midpoint, if not explicitly provided
  refractivity = refractDriver.Refractivity(latmid, lonmid)

  # Call ITM prop loss.
  reliabilities = reliability
  do_avg = False
  if np.isscalar(reliabilities) and reliability == -1:
    # Pathloss mean: average the value for 1% to 99% included
    reliabilities = np.arange(0.01, 1.0, 0.01)
    do_avg = True

  db_loss, str_mode, err_num = itm.point_to_point(its_elev, height_cbsd, height_rx,
                                                  dielec, conductivity,
                                                  refractivity, freq_mhz,
                                                  climate, polarization,
                                                  confidence, reliabilities,
                                                  mdvar, False)
  if do_avg:
    db_loss = np.mean(db_loss)

  if err_num !=  ItmErrorCode.NONE:
    logging.info('Got ITM applicability warning [%d]: %s' % (err_num, str_mode))

  # Add indoor losses
  if cbsd_indoor:
    if np.isscalar(db_loss):
      db_loss += 15
    else:
      db_loss = [loss+15 for loss in db_loss]

  # Get the incidence angles
  ver_cbsd, ver_rx, _, _ = GetHorizonAngles(its_elev, height_cbsd, height_rx, refractivity)

  # Create distance/terrain arrays for plotting if desired
  prof_d_km = (its_elev[1]/1000.) * np.arange(len(its_elev)-2)
  prof_elev = np.asarray(its_elev[2:])


  return _PropagResult(
      db_loss = db_loss,
      incidence_angles = _IncidenceAngles(
          hor_cbsd = bearing_cbsd,
          ver_cbsd = ver_cbsd,
          hor_rx = bearing_rx,
          ver_rx = ver_rx),
      internals = {
          'itm_err_num': err_num,
          'itm_str_mode': str_mode,
          'dist_km': dist_km,
          'prof_d_km': prof_d_km,
          'prof_elev': prof_elev
          })


# Utility function to compute the vertical incidence angles at CBSD and Rx
# This code is derived from the qlrps() routine in itm.py, as specified
# in R2-SGN-21. These data are returned as part of the above
# CalcItmPropagationLoss() routine.
def GetHorizonAngles(its_elev, height_cbsd, height_rx, refractivity):
  """Gets the horizon angles given a terrain profile.

  Derived from ITM hzns() routine as specified in R2-SGN-21.

  Inputs:
    its_elev:   Terrain profile in ITM format
                  - pfl[0] = number of terrain points + 1
                  - pfl[1] = step size, in meters
                  - pfl[i] = elevation above mean sea level, in meters
    height_cbsd:Height of the CBSD
    height_rx:  Height of the reception point

  Returns:
    a tuple of:
      ver_cbsd:      Vertical incidence angle. Positive value means upwards.
      ver_rx:        Vertical incidence angle. Positive value means upwards.
      hor_dist_cbsd: Horizon distance from CBSD (ie diffraction edge)
      hor_dist_rx:   Horizon distance from Rx (ie diffraction edge).
  """
  num_points = int(its_elev[0])
  step = its_elev[1]
  dist = num_points * step

  # Find the refractivity at the average terrain height
  start_avg = int(3.0 + 0.1 * num_points)
  end_avg = num_points - start_avg + 6
  zsys = np.mean(its_elev[start_avg-1:end_avg])
  refractivity *= np.exp(-zsys/9460.0)

  # Find the ray down-curvature per meter
  gma = 157e-9
  gme = gma*(1.0 - 0.04665 * np.exp(refractivity/179.3))

  alt_cbsd = its_elev[2] + height_cbsd
  alt_rx = its_elev[num_points+2] + height_rx
  qc = 0.5 * gme
  q = qc * dist
  # theta0 and theta1 the slopes, dl0 and dl1 the horizon distances
  theta1 = (alt_rx - alt_cbsd) / dist
  theta0 = theta1 - q
  theta1 = -theta1 - q
  dl0 = dist
  dl1 = dist

  if num_points >= 2:
    sa = 0.0
    sb = dist
    wq = True
    for i in range(1, num_points):
      sa += step
      sb -= step
      q = its_elev[i+2] - (qc*sa + theta0) * sa - alt_cbsd
      if q > 0.0:
        theta0 += q/sa
        dl0 = sa
        wq = False
      if not wq:
        q = its_elev[i+2] - (qc*sb + theta1) * sb - alt_rx
        if q > 0.0:
          theta1 += q/sb
          dl1 = sb

  return (np.arctan(theta0) * 180/np.pi,
          np.arctan(theta1) * 180/np.pi,
          dl0,
          dl1)
