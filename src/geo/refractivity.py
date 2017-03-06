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

# Returns the ITU surface refractivity given a specified lat/lon.
# It retrieves the nearest four refractivity points from a data
# file with 1.5 degree data points and interpolates bilinearly within
# those points.
#
# Example use:
#   refr = RefractivityIndexer($dir)    
#   r = refr.Refractivity(19.66, -155.55)
#   r = refr.Refractivity(39.2, -77.1)
#   ...

import math
import numpy
import os
import sys

class RefractivityIndexer:
  def __init__(self, directory):
    datafile = os.path.join(directory, 'n050.txt')
    self.NLATROWS = 121  # Number of latitude rows in the data file
    self.NLONCOLS = 241  # Number of longitude columns in the data file
    self.LATSTART = 90.0 # Latitude corresponding to first row of file (deg)
    self.LONSTART = 0.0 # Longitude corresponding to first column of file (deg)
    self.DLAT = self.DLON = 1.5 # Spacing between lat/lon rows/columns (deg)
    self.DATA = numpy.loadtxt(datafile)
    print 'Loaded refractivity data from %s' % datafile

  def Refractivity(self, lat, lon):
    """
    Returns ITU refractivity for the specified lat/lon.

    Andrew Clegg
    January 2017
    """

    if lon < 0.0:
      lon = lon + 360.0

    irow = float((self.LATSTART - lat)/self.DLAT)
    icol = float((lon - self.LONSTART)/self.DLON)
    # print 'Got irow=%s, icol=%s' % (irow, icol)

    # bilinear interpolation on values
    irowl = int(math.floor(irow))
    icoll = int(math.floor(icol))
    irowh = irowl + 1
    icolh = icoll + 1

    r1 = self.DATA[irowl, icoll]
    r2 = self.DATA[irowh, icolh]
    r3 = self.DATA[irowl, icolh]
    r4 = self.DATA[irowh, icoll]
    # print 'Got values ', r1, r2, r3, r4

    refractivity = (((irow - float(irowl)) * (icol - float(icoll))) * r2 + 
                    ((float(irowh) - irow) * (float(icolh) - icol)) * r1 + 
                    ((float(irowh) - irow) * (icol - float(icoll))) * r3 + 
                    ((irow - float(irowl)) * (float(icolh) - icol)) * r4)

    return refractivity 

if __name__ == '__main__':
  dir = os.path.dirname(os.path.realpath(__file__))
  rootDir = os.path.dirname(os.path.dirname(dir))
  ituDir = os.path.join(os.path.join(rootDir, 'data'), 'itu')

  indx = RefractivityIndexer(ituDir)

  r = indx.Refractivity(float(sys.argv[1]), float(sys.argv[2]))
  print 'Surface Refractivity (n-units) = %s' % r


