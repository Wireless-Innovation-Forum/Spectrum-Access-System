#    Copyright 2020 SAS Project Authors. All Rights Reserved.
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
"""Driver for reading USGS population raster map.

Obtaining the data:
   - See https://www.sciencebase.gov/catalog/item/57753ebee4b07dd077c70868
   - Download pden2010_block.zip
   - Install it in default location `Spectrum-Access-Systems/data/pop/`.

Typical usage:

  # Method 1: Explicit data loading
  # - Initialize raster.
  driver = UsgsPopDriver(usgs_pop_directory)

  # - Load full data in memory.
  driver.LoadRaster()
  #   .. or load only block of interest in memory.
  driver.LoadRaster((lat_min, lon_min, lat_max, lon_max)

  # - Now read population density for one or a sequence of points.
  density = driver.GetPopulationDensity(latitudes, longitudes)

  # Method 2: Lazy loading
  # - Initialize raster.
  driver = UsgsPopDriver(usgs_pop_directory, lazy_load=True)

  # - Directly read population density for one or a sequence of points.
  #   Loading happens automatically as needed
  density = driver.GetPopulationDensity(latitudes, longitudes)

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import glob
import os

import numpy as np
from osgeo import gdal
from osgeo import osr

gdal.UseExceptions()

# The default pop dir
DEFAULT_POP_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               '..', '..', '..', 'data', 'pop', 'pden2010_block')


class UsgsPopDriver(object):
  """USGS  Population Raster driver.

  This class manages the reading of population raster data provided by USGS
  at: https://www.sciencebase.gov/catalog/item/57753ebee4b07dd077c70868
  """

  def __init__(self, pop_directory=None, lazy_load=False):
    """Initializes the driver.

    Args:
      pop_directory: The directory holding the USGS population raster. If None,
        use the default location.
      lazy_load: If True, then lazy population loading done (as needed).
    """
    self.lazy_load = lazy_load
    self.fully_loaded = False
    if not pop_directory:
      pop_directory = DEFAULT_POP_DIR
    tiff_path = glob.glob(os.path.join(pop_directory, '*.tif'))
    if not tiff_path:
      raise ValueError('No TIFF file name in directory: %s' % pop_directory)
    self._tiff_path = tiff_path[0]
    self._raster_info = _RasterInfo(self._tiff_path)
    self._raster = np.zeros((self._raster_info.height, self._raster_info.width),
                            dtype=np.uint16)
    dataset = gdal.Open(self._tiff_path)
    raster_band = dataset.GetRasterBand(1)
    self._block_xsize, self._block_ysize = raster_band.GetBlockSize()
    dataset = None
    self._raster_mask = np.zeros(
        (self._raster_info.height // self._block_ysize + 1,
         self._raster_info.width // self._block_xsize + 1),
        dtype=np.bool)

  def LoadRaster(self, box=None):
    """Load raster in memory.

    Args:
      box: A (lat_min, lon_min, lat_max, lon_max) bounding box. If None, the
        full raster is loaded in memory.
    """
    dataset = gdal.Open(self._tiff_path)
    raster_band = dataset.GetRasterBand(1)
    row_min, row_max = 0, dataset.RasterYSize-1
    col_min, col_max = 0, dataset.RasterXSize-1
    if box:
      row_se, col_se = self._raster_info.Indexes(box[0], box[1])
      row_ne, col_ne = self._raster_info.Indexes(box[2], box[1])
      row_sw, col_sw = self._raster_info.Indexes(box[0], box[3])
      row_nw, col_nw = self._raster_info.Indexes(box[2], box[3])
      row_min = max(min(row_ne, row_nw), 0)
      row_max = min(max(row_se, row_sw), dataset.RasterYSize-1)
      col_min = max(min(col_se, col_ne), 0)
      col_max = min(max(col_sw, col_nw), dataset.RasterXSize-1)

    b_y_min = int(row_min // self._block_ysize)
    b_y_max = int(row_max // self._block_ysize)
    b_x_min = int(col_min // self._block_xsize)
    b_x_max = int(col_max // self._block_xsize)
    for b_y in range(b_y_min, b_y_max+1):
      for b_x in range(b_x_min, b_x_max+1):
        if self._raster_mask[b_y, b_x]:
          continue
        yoff, xoff = b_y * self._block_ysize, b_x * self._block_xsize
        win_xsize, win_ysize = raster_band.GetActualBlockSize(b_x, b_y)
        block = raster_band.ReadAsArray(
            xoff=xoff, yoff=yoff, win_xsize=win_xsize, win_ysize=win_ysize)
        self._raster[yoff:yoff+win_ysize,
                     xoff:xoff+win_xsize] = np.minimum(block, 65500)
        self._raster_mask[b_y, b_x] = True

    if box is None:
      self.all_loaded = True
    # Close the file
    dataset = None

  def GetPopulationDensity(self, latitudes, longitudes):
    """Retrieves the population density on locations.

    Args:
      latitudes: A sequence of points latitudes.
      longitudes: A sequence of points longitudes.

    Returns:
      The population density (pop/km2) as a ndarray (dtype=int16).
    """
    if len(latitudes) == 0:
      return 0
    latitudes = np.asarray(latitudes)
    longitudes = np.asarray(longitudes)
    densities = np.zeros(len(latitudes), dtype=np.int16)
    rows, cols = self._raster_info.Indexes(latitudes, longitudes)
    idx_inside = np.where((rows >= 0) &
                          (cols >= 0) &
                          (rows < self._raster.shape[0]) &
                          (cols < self._raster.shape[1]))[0]
    if self.lazy_load and not self.fully_loaded:
      lat_min, lat_max = np.min(latitudes), np.max(latitudes)
      lon_min, lon_max = np.min(longitudes), np.max(longitudes)
      self.LoadRaster((lat_min, lon_min, lat_max, lon_max))

    densities[idx_inside] = self._raster[rows[idx_inside], cols[idx_inside]]
    return densities


# This class contains metadata about a particular tile and can be used to
# quickly determine the indexes of a lat/lon coordinate within the tile.
class _RasterInfo:
  """Manages raster information.

  Typical usage:

    # Initialize tile metadata
    raster_info = _RasterInfo(raster_path)

    # Check if a point is covered by the tile
    inside = raster_info.IsWithinTile(latitude=38, longitude=-122)

    # Get the indexes to access the data for a point
    row, col = raster_info.Indexes(latitude=38, longitude=-122)
  """

  def __init__(self, raster_path):
    """Initializes the raster Information.

    Args:
      raster_path: The raster path.
    """
    self.raster_path = raster_path
    dataset = gdal.Open(raster_path)
    self.width = dataset.RasterXSize
    self.height = dataset.RasterYSize
    # Gets the gdal geo transformation tuples
    # gdal_version = gdal.__version__
    self._txf = dataset.GetGeoTransform()
    # self._inv_txf = gdal.InvGeoTransform(self._txf)[1]
    self._inv_txf = gdal.InvGeoTransform(self._txf)
    # Gets the transformation from lat/lon to coordinates
    wgs84_ref = osr.SpatialReference()
    wgs84_ref.ImportFromEPSG(4326)   # WGS84
    sref = osr.SpatialReference()
    sref.ImportFromWkt(dataset.GetProjection())
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
    dataset = None

  def Indexes(self, latitudes, longitudes):
    """Retrieves indexes of points in original projected grid.

    Args:
      latitudes: A sequence of points latitudes.
      longitudes: A sequence of points longitudes.

    Returns:
      A tuple (idx_row, idx_col) of ndarrays specifying the index in the
        raster matrix.
    """
    res = self._transform.TransformPoints(
        np.column_stack((longitudes, latitudes)))
    res = list(zip(*res))
    x, y = np.array(res[0]), np.array(res[1])
    idx_col = self._inv_txf[0] + self._inv_txf[1] * x + self._inv_txf[2] * y
    idx_row = self._inv_txf[3] + self._inv_txf[4] * x + self._inv_txf[5] * y
    return idx_row.astype(int), idx_col.astype(int)
