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

"""Provides a driver for reading original USGS NLCD (National Land Cover) database.

This driver works with the original untiled files provided by USGS, typically found
in https://www.mrlc.gov/data. Currently 2011 and 2001 NLCD data:
   nlcd_2011_landcover_2011_edition_2014_10_10.XXX
   ak_nlcd_2011_landcover_2011_xxx.XXX
   hi_landcover_wimperv_9-30-08_se5.XXX
   pr_landcover_wimperv_10-28-08_se5.XXX

Typical usage:

  # Create driver - One of following options:
  #   - with auto subtile loading (size 1x1 degrees) and LRU caching.
  driver = NlcdOriginDriver(usgs_nlcd_file, data_mode=8, tile_size=(1,1))

  #   - With manual loading of rectangle box.
  driver = NlcdOriginDriver(usgs_nlcd_file, data_mode=0)
  driver.CacheTileInBox(lat_min, lat_max, lon_min, lon_max)

  #   - Full tile load - Warning as it requires 32GB transient RAM.
  driver = NlcdOriginDriver(usgs_nlcd_file, data_mode=-1)

  # Now read NLCD codes for one or a list/array of points
  codes = driver.GetLandCoverCodes(lats, lons)
"""

import gdal
import logging
import numpy as np
import os
import osgeo.gdal
import osr
import sys
import time

gdal.UseExceptions()

# The following line is needed on Windows OS
if os.name == 'nt':
  os.putenv('GDAL_DATA', 'C:\\Program Files (x86)\\GDAL\\gdal-data')

#if sys.version.startswith('3'):
#  raise ValueError('Currently unsupported with Python3..')


