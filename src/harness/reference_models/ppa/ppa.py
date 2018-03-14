#    Copyright 2016-2018 SAS Project Authors. All Rights Reserved.
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

import logging
import multiprocessing
from collections import namedtuple

import numpy as np
from concurrent import futures
from reference_models.antenna import antenna
from reference_models.geo import drive
from reference_models.geo import vincenty, nlcd
from reference_models.geo import utils
from reference_models.propagation import wf_hybrid

from shapely import geometry, ops
import json
import util

THRESHOLD_PER_10MHZ = -96
RX_HEIGHT = 1.5
MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_A = 30.
MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_B = 47.


def _CalculateDbLossForEachPointAndGetContour(install_param, eirp_capability, antenna_gain,
                                              cbsd_region_type, latitudes, longitudes):
  """Returns Vertex Point Distance for each azimuth with signal strength greater 
  than or equal to Threshold"""
  db_loss = np.zeros(len(latitudes), dtype=np.float64)
  for index, lat_lon in enumerate(zip(latitudes, longitudes)):
    lat, lon = lat_lon
    db_loss[index] = wf_hybrid.CalcHybridPropagationLoss(install_param['latitude'],
                                                         install_param['longitude'],
                                                         install_param['height'],
                                                         lat, lon, RX_HEIGHT,
                                                         install_param['indoorDeployment'],
                                                         reliability=0.5,
                                                         region=cbsd_region_type).db_loss

  index_cond, = np.where(
    (eirp_capability - install_param['antennaGain'] + antenna_gain) - db_loss >= THRESHOLD_PER_10MHZ)
  return index_cond.shape[0] * 0.2


def _HammingFilter(x, window_len=15):
  """Process a full radial at a given azimuth for all distance ranges"""
  s = np.r_[x[-(window_len / 2):], x, x[0:window_len / 2]]
  w = np.hamming(window_len)
  y = np.convolve(w / w.sum(), s, mode='valid')
  return y


def _GetPolygon(device):
  """Returns the PPA contour for a single CBSD device, as a shapely polygon."""
  install_param = device['installationParam']
  eirp_capability = install_param.get('eirpCapability',
                                      MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_A
                                      if device['cbsdCategory'] == 'A' else
                                      MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_B)

  # Compute all the Points in 0-359 every 200m upto 40km
  distances = np.arange(0.2, 40.1, 0.2)
  azimuths = np.arange(0.0, 360.0)
  latitudes, longitudes, _ = zip(*[vincenty.GeodesicPoints(install_param['latitude'],
                                                           install_param['longitude'],
                                                           distances, azimuth)
                                   for azimuth in azimuths])
  # Compute the Gain for all Direction
  antenna_gains = antenna.GetStandardAntennaGains(azimuths,
                                                  install_param['antennaAzimuth']
                                                  if 'antennaAzimuth' in install_param.keys()
                                                  else None,
                                                  install_param['antennaBeamwidth'],
                                                  install_param['antennaGain'])
  # Get the Nlcd Region Type for Cbsd
  cbsd_region_code = drive.nlcd_driver.GetLandCoverCodes(install_param['latitude'],
                                                         install_param['longitude'])
  cbsd_region_type = nlcd.GetRegionType(cbsd_region_code)
  # Compute the Path Loss, and contour based on Gain and Path Loss Comparing with Threshold
  # Smoothing Contour using Hamming Filter
  contour_dists_km = _HammingFilter([_CalculateDbLossForEachPointAndGetContour(install_param,
                                                                               eirp_capability, gain,
                                                                               cbsd_region_type,
                                                                               radial_lats, radial_lons)
                                     for radial_lats, radial_lons, gain in zip(latitudes,
                                                                               longitudes,
                                                                               antenna_gains)])
  # Generating lat, lon for Contour
  contour_lats, contour_lons, _ = zip(*[vincenty.GeodesicPoint(install_param['latitude'],
                                                               install_param['longitude'], dist, az)
                                        for dist, az in zip(contour_dists_km, azimuths)])
  return geometry.Polygon(zip(contour_lons, contour_lats)).buffer(0)


def _ClipPpaByCensusTract(contour_union, pal_records):
  """ Clip a PPA 'contour_union' zone (shapely.MultiPolygon) 
  with the census tracts defined by a sequence of 'pal_records'."""

  # Get the Census Tract for Each Pal Record and Convert it to Shapely Geometry
  census_tracts_for_pal = [geometry.shape(
      drive.census_tract_driver.GetCensusTract(pal['license']['licenseAreaIdentifier'])
      ['features'][0]['geometry']).buffer(0) for pal in pal_records]
  census_tracts_union = ops.cascaded_union(census_tracts_for_pal)
  return contour_union.intersection(census_tracts_union)


def PpaCreationModel(devices, pal_records):
  """Create a PPA Polygon based on the PAL Records and Device Information
  Args:
    devices: (List) A list containing device information.
    pal_records: (List) A list containing pal records.
  Returns:
    A PPA Polygon Dictionary in GeoJSON format
  """
  # Validation for Inputs
  for device in devices:
    logging.info('Validating device', device)
    util.assertContainsRequiredFields("RegistrationRequest.schema.json", device)
  for pal_rec in pal_records:
    logging.info('Validating pal_rec', pal_rec)
    util.assertContainsRequiredFields("PalRecord.schema.json", pal_rec)
  pool = futures.ProcessPoolExecutor(multiprocessing.cpu_count())
  # Create Contour for each CBSD
  device_polygon = list(pool.map(_GetPolygon, devices))
  # Create Union of all the CBSD Contours and Check for hole
  # after Census Tract Clipping
  contour_union = ops.cascaded_union(device_polygon)
  ppa_polygon = _ClipPpaByCensusTract(contour_union, pal_records)

  if ppa_polygon.is_empty:
    raise Exception("Empty Polygon is generated, please check the inputs.")
  if ppa_polygon.geom_type == "MultiPolygon":
    raise Exception("Multi Polygon is not supported, please check the inputs.")

  ppa_without_small_holes = utils.PolyWithoutSmallHoles(ppa_polygon)
  # Convert Shapely Object to GeoJSON Dictionary
  return json.dumps(geometry.mapping(ppa_without_small_holes))
