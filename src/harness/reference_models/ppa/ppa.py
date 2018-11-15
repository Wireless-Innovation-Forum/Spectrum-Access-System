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
import json

import numpy as np
from shapely import geometry as sgeo
from shapely import ops

from reference_models.common import mpool
from reference_models.antenna import antenna
from reference_models.geo import drive
from reference_models.geo import vincenty
from reference_models.geo import nlcd
from reference_models.geo import utils
from reference_models.propagation import wf_hybrid
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
  lat_cbsd, lon_cbsd  = install_param['latitude'], install_param['longitude']
  height_cbsd = install_param['height']
  for index, lat_lon in enumerate(zip(latitudes, longitudes)):
    lat, lon = lat_lon
    db_loss[index] = wf_hybrid.CalcHybridPropagationLoss(
        lat_cbsd, lon_cbsd, height_cbsd,
        lat, lon, RX_HEIGHT,
        cbsd_indoor=install_param['indoorDeployment'],
        reliability=0.5,
        region=cbsd_region_type,
        is_height_cbsd_amsl=(install_param['heightType'] == 'AMSL')).db_loss

  index_cond, = np.where(
    (eirp_capability - install_param['antennaGain'] + antenna_gain) - db_loss
    >= THRESHOLD_PER_10MHZ)
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
                                      if device['cbsdCategory'] == 'A'
                                      else MAX_ALLOWABLE_EIRP_PER_10_MHZ_CAT_B)

  # Compute all the Points in 0-359 every 200m up to 40km
  distances = np.arange(0.2, 40.1, 0.2)
  azimuths = np.arange(0.0, 360.0)
  latitudes, longitudes, _ = zip(*[vincenty.GeodesicPoints(install_param['latitude'],
                                                           install_param['longitude'],
                                                           distances, azimuth)
                                   for azimuth in azimuths])
  # Compute the Gain for all Direction
  # Note: some parameters are optional for catA, so falling back to None (omni) then
  antenna_gains = antenna.GetStandardAntennaGains(
      azimuths,
      install_param['antennaAzimuth'] if 'antennaAzimuth' in install_param else None,
      install_param['antennaBeamwidth'] if 'antennaBeamwidth' in install_param else None,
      install_param['antennaGain'])
  # Get the Nlcd Region Type for Cbsd
  cbsd_region_code = drive.nlcd_driver.GetLandCoverCodes(install_param['latitude'],
                                                         install_param['longitude'])
  cbsd_region_type = nlcd.GetRegionType(cbsd_region_code)
  # Compute the Path Loss, and contour based on Gain and Path Loss Comparing with Threshold
  # Smoothing Contour using Hamming Filter
  contour_dists_km = _HammingFilter(
      [_CalculateDbLossForEachPointAndGetContour(install_param,
                                                 eirp_capability, ant_gain,
                                                 cbsd_region_type,
                                                 radial_lats, radial_lons)
       for radial_lats, radial_lons, ant_gain in zip(latitudes,
                                                     longitudes,
                                                     antenna_gains)])
  # Generating lat, lon for Contour
  contour_lats, contour_lons, _ = zip(*[
      vincenty.GeodesicPoint(install_param['latitude'], install_param['longitude'],
                             dists, az)
      for dists, az in zip(contour_dists_km, azimuths)])

  return sgeo.Polygon(zip(contour_lons, contour_lats)).buffer(0)


def _ClipPpaByCensusTract(contour_union, pal_records):
  """ Clip a PPA 'contour_union' zone (shapely.MultiPolygon)
  with the census tracts defined by a sequence of 'pal_records'."""

  # Get the Census Tract for Each Pal Record and Convert it to Shapely Geometry.
  census_tracts_for_pal = [sgeo.shape(
      drive.census_tract_driver.GetCensusTract(pal['license']['licenseAreaIdentifier'])
      ['features'][0]['geometry']).buffer(0) for pal in pal_records]
  census_tracts_union = ops.cascaded_union(census_tracts_for_pal)
  return contour_union.intersection(census_tracts_union)


def PpaCreationModel(devices, pal_records):
  """Creates a PPA Polygon based on the PAL Records and Device Information
  Args:
    devices: A list of CBSD records (schema |CbsdRecordData|).
    pal_records: A list of pal records.
  Returns:
    The PPA polygon in GeoJSON format (string).
  """
  # Validation for Inputs
  for device in devices:
    logging.info('Validating device', device)
    util.assertContainsRequiredFields("RegistrationRequest.schema.json", device)
  for pal_rec in pal_records:
    logging.info('Validating pal_rec', pal_rec)
    util.assertContainsRequiredFields("PalRecord.schema.json", pal_rec)

  # Create Contour for each CBSD
  pool = mpool.Pool()
  device_polygon = pool.map(_GetPolygon, devices)

  # Create Union of all the CBSD Contours and Check for hole
  # after Census Tract Clipping
  contour_union = ops.cascaded_union(device_polygon)
  logging.info('contour_union = %s', contour_union)
  ppa_polygon = _ClipPpaByCensusTract(contour_union, pal_records)
  logging.info('contour_union clipped by census tracts: %s', ppa_polygon)
  if ppa_polygon.is_empty:
    raise Exception("Empty Polygon is generated, please check the inputs.")
  if ppa_polygon.geom_type == "MultiPolygon":
    raise Exception("Multi Polygon is not supported, please check the inputs.")
  ppa_without_small_holes = utils.PolyWithoutSmallHoles(ppa_polygon)
  logging.info('ppa_without_small_holes = %s', ppa_without_small_holes)

  # Convert Shapely Object to GeoJSON geometry string
  return utils.ToGeoJson(ppa_without_small_holes)
