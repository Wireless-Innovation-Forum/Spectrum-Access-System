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

"""Utility routines for running tests.
"""

import glob
import random
import numpy as np
import os
import zipfile

from reference_models.geo import vincenty

# Generate random pair of lat,lng within distance
def MakeLatLngPairs(n_pairs,
                    dmin_meters=0, dmax_meters=150000.,
                    lat_min=32.8, lat_max=41.0,
                    lng_min=-117.0, lng_max=-80):
  """Generates random pairs of points within distance.

  Each pair of points are  within a bounding box, and at at
  controllable distance from each other.

  Inputs:
    n_pairs:  number of pairs to generate.
    d_min_meters, d_max_meters: range of distance for each pair of
        points (default 0 to 150km)
    lat_min, lat_max, lng_min, lng_max: bounding box that contain
        pair of points
        By default uses a bounding box fully included in continental
        US border (but not covering all US).

  Returns:
    an array of tuple (lat1,lng1, lat2, lng2) of size n_pairs
  """

  pair_points = []
  while len(pair_points) < n_pairs:
    lat1 = random.uniform(lat_min, lat_max)
    lng1 = random.uniform(lng_min, lng_max)
    bearing = random.uniform(0., 360.)
    d = random.uniform(dmin_meters, dmax_meters)
    lat2, lng2, backaz = vincenty.GeodesicPoint(lat1, lng1, d, bearing)
    if (lat2 < lat_min or lat2 > lat_max or
        lng2 < lng_min or lng2 > lng_max):
      continue
    pair_points.append((lat1, lng1, lat2, lng2))

  return pair_points

# Managing test directory with zipped files
def UnzipTestDir(directory):
  """Unzip all zip file in a directory.

  Inputs:
    directory: target directory

  Returns:
    list of unzipped files
  """
  unzip_files = []
  for zfile_name in glob.glob(os.path.join(directory, "*.zip")):
    zfile = zipfile.ZipFile(zfile_name, 'r')
    unzip_files.extend(zfile.namelist())
    # Do not unzip if already there
    do_unzip = False
    for zf in zfile.namelist():
      if not os.path.exists(os.path.join(directory, zf)):
        do_unzip = True
    if do_unzip:
      zfile.extractall(directory)

  return unzip_files

# Delete files
def RemoveFiles(directory, file_list):
  """Remove all specified files in specified directory.

  Inputs:
    directory: target directory
    file_list: list of files to remove
  """
  for f in file_list:
    os.remove(os.path.join(directory, f))
