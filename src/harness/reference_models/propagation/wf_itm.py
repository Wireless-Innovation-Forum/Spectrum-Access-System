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

Typical usage:
  # Configure the terrain driver (memory use is: cache_size * 50MB)
  from reference_models.geo import drive
  drive.ConfigureTerrainDriver(terrain_dir=my_ned_path, cache_size=16)

  # Get the path loss and incidence angles
  db_loss, incidence_angles, internals = CalcItmPropagationLoss(
              lat_cbsd, lon_cbsd, height_cbsd,
              lat_rx, lon_rx, height_rx,
              cbsd_indoor=False,
              reliability=0.5,
              freq_mhz=3625.)
"""

from collections import namedtuple
import numpy as np

from reference_models.geo import drive
from reference_models.geo import vincenty
from reference_models.propagation.itm import itm

# TEMPORARY to avoid breaking code under PR
terrainDriver = drive.terrain_driver


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
                           reliability=0.5,
                           freq_mhz=3625.,
                           its_elev=None,
                           is_height_cbsd_amsl=False):
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
    is_height_cbsd_amsl: If True, the CBSD height shall be considered as AMSL (Average
                         mean sea level).
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
  if freq_mhz < 40.0 or freq_mhz > 10000:
    raise Exception('Frequency outside range [40MHz - 10GHz]')

  if is_height_cbsd_amsl:
    altitude_cbsd = drive.terrain_driver.GetTerrainElevation(lat_cbsd, lon_cbsd)
    height_cbsd = height_cbsd - altitude_cbsd

  # Ensure minimum height of 1 meter
  if height_cbsd < 1:
    height_cbsd = 1
  if height_rx < 1:
    height_rx = 1

  # Internal ITM parameters are always set to following values in WF version:
  confidence = 0.5     # Confidence (always 0.5)
  dielec = 25.         # Dielectric constant (always 25.)
  conductivity = 0.02  # Conductivity (always 0.02)
  polarization = 1     # Polarization (always vertical = 1)
  mdvar = 13

  # Get the terrain profile, using Vincenty great circle route, and WF
  # standard (bilinear interp; 1500 pts for all distances over 45 km)
  if its_elev is None:
    its_elev = drive.terrain_driver.TerrainProfile(
        lat1=lat_cbsd, lon1=lon_cbsd,
        lat2=lat_rx, lon2=lon_rx,
        target_res_meter=30.,
        do_interp=True, max_points=1501)

  # Find the midpoint of the great circle path
  dist_km, bearing_cbsd, bearing_rx = vincenty.GeodesicDistanceBearing(
      lat_cbsd, lon_cbsd, lat_rx, lon_rx)
  latmid, lonmid, _ = vincenty.GeodesicPoint(
      lat_cbsd, lon_cbsd, dist_km/2., bearing_cbsd)

  # Determine climate value, based on ITU-R P.617 method:
  climate = drive.climate_driver.TropoClim(latmid, lonmid)
  # If the common volume lies over the sea, the climate value to use depends
  # on the climate values at either end. A simple min() function should
  # properly implement the logic, since water is the max.
  if climate == 7:
    climate = min(drive.climate_driver.TropoClim(lat_cbsd, lon_cbsd),
                  drive.climate_driver.TropoClim(lat_rx, lon_rx))

  # Look up the refractivity at the path midpoint, if not explicitly provided
  refractivity = drive.refract_driver.Refractivity(latmid, lonmid)

  # Call ITM prop loss.
  reliabilities = reliability
  do_avg = False
  if np.isscalar(reliabilities) and reliability == -1:
    # Pathloss mean: average the value for 1% to 99% included
    reliabilities = np.arange(0.01, 1.0, 0.01)
    do_avg = True

  db_loss, ver_cbsd, ver_rx, str_mode, err_num = itm.point_to_point(
      its_elev, height_cbsd, height_rx,
      dielec, conductivity,
      refractivity, freq_mhz,
      climate, polarization,
      confidence, reliabilities,
      mdvar, False)
  if do_avg:
    db_loss = -10*np.log10(np.mean(10**(-np.array(db_loss)/10.)))

  # Add indoor losses
  if cbsd_indoor:
    if np.isscalar(db_loss):
      db_loss += 15
    else:
      db_loss = [loss+15 for loss in db_loss]

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


# Utility function to compute the HAAT for a CBSD
def ComputeHaat(lat_cbsd, lon_cbsd, height_cbsd, height_is_agl=True):
  """Computes a CBSD HAAT (Height above average terrain).

  Args:
    lat_cbsd, lon_cbsd: the CBSD location (degrees).
    height_cbsd: the CBSD antenna height (meters)
    height_is_agl: boolean specifying if height is AGL (Above Ground Level)
      or AMSL (Above Mean Sea Level).

  Returns:
    the CBSD HAAT (meters).
  """
  norm_haat, alt_ground = drive.terrain_driver.ComputeNormalizedHaat(lat_cbsd, lon_cbsd)
  if height_is_agl:
    return height_cbsd + norm_haat
  else:
    return height_cbsd - alt_ground + norm_haat