class NlcdOriginDriver(object):
  """Original NCLD driver.

  This class manages reading the NLCD data in its original form, as provided
  by USGS (ie in Albers Conical projection).

  Several modes are supported:
    data_mode=-1: cached the full NLCD database (requires 16GB permanent
                  memory and 32GB transient) for conus file.
    data_mode=0:  user defined loading with CacheTileInBox().
    data_mode>0:  auto loading as small subtiles with LRU cache.
  """
  def __init__(self, nlcd_file,
               data_mode=0,
               tile_size=(1, 1)):
    """Initializes the original NLCD driver.

    Inputs:
      nlcd_file: File holding the original NLCD data ('.img' format).
      data_mode: Internal data mode (default: 0).
                 If -1, load the full NLCD in memory (32GB transient RAM required).
                 If 0, load of working sub-tile in memory managed by user.
                 If > 0, automatic loading of sub-tiles, each NxM degrees with
                   value specifying size of small tiles managed in LRU fashion.
      tile_size: Tuple (N,M) for size (in degrees) of small tiles in lat/lon
                 directions (in degrees) when using data_mode > 0.
    """
    # Keep a small tile cache, LRU fashion
    self.data_mode = data_mode
    self._tile_size = tile_size
    self._tile_cache = {}
    self._tile_lru = {}
    self._use_default_tile = False

    # Read the tile info
    if not os.path.exists(nlcd_file):
      raise Exception('The file is not found %s' % nlcd_file)

    self.img_path = nlcd_file

    self.tinfo = NlcdTileInfo(self.img_path)
    if self.data_mode <= 0:
      self._use_default_tile = True
      if self.data_mode == -1:
        self.CacheTileInBox()

  def UnloadTile(self, key=None):
    """Unloads a given tile by key.

    By default unload the default tile, ie either the full NLCD if using
    cache_size=-1, or the manually user loaded tile, if any.
    """
    if key in self._tile_cache:
      del self._tile_cache[key]

  def CacheTileInBox(self, lat_min=None, lat_max=None,
                     lon_min=None, lon_max=None,
                     key=None):
    """Caches NLCD within bounding box.

    If no bounding box specified, cache the full NLCD (up to 32GB transient RAM
    needed for CONUS NLCD file).
    The internal cache element is a tuple (box, tile_cache)
        - box is a tuple (idx_row, idx_col) of the offset of the NW point
          of the returned ticompared to the original tile NW point.
          To be used to offset the self.tinfo.Indexes() routines.
        - tile_cache is a ndarray of shape (num_rows, num_cols).
          All data outside bounds of original tile are set to zero

    Inputs:
      lat_min, lat_max :  extend of the box in latitude (degrees).
      lon_min, lon_max :  extend of the box in longitude (degrees).
      key: storage key in cache

    Returns:
      the cache element (box, tile_cache) (see above) if the tile is within bounds
      or None if outside bounds
    """
    # Case of full file reading
    if None in [lat_min, lat_max, lon_min, lon_max]:
      logging.info('Reading full NLCD image')
      dataset = gdal.Open(self.img_path)
      self._tile_cache[None] = (
          (0, 0),
          dataset.ReadAsArray().astype(np.uint8))
      dataset = None  # Close file
      return self._tile_cache[None]

    # Find the minimal bounding box in original projection
    row_nw, col_nw = self.tinfo.Indexes(lat_max, lon_min)
    row_ne, col_ne = self.tinfo.Indexes(lat_max, lon_max)
    row_sw, col_sw = self.tinfo.Indexes(lat_min, lon_min)
    row_se, col_se = self.tinfo.Indexes(lat_min, lon_max)
    row_min = int(min([row_nw, row_ne, row_sw, row_se]))
    row_max = int(max([row_nw, row_ne, row_sw, row_se]))
    col_min = int(min([col_nw, col_ne, col_sw, col_se]))
    col_max = int(max([col_nw, col_ne, col_sw, col_se]))

    row_offset = row_min
    col_offset = col_min
    nrows = row_max - row_min + 1
    ncols = col_max - col_min + 1
    box = (row_offset, col_offset)
    data = np.zeros((nrows, ncols), dtype=np.uint8)

    # Manage limits in original raster
    orig_row_min = max(0, row_min)
    orig_col_min = max(0, col_min)
    orig_row_max = min(self.tinfo.height - 1, row_max)
    orig_col_max = min(self.tinfo.width - 1, col_max)
    orig_nrows = orig_row_max - orig_row_min + 1
    orig_ncols = orig_col_max - orig_col_min + 1
    new_row_min = max(-row_min, 0)
    new_col_min = max(-col_min, 0)

    # If completely outside, the zero matrix will be stored
    outside = True
    if orig_ncols > 0 and orig_nrows > 0:
      dataset = gdal.Open(self.img_path)
      data[new_row_min:new_row_min + orig_nrows,
           new_col_min:new_col_min + orig_ncols] = dataset.ReadAsArray(
               xoff=orig_col_min, yoff=orig_row_min,
               xsize=orig_ncols, ysize=orig_nrows).astype(np.uint8)
      dataset = None  # Close gdal file
      outside = False

    self._tile_cache[key] = (box, data)
    if outside: return None
    return self._tile_cache[key]

  def _GetKeys(self, lat, lon):
    """Get the tile key for given lat,lon."""
    ilat = np.ceil(lat / self._tile_size[0]) * self._tile_size[0]
    ilon = np.floor(lon / self._tile_size[1]) * self._tile_size[1]
    return (ilat, ilon)

  def _CacheGridTile(self, lat, lon):
    """Cache a small tile holding given point."""
    key = (ilat, ilon) = self._GetKeys(lat, lon)
    lat_min, lat_max = ilat - self._tile_size[0], ilat
    lon_min, lon_max = ilon, ilon + self._tile_size[1]
    # Check cache size and evict oldest
    if len(self._tile_cache) >= self.data_mode:
      key_to_evict = min(self._tile_lru, key=self._tile_lru.get)
      del self._tile_cache[key_to_evict]
      del self._tile_lru[key_to_evict]

    self.CacheTileInBox(lat_min, lat_max, lon_min, lon_max,
                        key)
    self._CacheLruUpdate(key)
    return self._tile_cache[key]

  def _CacheLruUpdate(self, key):
    """Updates the cache LRU."""
    self._tile_lru[key] = time.time()

  def GetLandCoverCodes(self, lat, lon):
    """Retrieves the NLCD value of one or several points.

    Inputs:
      lat,lon: coordinates of points to read (scalar or
               iterable such as list or ndarray).

    Returns:
      the NLCD land cover code of that point,
      or a ndarray of codes for the given points if inputs lat,lon are a ndarray,
      or a list of codes in other iterable cases.
    """
    is_scalar = np.isscalar(lat)
    is_ndarray = isinstance(lat, np.ndarray)
    if is_scalar:
      lat, lon = np.array([lat]), np.array([lon])
    else:
      lat = np.asarray(lat)
      lon = np.asarray(lon)

    codes = np.zeros(len(lat), dtype=np.uint8)

    if self._use_default_tile:  # Full or user defined raster
      irows, icols = self.tinfo.Indexes(lat, lon)
      box, tile = self._tile_cache[None]
      irows -= box[0]
      icols -= box[1]
      idx_inside = np.where((irows >= 0) &
                            (icols >= 0) &
                            (irows < tile.shape[0]) &
                            (icols < tile.shape[1]))[0]
      codes[idx_inside] = tile[irows[idx_inside], icols[idx_inside]]

    else:  # Automatic small tile caching
      ilat, ilon = self._GetKeys(lat, lon)
      irows, icols = self.tinfo.Indexes(lat, lon)

      ilatlon = ilat + 1j*ilon
      unique_ilatlon = np.unique(ilatlon)
      for key in unique_ilatlon:
        try:
          box, tile_cache = self._tile_cache[(key.real, key.imag)]
          self._CacheLruUpdate((key.real, key.imag))
        except:
          box, tile_cache = self._CacheGridTile(key.real, key.imag)

        idx = np.where(ilatlon == key)
        iy = irows[idx] - box[0]
        ix = icols[idx] - box[1]
        codes[idx] = tile_cache[iy, ix]

    if is_scalar:
      return codes[0]
    elif is_ndarray:
      return codes
    else:
      return list(codes)


