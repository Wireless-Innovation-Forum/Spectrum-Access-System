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

"""Returns the ITU climate zone given a specified lat/lon.

Standalone execution:
  python tropoclim.py lat lng
"""

import logging
import os
import sys
import numpy as np

from reference_models.geo import CONFIG


class ClimateIndexer:
  """ClimateIndexer class to retrieve climate codes for given world location.

  The given lat/lon is rounded to the nearest half-degree point and that
  coordinate is used for obtaining the climate value.

  Usage:
    climater = ClimateIndexer()
    code = climater.TropoClim(19.66, -155.55)
    print code, ClimateZoneName(code)
  """
  def __init__(self, datafile_or_dir=None):
    self.ConfigureDataFile(datafile_or_dir, do_load=False)

    self._num_lat_rows = 360  # Number of latitude rows in the data file
    self._num_lon_cols = 720  # Number of longitude columns in the data file
    self._lat_start = 89.75 # Latitude corresponding to first row of file (deg)
    self._lon_start = -179.75 # Longitude corresponding to first column of file (deg)
    self._delta_lat = self._delta_lon = 0.5 # Spacing between lat/lon rows/columns (deg)
    self._data = None

  def ConfigureDataFile(self, datafile_or_dir, do_load=True):
    """Configure the refractivity data file.

    Inputs:
      datafile_or_dir: the data path or directory.
         If directory, then the datafile is the standard 'n050.txt'.
         If None, then use the standard database location from CONFIG.py.
      do_load: if set (default), load the data, otherwise do lazy loading.
    """
    self.datafile = datafile_or_dir
    if self.datafile is None:
      self.datafile = os.path.join(CONFIG.GetItuDir(), 'TropoClim.txt')
    elif os.path.isdir(self.datafile):
      self.datafile = os.path.join(self.datafile, 'TropoClim.txt')
    self._data = None
    if do_load:
      self._data = np.loadtxt(self.datafile, dtype=np.int)

  def TropoClim(self, lat, lon):
    """Returns ITU climate zone for the specified lat/lon.

    Climate codes are the following:
      1: 'Equatorial'
      2: 'Continental Subtropical'
      3: 'Maritime Tropical'
      4: 'Desert'
      5: 'Continental Temperate'
      6: 'Maritime Temperate, Over Land'
      7: 'Maritime Temperate, Over Sea'

    Note that 'Sea' climate is returned as value 7, which differs
    from original TropoClim file encoding at 0.
    """
    if self._data is None:
      self._data = np.loadtxt(self.datafile, dtype=np.int)
      logging.info('Loaded climate data from %s' % self.datafile)

    irow = int((self._lat_start - lat)/self._delta_lat + 0.5)
    icol = int((lon - self._lon_start)/self._delta_lon + 0.5)

    climate = self._data[irow, icol]
    if climate == 0:
      climate = 7

    return climate

_ZONE_NAMES = [
    'Unknown',
    'Equatorial',
    'Continental Subtropical',
    'Maritime Tropical',
    'Desert',
    'Continental Temperate',
    'Maritime Temperate, Over Land',
    'Maritime Temperate, Over Sea'
]

def ClimateZoneName(zone):
  """Returns the name of a given climate code
  """
  if zone > 7: zone = 0
  return _ZONE_NAMES[zone]

if __name__ == '__main__':
  indx = ClimateIndexer()
  clim = indx.TropoClim(float(sys.argv[1]), float(sys.argv[2]))
  print 'Climate zone = %d' % clim
  print ' (%s)' % ClimateZoneName(clim)
