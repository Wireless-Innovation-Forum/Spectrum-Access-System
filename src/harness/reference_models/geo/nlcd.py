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

"""Driver for access to NLCD (National Land Cover) data.

Original NLCD codes from USGS are described at:
  https://www.mrlc.gov/nlcd11_leg.php

For WinnForum use, only 3 classification are used:
 - URBAN: code 24 (Developed High Density) and 23 (Developed Medium Density)
 - SUBURBAN: code 22 (Developed Low Density)
 - RURAL: everything else
"""
#
# This module uses the 1" NLCD data obtained by resampling the original
# National Land Cover Database at multiple of 1".
# Because most use of the NLCD in Winnforum propagation is done effectively
# at multiple of 1", there is no loss of information, and the approach
# should be equivalent to projecting on the fly lat/lon coordinates to the
# Albert projection used by original USGS NLCD geodata and reading directly
# from those files.
# See the src/data/ directory for the scripts doing the regridding.

import enum
import numpy as np
import os
import time
import threading

from reference_models.geo import tiles
from reference_models.geo import CONFIG


# Note: need to use IntEnum to have comparable enum values to numeric values
# since they need to be compared to integer values returned by data drivers.
class LandCoverCodes(enum.IntEnum):
  """Defines the land cover codes from USGS NLCD database.

  Original NLCD codes from USGS are described at:
    https://www.mrlc.gov/nlcd11_leg.php
  """
  UNDEFINED = 0
  # Water
  OPEN_WATER = 11
  PERENNIAL_SNOW = 12
  # Developed
  DEVELOPED_OPEN = 21
  DEVELOPED_LOW = 22
  DEVELOPED_MEDIUM = 23
  DEVELOPED_HIGH = 24
  # Barren
  BARREN_LAND = 31
  # Forest
  DECIDUOUS_FOREST = 41
  EVERGREEN_FOREST = 42
  MIXED_FOREST = 43
  # Shrubland
  DWARF_SCRUB = 51
  SHRUB_SCRUB = 52
  # Herbaceous
  GRASSLAND = 71
  SEDGE = 72
  LICHENS = 73
  MOSS = 74
  # Planted/ Cultivated
  PASTURE_HAY = 81
  CULTIVATED_CROPS = 82
  # Wetlands
  WOODY_WETLANDS = 90
  EMERGENT_HERBACEOUS_WETLANDS = 95


# Tiles dimension
_TILE_DIM = 3600
_TILES_KEYS = tiles.NLCD_TILES


def GetRegionType(code):
  """Get the region type for a code.

  Inputs:
    lat,lon: coordinates of a point.

  Returns:
    the region type among 'URBAN', 'SUBURBAN', 'RURAL'
    """
  if code == LandCoverCodes.DEVELOPED_LOW:
    return 'SUBURBAN'
  elif (code == LandCoverCodes.DEVELOPED_MEDIUM or
        code == LandCoverCodes.DEVELOPED_HIGH):
    return 'URBAN'

  return 'RURAL'


