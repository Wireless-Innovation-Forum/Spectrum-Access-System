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

"""Returns the ITU surface refractivity for a specified lat/lon.

Standalone execution:
  python refractivity.py lat lng
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import math
import os
import sys

import numpy as np

from reference_models.geo import CONFIG


class RefractivityIndexer:
  """RefractivityIndexer class to retrieve refractivity for given world location.

  It retrieves the nearest four refractivity points from ITU data file with
  1.5 degree grid, and interpolates bilinearly between those points.

  Typical usage:
    refractor = RefractivityIndexer()
    r = refractor.Refractivity(19.66, -155.55)
  """
  def __init__(self, datafile_or_dir=None):
    self.ConfigureDataFile(datafile_or_dir, do_load=False)
    self._num_lat_rows = 121  # Number of latitude rows in the data file
    self._num_lon_cols = 241  # Number of longitude columns in the data file
    self._lat_start = 90.0  # Latitude corresponding to first row of file (deg)
    self._lon_start = 0.0  # Longitude corresponding to first column of file (deg)
    self._delta_lat = self._delta_lon = 1.5  # Spacing between lat/lon rows/columns (deg)

  def ConfigureDataFile(self, datafile_or_dir, do_load=True):
    """Configure the refractivity data file.

    Inputs:
      datafile_or_dir: the data path or directory.
         If directory, then the datafile is the standard 'n050.txt'.
         If None, then use the standard database location from CONFIG.py.
      do_load: if set (default), load the data, otherwise do lazy loading.
    """
    self._datafile = datafile_or_dir
    if self._datafile is None:
      self._datafile = os.path.join(CONFIG.GetItuDir(), 'n050.txt')
    elif os.path.isdir(self._datafile):
      self._datafile = os.path.join(self._datafile, 'n050.txt')
    self._data = None
    if do_load:
      self._data = np.loadtxt(self._datafile)

  def Refractivity(self, lat, lon):
    """Returns ITU refractivity for the specified lat/lon.

    Inputs:
      lat, lon : the coordinates of a point.

    Returns:
      the sea level refractivity on that point.
    """
    if self._data is None:
      self._data = np.loadtxt(self._datafile)
      logging.info('Loaded refractivity data from %s' % self._datafile)

    if lon < 0:
      lon = lon + 360.0

    row = (self._lat_start - lat) / self._delta_lat
    col = (lon - self._lon_start) / self._delta_lon

    # Bilinear interpolation on values
    irow = int(math.floor(row))
    icol = int(math.floor(col))

    r00 = self._data[irow,   icol]
    r11 = self._data[irow+1, icol+1]
    r01 = self._data[irow,   icol+1]
    r10 = self._data[irow+1, icol]

    alpha_r, alpha_c = row - irow, col - icol
    refractivity = ( r11 * alpha_r * alpha_c +
                     r00 * (1-alpha_r) * (1-alpha_c) +
                     r01 * (1-alpha_r) * alpha_c +
                     r10 * alpha_r * (1-alpha_c) )

    return refractivity

if __name__ == '__main__':
  indx = RefractivityIndexer()
  r = indx.Refractivity(float(sys.argv[1]), float(sys.argv[2]))
  print('Surface Refractivity (n-units) = %s' % r)
