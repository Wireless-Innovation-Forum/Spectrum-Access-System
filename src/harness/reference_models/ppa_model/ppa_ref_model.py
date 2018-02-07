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

from multiprocessing import Pool, cpu_count

import geojson
import numpy as np
from shapely.geometry import shape
from shapely.ops import cascaded_union
from reference_models.antenna.antenna import GetStandardAntennaGains
from reference_models.geo import vincenty
from reference_models.propagation.wf_hybrid import CalcHybridPropagationLoss

THRESHOLD = -96
RX_HEIGHT = 6


def _CalculatePropLossForEachPointAndCnt(install_param, antenna_gain, latitude, longitude):
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
  index_cond, _ = np.where(install_param['eirpCapability'] - prop + antenna_gain > THRESHOLD)
  return index_cond.shape[0] / 5


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
  cnt = [_CalculatePropLossForEachPointAndCnt(install_param, gain, lat, lon)
         for lat, lon, gain in zip(latitude, longitude, antenna_gain)]
  # Compute the Contour based on Gain and Path Loss Comparing with Threshold
  # Smoothing Contour using Hamming Filter
  smooth_cnt = _HammingFilter(cnt)

  # Generating lat, lon for Contours
  cnt_lat, cnt_lon, _ = [vincenty.GeodesicPoint(install_param['latitude'],
                                                install_param['longitude'], cn, az)
                         for cn, az in zip(smooth_cnt, range(0, 360))]
  polygon = geojson.Polygon([zip(cnt_lat, cnt_lon)])
  return shape(polygon).buffer(0)


def PpaCreationModel(devices, pal_records):
  """Create a PPA Polygon based on the PAL Records and Device Information
  Args:
    devices: (List) A list containing device information.
    pal_records: (List) A list containing pal records.
  Returns:
     A GeoJSON Dictionary of PPA Polygon
   Note: Device Records must contain eirpCapability in installationParam Object
   and Pal Records must contain fipsCode
  """
  pool = Pool(cpu_count())
  polygon_device = pool.map(_GetPolygon, devices)
  #TODO: Add Area Check for Holes and Census Tract Clipping
  # Create Union of all the CBSD Contours and Check for hole
  #contour_union = cascaded_union(polygon_device)

  #return convert_to_polygon(clip_ppa_census_tracts(pal_records,
  #                                                 contour_union))
