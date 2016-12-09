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

# This script contains a class implementing a NED elevation indexing function.
# The class is passed a directory containing USGS NED elevation GridFLOAT
# data files and uses them to lookup elevations. Interpolation method is
# bilinear. The class uses an LRU system to manage degree tiles, making
# repeated lookups in the same geographical area very fast.

import gdal
import math
import numpy
import os
import re
import sys
import time

class NedIndexer:
  def __init__(self, directory, lru_size=10):
    self.directory = directory
    files = os.listdir(self.directory)
    files.sort()
    self.latlng_file = {}
    for f in files:
      if f.endswith('.flt'):
        m = re.match('(.*?)([ns])(\d+)([ew])(\d+)(.*)', f)
        if m:
          lat = m.group(3)
          lng = m.group(5)
          # print 'found %s %s for file %s' % (lat, lng, f)
          if m.group(2) == 's':
            lat = lat * -1
          if m.group(4) == 'w':
            lng = str(int(lng) * -1)
          k = '%s.%s' % (lat, lng)
          # print 'found %s for file %s' % (k, f)
          if k in self.latlng_file and m.group(1) == 'float':
            continue
          self.latlng_file[k] = os.path.join(directory, f)
    # latlng_file now has a list of the correct FLT sources for each degree tile.

    # tile_cache will hold numpy arrays of the specific tiles as they are read in
    # by the indexer.
    self.tile_cache = {}
    self.tile_lru = {}
    self.tile_lru_size = lru_size

    # txf will contain the inverse geo transform functions for specific tiles as
    # they are created by reading the tiles
    self.txf = {}

  # This method loads a specific geo tile which includes the lat/lng provided.
  # It manages the LRU such that a new tile replaces the least-recently-used tile
  # if needed to remain under the size constraint.
  def LoadTileForLatLng(self, lat, lng):
    latf = int(math.ceil(lat))
    lngf = int(math.floor(lng))
    k = '%s.%s' % (latf, lngf)
    if k in self.tile_cache:
      return

    filename = self.latlng_file[k]
    print 'Loading tile %s from %s' % (k, filename)
    dataset = gdal.Open(filename)
    # Store the inverse geo transform which will map (lat, lng) to array indices
    # in this tile.
    tx = dataset.GetGeoTransform()
    self.txf[k] = gdal.InvGeoTransform(tx)

    self.tile_cache[k] = dataset.ReadAsArray().astype(numpy.float)
    self.tile_lru[k] = time.clock()

    # evict a tile if there are more than tile_lru_size elements in the cache
    if len(self.tile_lru) > self.tile_lru_size:
      mint = 0
      mink = ''
      for k in self.tile_lru.keys():
        if self.tile_lru[k] > mint:
          mint = self.tile_lru[k]
          mink = k
      print 'Evicting tile %s' % k
      del self.tile_cache[k]
      del self.tile_lru[k]

    # close the file
    dataset = None

  # Returns elevation in meters at the given lat,lng. The result uses
  # bilinear interpolation for values between the sample points of the
  # elevation raster data.
  def Elevation(self, lat, lng):
    self.LoadTileForLatLng(lat, lng)

    latf = int(math.ceil(lat))
    lngf = int(math.floor(lng))
    k = '%s.%s' % (latf, lngf)
    #print 'lat, lng = %f, %f' % (lat, lng)

    tx = self.txf[k]
    ipx = tx[0] + tx[1] * lng + tx[2] * lat
    iln = tx[3] + tx[4] * lng + tx[5] * lat

    a = self.tile_cache[k]
    self.tile_lru[k] = time.clock()
    #print 'Retrieving (%s, %s) from (%f, %f) from tile %s' % (lat, lng, ipx, iln, k)

    ilnf = int(math.floor(iln))
    ipxf = int(math.floor(ipx))
    ilnc = int(math.ceil(iln))
    ipxc = int(math.ceil(ipx))
    if ilnc == ilnf:
      ilnc = ilnc + 1
    if ipxc == ipxf:
      ipxc = ipxc + 1
    eff = a[ilnf][ipxf]
    efc = a[ilnf][ipxc]
    ecf = a[ilnc][ipxf]
    ecc = a[ilnc][ipxc]
    #print 'Elevations: %f, %f, %f, %f' % (eff, efc, ecf, ecc)

    a1 = (iln - float(ilnf)) * (ipx - float(ipxf))
    a2 = (iln - float(ilnf)) * (float(ipxc) - ipx)
    a3 = (float(ilnc) - iln) * (ipx - float(ipxf))
    a4 = (float(ilnc) - iln) * (float(ipxc) - ipx)
    #print 'Areas: %f, %f, %f, %f' % (a1, a2, a3, a4)

    # interpolation multiplies each corner by the opposite area. Since the area
    # is normalized to index lookups, the total area is 1.
    elev = a1*ecc + a2*efc + a3*ecf + a4*eff

    return elev
    
# If run directly, takes command line arguments for lat and lng and prints elevation.
if __name__ == '__main__':
  dir = os.path.dirname(os.path.realpath(__file__))
  rootDir = os.path.dirname(os.path.dirname(dir))
  nedDir = os.path.join(os.path.join(rootDir, 'data'), 'ned')

  indx = NedIndexer(nedDir)

  # e.g. python ned_indexer.py 61.549 -136.571
  print indx.Elevation(float(sys.argv[1]), float(sys.argv[2]))

