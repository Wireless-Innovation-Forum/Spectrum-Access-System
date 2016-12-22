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

import gdal
import math
import numpy
import osr
import os
import sys
import time

# This class contains metadata about a particular tile and can be used to quickly
# determine whether a lat/lng coordinate is within the tile.
class NlcdTileInfo:
  def __init__(self, filename):
    self.filename = filename

    ds = gdal.Open(filename)
    self.txf = ds.GetGeoTransform()
    self.inv_txf = gdal.InvGeoTransform(self.txf)

    wgs84_ref = osr.SpatialReference()
    wgs84_ref.ImportFromEPSG(4326)
    sref = osr.SpatialReference()
    sref.ImportFromWkt(ds.GetProjection())

    self.transform = osr.CoordinateTransformation(wgs84_ref, sref)
    self.inv_transform = osr.CoordinateTransformation(sref, wgs84_ref)

    print 'x', ds.RasterXSize
    print 'y', ds.RasterYSize
    print self.txf
    self.coord_bounds = [
      self.txf[0],     # upper left x
      self.txf[3],     # upper left y
      self.txf[1] * ds.RasterXSize + self.txf[0],  # lower right x
      self.txf[5] * ds.RasterYSize + self.txf[3]   # lower right y
    ]
    print self.coord_bounds

    ul = self.inv_transform.TransformPoint(self.coord_bounds[0],
                                           self.coord_bounds[1])
    lr = self.inv_transform.TransformPoint(self.coord_bounds[2],
                                           self.coord_bounds[3])
    self.max_lng = max(ul[0], lr[0])
    self.max_lat = max(ul[1], lr[1])
    self.min_lng = min(ul[0], lr[0])
    self.min_lat = min(ul[1], lr[1])

    print 'loaded tile %s' % filename
    print 'bounds', self.min_lng, self.max_lng, self.min_lat, self.max_lat
    print 'txf', self.txf

    # Close file
    ds = None

  def WithinTile(self, lat, lng):
    print 'Compare %f %f to %f %f' % (lat, lng, self.min_lng, self.min_lat)
    # Fast latlng bounds check
    if (lng >= self.max_lng or
        lng <= self.min_lng or
        lat >= self.max_lat or
        lat <= self.min_lat):
      print 'quick out'
      return False

    # Check with transform
    coord = self.TileCoords(lat, lng)
    print 'compare ', coord, ' with ', self.coord_bounds
    if (coord[0] >= self.coord_bounds[0] and
        coord[0] <= self.coord_bounds[2] and
        coord[1] >= self.coord_bounds[3] and
        coord[1] <= self.coord_bounds[1]):
      print 'IN!'
      return True

    return False

  def TileCoords(self, lat, lng):
    return self.transform.TransformPoint(lng, lat)

  def IndexCoords(self, lat, lng):
    coord = self.TileCoords(lat, lng)
    x = self.inv_txf[0] + self.inv_txf[1] * coord[0] + self.inv_txf[2] * coord[1]
    y = self.inv_txf[3] + self.inv_txf[4] * coord[0] + self.inv_txf[2] * coord[1]
    return [x, y]

class NlcdIndexer:
  def __init__(self, directory, lru_size=10):
    print 'init NLCD indexer for %s' % directory
    self.directory = directory
    files = os.listdir(self.directory)
    files.sort()
    self.nlcd_file = {}
    for f in files:
      filename = os.path.join(directory, f)
      if f.endswith('.img'):
        # skip the AK file if present -- contents are split into a *_tiles directory
        if f.startswith('ak_nlcd_2011'):
          continue
        self.nlcd_file[filename] = NlcdTileInfo(filename)
      if f.endswith('_tiles_xxx') and os.path.isdir(filename):
        tilepath = os.path.join(directory, f)
        tile_files = os.listdir(tilepath)
        for ft in tile_files:
          if ft.endswith('.img'):
            filename = os.path.join(tilepath, ft)
            self.nlcd_file[filename] = NlcdTileInfo(filename)

    # tile_cache holds maps of NlcdTileInfo to numpy arrays with data for that tile
    self.tile_cache = {}
    self.tile_lru = {}
    self.tile_lru_size = lru_size

  def LoadTileForLatLng(self, lat, lng):
    for t in self.tile_cache:
      if t.WithinTile(lat, lng):
        return

    print 'Searching tiles...'
    for fn in self.nlcd_file:
      t = self.nlcd_file[fn]
      if t.WithinTile(lat, lng):
        print 'Found within tile %s' % fn
        dataset = gdal.Open(fn)
        self.tile_cache[t] = dataset.ReadAsArray().astype(numpy.byte)
        self.tile_lru[t] = time.clock()

        if len(self.tile_lru) > self.tile_lru_size:
          mint = 0
          mink = ''
          for k in self.tile_lru.keys():
            if self.tile_lru[k] > mint:
              mint = self.tile_lru[k]
              mink = k
          print 'Evicting tile %s' % k.filename
          del self.tile_cache[k]
          del self.tile_lru[k]

        # close the file
        dataset = None
        return

    raise Exception('No tile found for lat lng %f %f' % (lat, lng))

  def NlcdCode(self, lat, lng):
    print 'Code for %f, %f' % (lat, lng)
    self.LoadTileForLatLng(lat, lng)
    for t in self.tile_cache:
      if t.WithinTile(lat, lng):
        index = t.IndexCoords(lat, lng)
        a = self.tile_cache[t]
        self.tile_lru[t] = time.clock()

        iln = round(index[1])
        ipx = round(index[0])
        print 'iln=', iln
        print 'ipx=', ipx

        return a[iln][ipx]

    raise Exception('No NLCD data for lat lng %f, %f' % (lat, lng))

# If run directly, takes command line lat lng arguments and prints the NLCD code.
if __name__ == '__main__':
  dir = os.path.dirname(os.path.realpath(__file__))
  rootDir = os.path.dirname(os.path.dirname(dir))
  nlcdDir = os.path.join(os.path.join(rootDir, 'data'), 'nlcd')
  indx = NlcdIndexer(nlcdDir)

  print 'NLCD=%d' % indx.NlcdCode(float(sys.argv[1]), float(sys.argv[2]))

