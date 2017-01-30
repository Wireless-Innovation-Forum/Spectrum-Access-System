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

# Returns the ITU climate zone given a specified lat/lon.
# It rounds the given lat/lon to the nearest data point in a half-degree
# world data file and returns that climate value.
#
# Example use:
#   climate = ClimateIndexer($dir)    
#   result = climate.TropoClim(19.66, -155.55)
#   result = climate.TropoClim(39.2, -77.1)
#   ...

import numpy
import os
import sys

class ClimateIndexer:
  def __init__(self, directory):
    datafile = os.path.join(directory, 'TropoClim.txt')
    self.NLATROWS = 360  # Number of latitude rows in the data file
    self.NLONCOLS = 720  # Number of longitude columns in the data file
    self.LATSTART = 89.75 # Latitude corresponding to first row of file (deg)
    self.LONSTART = -179.75 # Longitude corresponding to first column of file (deg)
    self.DLAT = self.DLON = 0.5 # Spacing between lat/lon rows/columns (deg)
    self.CLIMATEDATA = numpy.loadtxt(datafile, dtype=numpy.int)
    print 'Loaded climate data from %s' % datafile

  def TropoClim(self, lat, lon):
    """
    Returns ITU climate zone for the specified lat/lon.

    Andrew Clegg
    January 2017
    """

    irow = int((self.LATSTART - lat)/self.DLAT + 0.5)
    icol = int((lon - self.LONSTART)/self.DLON + 0.5)
    
    climate = self.CLIMATEDATA[irow, icol]
    if climate == 0:
      climate = 7

    return climate

  def ClimateZoneName(self, zone):
    if zone == 1:
      return 'Equatorial'
    if zone == 2:
      return 'Continental Subtropical'
    if zone == 3:
      return 'Maritime Tropical'
    if zone == 4:
      return 'Desert'
    if zone == 5:
      return 'Continental Temperate'
    if zone == 6:
      return 'Maritime Temperate, Over Land'
    if zone == 7:
      return 'Maritime Temperate, Over Sea'
    return 'Unknown'

if __name__ == '__main__':
  dir = os.path.dirname(os.path.realpath(__file__))
  rootDir = os.path.dirname(os.path.dirname(dir))
  ituDir = os.path.join(os.path.join(rootDir, 'data'), 'itu')

  indx = ClimateIndexer(ituDir)

  clim = indx.TropoClim(float(sys.argv[1]), float(sys.argv[2]))
  print 'Climate zone = %d' % clim
  print ' (%s)' % indx.ClimateZoneName(clim)