class NlcdDriver:
  """TerrainDriver class to retrieve land cover data.

  This driver works on 1-degrees unprojected NLCD tile database.
  Keeps a LRU cache of most recent needed tiles.
  For best performance it is best to:
   - group request in neighboring regions so that tiles eviction is reduced
   - set the cache_size to the appropriate value for the region size.

  Typical usage:
    # Initialize driver
    driver = NlcdDriver(cache_size=8)

    # Get the land cover code in one location
    code = driver.GetLandCoverCode(lat, lon)

    # Get the region type of a code
    region_type = GetRegionType(code)

    # Get the region type of a zone defined by list of points
    region_type = driver.RegionNlcdVote(points)

    # Manage driver statistics. Useful to understand/optimize cache usage/size
    driver.stats.Report()  # simple statistic reporting
    driver.stats.Reset()   # reset the statistic counter
  """
  def __init__(self, nlcd_directory=None, cache_size=8):
    self.SetNlcdDirectory(nlcd_directory)
    self.SetCacheSize(cache_size)
    # Keep a small tile cache, LRU fashion
    self._tile_cache = {}
    self._tile_lru = {}
    self.stats = tiles.TileStats('nlcd')
    self._lock = threading.Lock()

  def SetNlcdDirectory(self, nlcd_directory):
    """Configures the NLCD data directory."""
    self._nlcd_dir = nlcd_directory
    if self._nlcd_dir is None:
      self._nlcd_dir = CONFIG.GetLandCoverDir()

  def SetCacheSize(self, cache_size):
    """Configures the cache size."""
    if cache_size < 1: cache_size = 1
    self.cache_size = cache_size

  def _CacheLruUpdate(self, key):
    """Updates the cache LRU."""
    self._tile_lru[key] = time.time()

  def GetTile(self, ilat, ilon):
    """Returns a given tile as a 2D array, or None if unmanaged tile.

    For tiles not in the database, returns None.
    If a tile in the database cannot be read, raises an exception.

    Input:
      ilat, ilon (int): coordinate of NW corner.

    Raises:
      IOError: if an expected tile cannot be read
    """
    key = (ilat, ilon)

    with self._lock:
      # Manage the cases of mem-loaded or unmanaged tiles.
      try:
        tile = self._tile_cache[key]
        self._CacheLruUpdate(key)
        return tile
      except KeyError:
        if key not in _TILES_KEYS:
          return None

      # Load a tile in memory and manage the cache
      encoding = '%c%02d%c%03d' % (
          'sn'[ilat >= 0], abs(ilat),
          'we'[ilon >= 0], abs(ilon))

      tile_name1 = 'nlcd_' + encoding + '_ref.int'
      tile_name2 = 'nlcd_' + encoding + '.int'
      tile_name = (tile_name1
                   if os.path.isfile(os.path.join(self._nlcd_dir, tile_name1))
                   else tile_name2)

      try:
        self._tile_cache[key] = np.fromfile(
            os.path.join(self._nlcd_dir, tile_name),
            dtype=np.uint8).reshape(_TILE_DIM, _TILE_DIM)
      except IOError:
        raise IOError('NLCD Tile (%d,%d) not found.' % (ilat, ilon))

      # Check cache size and evict oldest
      if len(self._tile_cache) > self.cache_size:
        key_to_evict = min(self._tile_lru, key=self._tile_lru.get)
        self._tile_cache.pop(key_to_evict)
        self._tile_lru.pop(key_to_evict)
      self._CacheLruUpdate(key)
      self.stats.UpdateForTileLoad(ilat, ilon)

      return self._tile_cache[key]

  def GetLandCoverCodes(self, lat, lon):
    """Retrieves the NLCD value of one or several points.

    This function is vectorized for efficiency.

    Inputs:
      lat,lon (scalar or iterables such as list or ndarray): coordinates of
        points to read (degrees).

    Returns:
      the NLCD land cover code(s) as:
        - a scalar if the input point is scalar.
        - a ndarray of codes if the input lat/lon are iterables
    """
    is_scalar = np.isscalar(lat)
    lat = np.atleast_1d(lat)
    lon = np.atleast_1d(lon)

    ilat = np.ceil(lat - 0.5/3600.)
    ilon = np.floor(lon + 0.5/3600.)
    codes = np.zeros(len(lat), dtype=np.uint8)

    ix = (3600. * (lon - ilon) + 0.5).astype(int)
    iy = (3600. * (ilat - lat) + 0.5).astype(int)

    ilatlon = ilat + 1j*ilon
    unique_ilatlon = np.unique(ilatlon)
    for key in unique_ilatlon:
      tile_cache = self.GetTile(key.real, key.imag)
      if tile_cache is None:
        # Nothing to set, all values already at 0
        continue
      idx = np.where(ilatlon == key)[0]
      codes[idx] = tile_cache[iy[idx], ix[idx]]

    if is_scalar:
      return codes[0]
    elif isinstance(lat, np.ndarray):
      return codes

  def RegionNlcdVote(self, points, out_forbid=True):
    """Vote on most common NLCD in a region.

    According to WinnForum spec R2-SGN-04.

    Inputs:
      points: list of (lat,lon) tuples defining a region
      out_forbid: If True (default), will raise an exception
                  if some points have land cover code 0 (meaning
                  they are out of bounds of the NLCD).
    Returns:
      the region type among 'RURAL', 'URBAN', 'SUBURBAN'

    Raises:
      ValueError if request point outside of NLCD effective bounds
      (ie when code=0) AND out_forbid is True.
    """
    avg_code = 0
    lat, lon = zip(*points)
    codes = self.GetLandCoverCodes(lat, lon)
    codes22 = np.where(codes==LandCoverCodes.DEVELOPED_LOW)[0]
    codes23 = np.where(codes==LandCoverCodes.DEVELOPED_MEDIUM)[0]
    codes24 = np.where(codes==LandCoverCodes.DEVELOPED_HIGH)[0]
    if out_forbid:
      codes0 = np.where(codes==0)[0]
      if len(codes0):
        raise ValueError('Request NLCD vote in area with undefined code.')

    avg_code = (1.0 * len(codes22) + 2.0 * (len(codes23) + len(codes24))) / len(points)
    if avg_code < 2./3.:
      return 'RURAL'
    elif avg_code <= (1 + 1./3.):
      return 'SUBURBAN'
    else:
      return 'URBAN'
