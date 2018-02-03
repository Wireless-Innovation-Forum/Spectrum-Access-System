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

from math import log10
from functools import partial
import numpy as np
from utils import great_circle
from reference_models.antenna.antenna import GetStandardAntennaGains
from reference_models.geo import nlcd
from reference_models.propagation.wf_hybrid import CalcHybridPropagationLoss
RX_HEIGHT = 6

def prop_model(**kwargs):
  """Placeholder to Call Propagation Model, will be removed when it is moved to reference model"""
  pass


def cbsd_antenna_gain(**kwargs):
  """Placeholder to Call CBSD Antenna Model, will be removed when it is checked in"""
  pass


def __prop_model_rel(cbsd_lat, cbsd_lon,cbsd_height, cbsd_indoor, points):
  driver = nlcd.NlcdDriver(cache_size=8)
  latitude, longitude = points
  code = driver.GetLandCoverCodes(latitude, longitude)
  region_type = nlcd.GetRegionType(code)
  # reliability = np.arange(0.01, 1.00, 0.01)
  db_loss_namedtuple = CalcHybridPropagationLoss(cbsd_lat, cbsd_lon, cbsd_height, latitude, longitude, RX_HEIGHT, cbsd_indoor=cbsd_indoor, reliability = -1, region = region_type)
  # print db_loss_namedtuple
  db_loss = db_loss_namedtuple.db_loss
  # print db_loss
  prop = 10.0 ** (db_loss / 10.0)
  # return 10 * log10(sum(prop) / float(len(prop)))
  return 10 * log10(float(prop))


def __antenna_gain_model(azimuth, beamwidth,antenna_gain, az):
  return GetStandardAntennaGains(az, azimuth, beamwidth, antenna_gain)


def __compute_prop(install_param, points_index_tuple):
  index, points = points_index_tuple
  prop_model_rel_partial = partial(__prop_model_rel,
								   install_param['latitude'],
								   install_param['longitude'],
                                   install_param['height'],
                                   install_param['indoorDeployment'])
  props = map(prop_model_rel_partial, zip(points['latitude'], points['longitude']))
  return props


def __compute_great_circle(install_param, azimuth):
  return great_circle(latitude=install_param['latitude'],
					  longitude=install_param['longitude'],
					  distance=np.arange(0.2, 40.2, 0.2),
					  azimuth=azimuth)


def __compute_cnt(install_param, threshold, gain_prop_tuple):
  gain, path_loss = gain_prop_tuple
  cnt = 0
  for pl in path_loss:
	if (install_param['eirpCapability'] - pl) + gain > threshold:
	  cnt += 1
  return cnt / 5


def load_partials(install_param, threshold):
  c_g_c_p = partial(__compute_great_circle, install_param)
  a_g_p = partial(__antenna_gain_model,
				  install_param['antennaAzimuth'],
				  install_param['antennaBeamwidth'],
                  install_param['antennaGain'])
  c_p_p = partial(__compute_prop, install_param)
  c_c_p = partial(__compute_cnt, install_param, threshold)
  return c_g_c_p, a_g_p, c_p_p, c_c_p
