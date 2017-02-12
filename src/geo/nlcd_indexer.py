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
import osgeo.gdal
import sys
import time

import land_use

# This class contains metadata about a particular tile and can be used to quickly
# determine whether a lat/lng coordinate is within the tile.
class NlcdTileInfo:
  def __init__(self, filename):
    self.filename = filename

    ds = gdal.Open(filename)
    self.txf = ds.GetGeoTransform()
    
    # Handles difference in return from gdal.InvGeoTransform between gdal version 1 and 2
    gdal_version = osgeo.gdal.__version__
    if gdal_version[0] == '1':
      self.inv_txf = gdal.InvGeoTransform(self.txf)[1]
    else:
      self.inv_txf = gdal.InvGeoTransform(self.txf)

    wgs84_ref = osr.SpatialReference()
    wgs84_ref.ImportFromEPSG(4326)
    sref = osr.SpatialReference()
    sref.ImportFromWkt(ds.GetProjection())
    self.width = ds.RasterXSize
    self.height = ds.RasterYSize

    self.transform = osr.CoordinateTransformation(wgs84_ref, sref)
    self.inv_transform = osr.CoordinateTransformation(sref, wgs84_ref)

    #print self.txf
    self.coord_bounds = [
      self.txf[0],     # upper left x
      self.txf[3],     # upper left y
      self.txf[0] + self.txf[1] * ds.RasterXSize + self.txf[2] * ds.RasterYSize,  # lower right x
      self.txf[3] + self.txf[4] * ds.RasterXSize + self.txf[5] * ds.RasterYSize   # lower right y
    ]

    # Find the corners of the tile for examining lat/lng to find intersection with tile.
    corners = []
    for x in [0, ds.RasterXSize]:
      for y in [0, ds.RasterYSize]:
        corners.append([self.txf[0] + self.txf[1] * x + self.txf[2] * y,
                        self.txf[3] + self.txf[4] * x + self.txf[5] * y])

    # TODO: does this account for 180-crossing tiles?
    self.max_lat = -100
    self.min_lat = 100
    self.max_lng = -500
    self.min_lng = 500
    for c in corners:
      p = self.inv_transform.TransformPoint(c[0], c[1])
      if p[0] > self.max_lng:
        self.max_lng = p[0]
      if p[0] < self.min_lng:
        self.min_lng = p[0]
      if p[1] > self.max_lat:
        self.max_lat = p[1]
      if p[1] < self.min_lat:
        self.min_lat = p[1]

    # Close file
    ds = None

  def WithinTile(self, lat, lng):
    #if abs(lng - self.max_lng) < 2 and abs(lat - self.max_lat) < 2:
    #  print 'Compare %f %f to %f %f' % (lat, lng, self.min_lat, self.min_lng)
    #  print self.filename

    # Fast latlng bounds check
    if (lng > self.max_lng or
        lng < self.min_lng or
        lat > self.max_lat or
        lat < self.min_lat):
      #print 'quick out'
      return False

    # Check with transform
    coord = self.IndexCoords(lat, lng)
    if (coord[0] >= 0 and coord[0] <= float(self.width) and
        coord[1] >= 0 and coord[1] <= float(self.height)):
      return True
      
    return False

  def TileCoords(self, lat, lng):
    return self.transform.TransformPoint(lng, lat)

  def IndexCoords(self, lat, lng):
    coord = self.TileCoords(lat, lng)
    #print 'IndexCoords for %s %s' % (lat, lng)
    #print '  Index coords ', coord
    #print '  bounds', self.min_lat, self.max_lat, self.min_lng, self.max_lng
    #print '  coord_bounds=', self.coord_bounds
    #print '  inv_txf=', self.inv_txf
    #print '  txf=', self.txf
    
    x = self.inv_txf[0] + self.inv_txf[1] * coord[0] + self.inv_txf[2] * coord[1]
    y = self.inv_txf[3] + self.inv_txf[4] * coord[0] + self.inv_txf[5] * coord[1]
      
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
      if f.endswith('_tiles') and os.path.isdir(filename):
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

    #print 'Searching tiles...'
    for fn in self.nlcd_file:
      t = self.nlcd_file[fn]
      if t.WithinTile(lat, lng):
        #print 'Found within tile %s' % fn
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
    #print 'Code for %f, %f' % (lat, lng)
    self.LoadTileForLatLng(lat, lng)
    for t in self.tile_cache:
      if t.WithinTile(lat, lng):
        # print 'Found in tile %s' % t.filename
        index = t.IndexCoords(lat, lng)
        a = self.tile_cache[t]
        self.tile_lru[t] = time.clock()

        iln = round(index[1])
        ipx = round(index[0])
        #print 'iln=', iln
        #print 'ipx=', ipx

        return a[iln][ipx]

    raise Exception('No NLCD data for lat lng %f, %f' % (lat, lng))

# If run directly, takes command line lat lng arguments and prints the NLCD code.
if __name__ == '__main__':
  dir = os.path.dirname(os.path.realpath(__file__))
  rootDir = os.path.dirname(os.path.dirname(dir))
  nlcdDir = os.path.join(os.path.join(rootDir, 'data'), 'nlcd')
  indx = NlcdIndexer(nlcdDir)

  code = indx.NlcdCode(float(sys.argv[1]), float(sys.argv[2]))
  print 'NLCD=%d' % code
  print 'Land use = %s' % land_use.NlcdLandCategory(code)

  if code == 11:
    print '  (open water)'

