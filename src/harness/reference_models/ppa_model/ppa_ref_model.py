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


import multiprocessing

import geojson
import numpy as np
from concurrent import futures
from reference_models.geo import census_tract, utils, vincenty, nlcd
from reference_models.propagation import wf_hybrid
from reference_models.antenna import antenna
from shapely import geometry, ops

THRESHOLD_PER_10MHZ = -96
RX_HEIGHT = 1.5

census_tract_driver = census_tract.CensusTractDriver()
nlcd_driver = nlcd.NlcdDriver()


def _CalculateDbLossForEachPointAndGetContour(install_param, antenna_gain, latitudes, longitudes):
  db_loss = np.zeros(len(latitudes), dtype=np.float64)
  for index, lat_lon in enumerate(zip(latitudes, longitudes)):
    lat, lon = lat_lon
    code = nlcd_driver.GetLandCoverCodes(lat, lon)
    region_type = nlcd.GetRegionType(code)
    db_loss[index] = wf_hybrid.CalcHybridPropagationLoss(install_param['latitude'],
                                                         install_param['longitude'],
                                                         install_param['height'],
                                                         lat, lon, RX_HEIGHT,
                                                         install_param['indoorDeployment'],
                                                         reliability=0.5,
                                                         region=region_type).db_loss

  index_cond, _ = np.where(install_param['eirpCapability'] - db_loss + antenna_gain > THRESHOLD_PER_10MHZ)
  return index_cond.shape[0] / 5.


def _HammingFilter(x, window_len=15):
  s = np.r_[x[-(window_len / 2):], x, x[0:window_len / 2]]
  w = np.hamming(window_len)
  y = np.convolve(w / w.sum(), s, mode='valid')
  return y


def _GetPolygon(device):
  install_param = device['installationParam']
  # Get all the Function Partials
  # Compute all the Points in 0-359 every 200m upto 40km
  distance = np.arange(0.2, 40.2, 0.2)
  latitudes, longitudes, _ = zip(*[vincenty.GeodesicPoints(install_param['latitude'],
                                                         install_param['longitude'],
                                                         distance, azimuth)
                                 for azimuth in np.arange(0, 360)])
  # Compute the Gain for all Direction
  antenna_gain = antenna.GetStandardAntennaGains(np.arange(0, 360),
                                                 install_param['antennaAzimuth']
                                                 if 'antennaAzimuth' in install_param.keys() else None,
                                                 install_param['antennaBeamwidth'],
                                                 install_param['antennaGain'])
  # Compute the Path Loss, and contour based on Gain and Path Loss Comparing with Threshold
  # Smoothing Contour using Hamming Filter
  contour_pts = _HammingFilter([_CalculateDbLossForEachPointAndGetContour(install_param, gain, lat, lon)
                                for lat, lon, gain in zip(latitudes, longitudes, antenna_gain)])

  # Generating lat, lon for Contour
  contour_lats, contour_lons, _ = [vincenty.GeodesicPoint(install_param['latitude'],
                                                        install_param['longitude'], cn, az)
                                 for cn, az in zip(contour_pts, np.arange(0, 360))]
  return geometry.shape(zip(contour_lons, contour_lats)).buffer(0)


def _ClipPpaByCensusTract(contour_union, pal_records):
  # Get the Census Tract for Each Pal Record and Convert it to Shapely Geometry
  census_tracts_for_pal = [geometry.shape(census_tract_driver.GetCensusTract(pal['license']
                                                                             ['licenseAreaIdentifier'])
                                          ['features'][0]['geometry']).buffer(0) for pal in pal_records]
  census_tracts_union = ops.cascaded_union(census_tracts_for_pal)
  return contour_union.intersection(census_tracts_union)


def _ConvertToGeoJson(ppa_polygon):
  if ppa_polygon.type == 'MultiPolygon':
    ppa_geojson = geojson.FeatureCollection(
      [geojson.Feature(geometry=polygon for polygon in ppa_polygon)])
  else:
    ppa_geojson = geojson.FeatureCollection(
      [geojson.Feature(geometry=ppa_polygon)])
  return ppa_geojson


def ConfigureCensusTractDriver(census_tract_dir=None):
  """Configure the Census Tract driver.

  Inputs:
    census_tract_dir: if specified, changes the census tract default directory.
  """
  if census_tract_dir is not None:
    census_tract_driver.SetCensusTractDirectory(census_tract_dir)


def ConfigureNlcdDriver(nlcd_dir=None, cache_size=None):
  """Configure the NLCD driver.

  Inputs:
    nlcd_dir: if specified, changes the NLCD Data default directory.
    cache_size:  if specified, change the NLCD tile cache size.
  Note: The memory usage is about cache_size * 50MB.

  """
  if nlcd_dir is not None:
    nlcd_driver.SetTerrainDirectory(nlcd_dir)
  if cache_size is not None:
    nlcd_driver.SetCacheSize(cache_size)


def PpaCreationModel(devices, pal_records):
  """Create a PPA Polygon based on the PAL Records and Device Information
  Args:
    devices: (List) A list containing device information.
    pal_records: (List) A list containing pal records.
  Returns:
     A GeoJSON Dictionary of PPA Polygon
  """
  # TODO: Add Validation for Inputs
  pool = futures.ProcessPoolExecutor(multiprocessing.cpu_count())
  # Create Contour for each CBSD
  device_polygon = pool.map(_GetPolygon, devices)
  # Create Union of all the CBSD Contours and Check for hole
  # after Census Tract Clipping
  contour_union = ops.cascaded_union(device_polygon)
  ppa_polygon = _ClipPpaByCensusTract(contour_union, pal_records)
  return _ConvertToGeoJson(utils.PolyWithoutSmallHoles(ppa_polygon))
