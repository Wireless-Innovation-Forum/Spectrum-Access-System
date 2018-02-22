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

"""Simple data model for SAS entities, and utility routines.

Used solely for running various examples of the protection logic.
"""

from collections import namedtuple
import numpy as np

from reference_models.geo import vincenty

# CBSD devices
Cbsd = namedtuple('Cbsd',
                  ['latitude',
                   'longitude',
                   'height_agl',
                   'is_indoor',
                   'category',
                   'eirp_dbm',
                   'antenna_azimuth',
                   'antenna_beamwidth'])

# Typical CBSD templates
# - Cat A Indoor - Omni - 23dBm EIRP
CBSD_TEMPLATE_CAT_A_INDOOR = Cbsd(latitude=0,longitude=0,
                                  height_agl=3,
                                  is_indoor=True,
                                  category='A',
                                  eirp_dbm=23,
                                  antenna_azimuth=0,
                                  antenna_beamwidth=None)

# - Cat A Outdoor - Omni - 30dBm  EIRP
CBSD_TEMPLATE_CAT_A_OUTDOOR = Cbsd(latitude=0,longitude=0,
                                   height_agl=6,
                                   is_indoor=False,
                                   category='A',
                                   eirp_dbm=30,
                                   antenna_azimuth=0,
                                   antenna_beamwidth=None)

# - Cat B Outdoor - Sectorized - 47dBm EIRP
CBSD_TEMPLATE_CAT_B = Cbsd(latitude=0,longitude=0,
                           height_agl=6,
                           is_indoor=False,
                           category='B',
                           eirp_dbm=47,
                           antenna_azimuth=[0, 120, 240],
                           antenna_beamwidth=90)

# FSS earth station
FssLicenseInfo = namedtuple('FssLicenseInfo',
                            ['latitude',
                             'longitude',
                             'height_agl',
                             'max_gain_dbi',
                             'satellite_arc_east_limit',
                             'satellite_arc_west_limit',
                             'elevation_east_limit',
                             'elevation_west_limit',
                             'azimuth_east_limit',
                             'azimuth_west_limit'])

FssProtection = namedtuple('FssProtectionPoint',
                           ['latitude',
                            'longitude',
                            'height_agl',
                            'max_gain_dbi',
                            'pointing_azimuth',
                            'pointing_elevation'])





def GenerateCbsdList(n_cbsd, template_cbsd,
                     ref_latitude, ref_longitude,
                     min_distance_km=1,
                     max_distance_km=150,
                     min_angle=0, max_angle=360):
  """Generate a random list of CBSDs from a CBSD template.

  The CBSD are randomly generated in a circular sector around a reference point,
  and using a CBSD template.
  If the template contains a list of azimuth, then multi-sector CBSD are built
  with the given azimuths. Otherwise a random azimuth is used.

  Inputs:
    n_cbsd:          Number of CBSD to generate.
    template_cbsd:   A |Cbsd| namedtuple used as a template for all non location
                     parameters.
    ref_latitude:    Reference point latitude (degrees).
    ref_longitude:   Reference point longitude (degrees).
    min_distance_km: Minimum distance of CBSD from central point (km). Default 1km.
    max_distance_km: Maximum distance of CBSD from central point (km). Default 150km.
    min_angle:       Minimum angle of the circular sector (degrees). Default 0
    max_angle:       Maximum angle of the circular sector (degrees). Default 360
                     Note that 0 degree is the north, and the angle goes clockwise.

  Returns:
    a list of |Cbsd| namedtuple
  """
  distances = np.random.uniform(min_distance_km, max_distance_km, n_cbsd)
  bearings = np.random.uniform(min_angle, max_angle, n_cbsd)
  t = template_cbsd
  multi_sectored = False
  if isinstance(t.antenna_azimuth, list):
    multi_sectored = t.antenna_azimuth

  cbsds = []
  for k in xrange(n_cbsd):
    lat, lng, _ = vincenty.GeodesicPoint(ref_latitude, ref_longitude,
                                         distances[k], bearings[k])
    if multi_sectored:
      for azimuth in multi_sectored:
        cbsd = Cbsd(lat, lng,
                    t.height_agl, t.is_indoor, t.category, t.eirp_dbm,
                    azimuth, t.antenna_beamwidth)
        cbsds.append(cbsd)
    else:
      cbsd = Cbsd(lat, lng,
                  t.height_agl, t.is_indoor, t.category, t.eirp_dbm,
                  np.random.uniform(0, 360, 1)[0], t.antenna_beamwidth)
      cbsds.append(cbsd)

  return cbsds