# This class contains metadata about a particular tile and can be used to quickly
# determine whether a lat/lon coordinate is within the tile.
class NlcdTileInfo:
  """Manages tile metadata.

  Typical usage:

    # Initialize tile metadata
    tinfo = NlcdTileInfo(tile_path)

    # Check if a point is covered by the tile
    inside = tinfo.IsWithinTile(lat=38, lon=-122)

    # Get the indexes to access the data for a point
    row, col = tinfo.Indexes(lat=38, lon=-122)
  """

  def __init__(self, tile_path):
    """Initializes the Tile Information.

    Inputs:
      tile_path: path the tile file.
    """
    self.tile_path = tile_path

    ds = gdal.Open(tile_path)
    self.width = ds.RasterXSize
    self.height = ds.RasterYSize

    # Gets the gdal geo transformation tuples
    gdal_version = osgeo.gdal.__version__
    self._txf = ds.GetGeoTransform()
    if gdal_version[0] == '1':
      self._inv_txf = gdal.InvGeoTransform(self._txf)[1]
    else:
      self._inv_txf = gdal.InvGeoTransform(self._txf)
    # Gets the transformation from lat/lon to coordinates
    wgs84_ref = osr.SpatialReference()
    wgs84_ref.ImportFromEPSG(4326)   # WGS84
    sref = osr.SpatialReference()
    sref.ImportFromWkt(ds.GetProjection())
    if int(osgeo.gdal.__version__[0]) >= 3:
      # Output order has changed in osgeo v3
      wgs84_ref.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
      sref.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    self._transform = osr.CoordinateTransformation(wgs84_ref, sref)
    inv_transform = osr.CoordinateTransformation(sref, wgs84_ref)
    # Find a loose lat/lon bounding box  for quick check without
    # having to do full coordinates transformation
    corners = []
    for x in [0, self.width]:
      for y in [0, self.height]:
        corners.append([self._txf[0] + self._txf[1] * x + self._txf[2] * y,
                        self._txf[3] + self._txf[4] * x + self._txf[5] * y])
    self.max_lat = -100
    self.min_lat = 100
    self.max_lon = -500
    self.min_lon = 500
    for c in corners:
      p = inv_transform.TransformPoint(c[0], c[1])
      if p[0] > self.max_lon:
        self.max_lon = p[0]
      if p[0] < self.min_lon:
        self.min_lon = p[0]
      if p[1] > self.max_lat:
        self.max_lat = p[1]
      if p[1] < self.min_lat:
        self.min_lat = p[1]

    # Close file
    ds = None

  def IsWithinTile(self, lat, lon):
    """Checks if given point is within tile.

    Inputs:
      lat, lon:  Point coordinates (degrees).

    Returns:
      True if inside the tile, False otherwise.
    """
    # Fast latlon bounds check
    if (lon > self.max_lon or
        lon < self.min_lon or
        lat > self.max_lat or
        lat < self.min_lat):
      return False

    # Check after transform to indexes
    idx_row, idx_col = self.Indexes(lat, lon)
    return (idx_col >= 0 and idx_col < self.width and
            idx_row >= 0 and idx_row < self.height)

  def Indexes(self, lat, lon):
    """Computes indexes of point(s) in original projected grid.

    Inputs:
      lat, lon : Coordinate(s) of one or several points (degrees).
                 Can be either scalar or an iterable.
    Returns:
      a tuple of indexes (idx_row, idx_col), where each element is either
        a scalar if single point,
        or a ndarray if ndarray input vectors,
        or a list for other iterable cases.
    """
    if np.isscalar(lat):
      x, y, _ = self._transform.TransformPoint(float(lon), float(lat))
      idx_col = self._inv_txf[0] + self._inv_txf[1] * x + self._inv_txf[2] * y
      idx_row = self._inv_txf[3] + self._inv_txf[4] * x + self._inv_txf[5] * y
      return int(idx_row), int(idx_col)
    else:
      res = self._transform.TransformPoints(np.column_stack((lon, lat)))
      res = list(zip(*res))
      x, y = np.array(res[0]), np.array(res[1])
      idx_col = self._inv_txf[0] + self._inv_txf[1] * x + self._inv_txf[2] * y
      idx_row = self._inv_txf[3] + self._inv_txf[4] * x + self._inv_txf[5] * y
    if isinstance(lat, np.ndarray):
      return idx_row.astype(int), idx_col.astype(int)
    else:
      return list(idx_row.astype(int)), list(idx_col.astype(int))
