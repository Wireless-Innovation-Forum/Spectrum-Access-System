#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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

import numpy as np
from reference_models.antenna.antenna import GetStandardAntennaGains
from reference_models.geo import vincenty
from reference_models.propagation.wf_hybrid import CalcHybridPropagationLoss

THRESHOLD = -96
RX_HEIGHT = 6


def _CalculatePropLossForEachPoint(install_param, latitude, longitude):
  db_loss = np.zeros(len(latitude), dtype=np.float64)
  for index, lat_lon in enumerate(zip(latitude, longitude)):
    lat, lon = lat_lon
    # driver = nlcd.NlcdDriver(cache_size=8)
    # code = driver.GetLandCoverCodes(lat, lon)
    # region_type = nlcd.GetRegionType(code)
    # TODO: Remove Default Region Type
    db_loss[index] = CalcHybridPropagationLoss(install_param['latitude'],
                                               install_param['longitude'],
                                               install_param['height'],
                                               lat, lon, RX_HEIGHT,
                                               install_param['indoorDeployment'],
                                               region="RURAL").db_loss

  prop = 10.0 ** (db_loss / 10.0)
  return prop


def _HammingFilter(x, window_len=15):
  s = np.r_[x[-(window_len / 2):], x, x[0:window_len / 2]]
  w = np.hamming(window_len)
  y = np.convolve(w / w.sum(), s, mode='valid')
  return y


def _ComputeCnt(antenna_gain, path_loss):

  pass


def _GetPolygon(device):
  install_param = device['installationParam']
  # Get all the Function Partials
  # Compute all the Points in 0-359 every 200m upto 40km
  distance = np.arange(0.2, 40.2, 0.2)
  latitude, longitude, _ = zip(*[vincenty.GeodesicPoints(install_param['latitude'],
                                                         install_param['longitude'],
                                                         distance, azimuth)
                                 for azimuth in np.arange(0, 10)])
  # Compute the Gain for all Direction
  antenna_gain = GetStandardAntennaGains(np.arange(0, 10),
                                         install_param['antennaAzimuth']
                                         if 'antennaAzimuth' in install_param.keys() else None,
                                         install_param['antennaBeamwidth'],
                                         install_param['antennaGain'])
  # Compute the Path Loss
  path_loss = [_CalculatePropLossForEachPoint(install_param, lat, lon)
               for lat, lon in zip(latitude, longitude)]
  # Compute the Contour based on Gain and Path Loss Comparing with Threshold
  cnt = _ComputeCnt(antenna_gain, path_loss)
  # Smoothing Contour using Hamming Filter
  # smooth_cnt = _HammingFilter(cnt)

  # # Generating lat, lon for Contours
  # lat = []
  # lon = []
  # for c, az in zip(cnt, range(0, 360)):
  #   l, lo, az = GeodesicPoint(install_param['latitude'],
  #                             install_param['longitude'],
  #                             c, float(az))
  #   lat.append(l)
  #   lon.append(lo)
  # polygon = geojson.Polygon([zip(lon, lat)])
  # return polygon


def PpaCreationModel(devices):
  """Create a PPA Polygon based on the PAL Records and Device Information
  Args:
    devices: (List) A list containing device information.
    pal_records: (List) A list containing pal records.
  Returns:
     A GeoJSON Dictionary of PPA Polygon
   Note: Device Records must contain eirpCapability in installationParam Object
   and Pal Records must contain fipsCode
  """
  # pool = Pool(multiprocessing.cpu_count())
  # polygon_device = \
  #   pool.map(_GetPolygon, devices)
  [_GetPolygon(d) for d in devices]
  # polygons = map(convert_shape, polygon_device)
  # contour_union = cascaded_union(polygons)
  #
  # return convert_to_polygon(clip_ppa_census_tracts(pal_records,
  #                                                 contour_union))
