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

from concurrent.futures import ProcessPoolExecutor as Pool
import multiprocessing
from utils import *
from compute import load_partials
from functools import partial
from src.harness.util import getRandomLatLongInPolygon
import random

THRESHOLD = 0.5


def __compute_points_gain_prop(device):
  pool = Pool(multiprocessing.cpu_count())
  install_param = device['installationParam']
  # Get all the Function Partials
  great_circle_partial, antenna_gain_partial, \
  prop_partial, cnt_partial = load_partials(install_param, THRESHOLD)
  # Compute all the Points in 0-359 every 200m upto 40km
  points = pool.map(great_circle_partial, range(0, 360))
  # Compute the Gain for all Direction
  antenna_gain = pool.map(antenna_gain_partial, range(0, 360))
  # Compute the Path Loss
  path_loss = pool.map(prop_partial, enumerate(points))
  # Compute the Contour based on Gain and Path Loss Comparing with Threshold
  cnt = pool.map(cnt_partial, zip(antenna_gain, path_loss))
  # Smoothing Contour using Hamming Filter
  cnt = smooth(np.asarray(list(cnt)))

  # Generating lat, lon for Contours
  contour_lat_lon = great_circle(latitude=install_param['latitude'],
                                 longitude=install_param['longitude'],
                                 distance=cnt, azimuth=range(0, 360))

  polygon = geojson.Polygon([zip(contour_lat_lon['longitude'],
                                 contour_lat_lon['latitude'])])
  return polygon


def ppa_creation_model(device_filenames, pal_record_filenames,
                       pal_user_id, pal_low_frequency, pal_high_frequency):
  """Create a PPA Polygon based on the PAL Records and Device Information
  Args:
    device_filenames: (List) A list containing device filenames.
    pal_record_filenames: (List) A list containing pal record filenames.
    pal_user_id: (String) Pal User Id to be used in all Pal Records. 
    pal_low_frequency: (Number) Pal Primary Low Frequency to be assigned 
    to all Pal Records. 
    pal_high_frequency: (Number) Pal Primary Hight Frequency to be assigned 
    to all Pal Records. 
  Returns:
     A Tuple containing PPA Polygon in GeoJSON, a List of 
     Consistent PAL Record and Device List
  """
  devices, pal_records = load_files(device_filenames, pal_record_filenames,
                                   pal_user_id, pal_low_frequency, pal_high_frequency)
  pool = Pool(multiprocessing.cpu_count())
  polygon_device = \
    pool.map(__compute_points_gain_prop, devices)
  polygons = map(convert_shape, polygon_device)
  contour_union = cascaded_union(polygons)

  return convert_to_polygon(clip_ppa_census_tracts(pal_records,
                                                   contour_union)), \
         pal_records, devices
