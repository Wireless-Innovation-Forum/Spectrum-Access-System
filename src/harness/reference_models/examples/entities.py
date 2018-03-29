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
This is *NOT* to be used for actual test harness.
"""

from collections import namedtuple
import numpy as np
import shapely.geometry as sgeo

from reference_models.geo import vincenty
from reference_models.geo import nlcd

# CBSD devices
Cbsd = namedtuple('Cbsd',
                  ['latitude',
                   'longitude',
                   'height_agl',
                   'is_indoor',
                   'category',
                   'eirp_dbm_mhz',
                   'antenna_azimuth',
                   'antenna_beamwidth',
                   'antenna_gain'])

# Typical CBSD templates
# - Cat A Indoor - Omni - 23dBm EIRP
CBSD_TEMPLATE_CAT_A_INDOOR = Cbsd(latitude=0,longitude=0,
                                  height_agl=3,
                                  is_indoor=True,
                                  category='A',
                                  eirp_dbm_mhz=13,
                                  antenna_azimuth=0,
                                  antenna_beamwidth=None,
                                  antenna_gain=0)

# - Cat A Outdoor - Omni - 30dBm  EIRP
CBSD_TEMPLATE_CAT_A_OUTDOOR = Cbsd(latitude=0,longitude=0,
                                   height_agl=6,
                                   is_indoor=False,
                                   category='A',
                                   eirp_dbm_mhz=20,
                                   antenna_azimuth=0,
                                   antenna_beamwidth=None,
                                   antenna_gain=6)

# - Cat B Outdoor - Sectorized - 47dBm EIRP
CBSD_TEMPLATE_CAT_B = Cbsd(latitude=0,longitude=0,
                           height_agl=10,
                           is_indoor=False,
                           category='B',
                           eirp_dbm_mhz=37,
                           antenna_azimuth=[0, 120, 240],
                           antenna_beamwidth=90,
                           antenna_gain=15)

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
  azimuths = (t.antenna_azimuth if isinstance(t.antenna_azimuth, list)
              else [t.antenna_azimuth])
  cbsds = []
  for k in xrange(n_cbsd):
    lat, lng, _ = vincenty.GeodesicPoint(ref_latitude, ref_longitude,
                                         distances[k], bearings[k])
    for azimuth in azimuths:
      cbsd = Cbsd(lat, lng,
                  t.height_agl, t.is_indoor, t.category, t.eirp_dbm_mhz,
                  int(azimuth + np.random.uniform(0, 360)) % 360,
                  t.antenna_beamwidth, t.antenna_gain)
      cbsds.append(cbsd)

  return cbsds


def GenerateCbsdsInPolygon(num_cbsds, template_cbsd, polygon,
                           nlcd_driver=None, urban_areas=None):
  """Returns an inland Cbsd within polygon, possibly in urban area.


  Args:
    template_cbsd: An |Cbsd| used as a template.
    polygon: A |shapely.Polygon| where to put the Cbsd.
    nlcd_driver: The land cover driver for detecting inland positions (optional).
    urban_areas: An optional  |shapely.MultiPolygon| defining the urban areas.
      If not specified, do not enforce the Cbsd to be in urban areas.
  """
  if urban_areas is not None:
    urban_areas = urban_areas.intersect(polygon)
  t = template_cbsd
  bounds = polygon.bounds
  cbsds = []
  while len(cbsds) < num_cbsds:
    while True:
      lng = np.random.uniform(bounds[0], bounds[2])
      lat = np.random.uniform(bounds[1], bounds[3])
      if not sgeo.Point(lng, lat).within(polygon):
        continue
      if nlcd_driver is not None:
        land_cover = nlcd_driver.GetLandCoverCodes(lat, lng)
        if land_cover <= nlcd.LandCoverCodes.PERENNIAL_SNOW:
          continue

      if urban_areas is not None:
        if not sgeo.Point(lng, lat).within(urban_areas):
          continue
      break

    azimuth_offset = np.random.uniform(0, 360)
    azimuths = (t.antenna_azimuth if isinstance(t.antenna_azimuth, list)
                else [t.antenna_azimuth])
    for azimuth in azimuths:
      cbsds.append(Cbsd(lat, lng, t.height_agl, t.is_indoor, t.category,
                        t.eirp_dbm_mhz, azimuth,
                        t.antenna_beamwidth, t.antenna_gain))

  return cbsds


# Utility routines to convert Cbsd object into registration and grant requests.
def GetCbsdRegistrationRequest(cbsd):
  """Returns a CBSD registration request from the |Cbsd| object.
  """
  return {
      'cbsdCategory': cbsd.category,
      'installationParam': {
          'latitude': cbsd.latitude,
          'longitude': cbsd.longitude,
          'height': cbsd.height_agl,
          'heightType': 'AGL',
          'indoorDeployment': cbsd.is_indoor,
          'antennaBeamwidth': cbsd.antenna_beamwidth,
          'antennaAzimuth': cbsd.antenna_azimuth,
          'antennaGain': cbsd.antenna_gain,
      }
  }


def GetCbsdGrantRequest(cbsd, min_freq_mhz, max_freq_mhz):
  """Returns a CBSD grant request from a |Cbsd| object and a min/max frequency.
  """
  return {
      'operationParam': {
          'operationFrequencyRange': {
              'lowFrequency': min_freq_mhz * 1e6,
              'highFrequency': max_freq_mhz * 1e6
          },
          'maxEirp': cbsd.eirp_dbm_mhz
      }
  }
