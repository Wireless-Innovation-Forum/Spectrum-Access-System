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

"""GSO (Geostationary Satellite Orbit) utility library.

Allows to obtain the actual pointing directions of a FSS earth station
towards all licensed orbital slot.
See an example of FSS earth station license at:
  http://licensing.fcc.gov/myibfs/displayLicense.do?filingKey=-205179

Typical usage:
  # Get the list of possible pointing direction according to license limitations
  pointings = GsoPossiblePointings(fss_lat, fss_lon,
                                   west_sat_lon, east_sat_lon,
                                   west_elevation_limit, east_elevation_limit,
                                   west_azimuth_limit, east_azimuth_limit)
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math

_GSO_SPHERICAL_CST = 0.1512


def GsoElevation(fss_lat, fss_lon, sat_lon):
  """Computes the elevation angle from earth station towards GSO satellite.

  Based on Appendix D of FCC 05-56.

  Inputs:
    fss_lat:   Latitude of earth station (degrees)
    fss_lon:   Longitude of earth station (degrees)
    sat_lon:   Longitude of satellite (degrees)

  Returns:
    the elevation angle of the pointing arc from earth station to GSO satellite.
  """
  fss_lat = math.radians(fss_lat)
  fss_lon = math.radians(fss_lon)
  sat_lon = math.radians(sat_lon)

  delta = sat_lon - fss_lon
  elevation = math.atan2(math.cos(delta) * math.cos(fss_lat) - _GSO_SPHERICAL_CST,
                         math.sqrt(1 - math.cos(delta)**2 * math.cos(fss_lat)**2))

  return math.degrees(elevation)


def GsoAzimuth(fss_lat, fss_lon, sat_lon):
  """Computes the azimuth angle from earth station toward GSO satellite.

  Based on Appendix D of FCC 05-56.

  Inputs:
    fss_lat:   Latitude of earth station (degrees)
    fss_lon:   Longitude of earth station (degrees)
    sat_lon:   Longitude of satellite (degrees)

  Returns:
    the azimuth angle of the pointing arc from earth station to GSO satellite.
  """
  fss_lat = math.radians(fss_lat)
  fss_lon = math.radians(fss_lon)
  sat_lon = math.radians(sat_lon)
  if fss_lat > 0:
    azimuth = math.pi - math.atan2(math.tan(sat_lon-fss_lon),
                                   math.sin(fss_lat))
  else:
    azimuth = math.atan2(math.tan(sat_lon-fss_lon),
                         math.sin(-fss_lat))
    if azimuth < 0: azimuth += 2*math.pi

  return math.degrees(azimuth)


def _GsoExtent(fss_lat, fss_min_elevation=5):
  """Computes the longitude extent for GSO arc visibility.

  The GSO orbit is visible between FSS longitude plus/minus the extent.
  Based on Appendix D of FCC 05-56.

  Inputs:
    fss_lat:   Latitude of earth station (degrees).
    fss_min_elevation:  Minimum elevation of angle of the FSS
                        earth station (degrees).

  Returns:
    the longitudinal extend in degrees of GSO arc visibility.
  """
  if fss_lat > 81: return 0  # visibility limited to latitude 81 degree

  fss_lat = math.radians(fss_lat)
  fss_min_elevation = math.radians(fss_min_elevation)

  tan_el2 = math.tan(fss_min_elevation)**2
  a = 1 + tan_el2
  b = -2 * _GSO_SPHERICAL_CST
  c = _GSO_SPHERICAL_CST**2 - tan_el2
  x = (-b + math.sqrt(b**2 - 4 * a * c)) / (2 * a)
  extent = math.acos(x / math.cos(fss_lat))
  return math.degrees(math.abs(extent))


def GsoPossiblePointings(fss_lat, fss_lon,
                         west_sat_lon=None, east_sat_lon=None,
                         west_elevation_limit=0, east_elevation_limit=0,
                         west_azimuth_limit=None, east_azimuth_limit=None):

  """Computes all possible pointings of FSS earth station to allowed GSO slots.

  C-band satellites are only licensed for odd-degree orbital slots (61, 63..).
  Further constraints are used to restrict the extent of possible orbital slots.

  Inputs:
    fss_lat:   Latitude of FSS earth station (degrees).
    fss_lon:   Longitude of FSS earth station (degrees).
    west_sat_lon: West bound allowed satellite longitude (degrees) - optional
    east_sat_lon: East bound allowed satellite longitude (degrees) - optional
    west_elevation_limit: West bound elevation limit (degrees) - default=0
    east_elevation_limit: East bound elevation limit (degrees) - default=0
    west_azimuth_limit: West bound azimuth limit (degrees) - optional
    east_azimuth_limit: East bound azimuth limit (degrees) - optional

  Returns:
    a list of tuple (azi, elev) of possible pointing direction for FSS.
  """
  allowed_pointings = []
  if west_sat_lon is None:
    west_sat_lon = fss_lon - 180
  if east_sat_lon is None:
    east_sat_lon = fss_lon + 180

  # Manage crossover of 180degree meridian
  if west_sat_lon > east_sat_lon:
    delta_west = fss_lon - west_sat_lon
    delta_east = fss_lon - east_sat_lon
    if abs(delta_west) > abs(delta_east):
      west_sat_lon -= 360
    else:
      east_sat_lon += 360

  # Find all orbital slots and corresponding pointing directions
  # Note: Using loops from the FSS meridian east then west, as it allows to
  #       handle nicely crossover over the +-180degree meridians.
  lon = int(fss_lon/2) * 2 - 1  # odd-degree nearby orbit slot
  while True:
    lon += 2
    if lon > east_sat_lon: break
    if lon < west_sat_lon: continue
    elevation = GsoElevation(fss_lat, fss_lon, lon)
    azimuth = GsoAzimuth(fss_lat, fss_lon, lon)
    if elevation < east_elevation_limit: break
    if east_azimuth_limit is not None:
      if fss_lat > 0:
        if azimuth < east_azimuth_limit: break
        if azimuth > west_azimuth_limit: continue
      else:
        if azimuth > east_azimuth_limit: break
        if azimuth < west_azimuth_limit: continue
    allowed_pointings.append((azimuth, elevation))

  lon = int(fss_lon/2) * 2 + 1
  while True:
    lon -= 2
    if lon < west_sat_lon: break
    if lon > east_sat_lon: continue
    elevation = GsoElevation(fss_lat, fss_lon, lon)
    azimuth = GsoAzimuth(fss_lat, fss_lon, lon)
    if elevation < west_elevation_limit: break
    if west_azimuth_limit is not None:
      if fss_lat > 0:
        if azimuth > west_azimuth_limit: break
        if azimuth < east_azimuth_limit: continue
      else:
        if azimuth < west_azimuth_limit: break
        if azimuth > east_azimuth_limit: continue
    allowed_pointings.append((azimuth, elevation))

  return allowed_pointings
