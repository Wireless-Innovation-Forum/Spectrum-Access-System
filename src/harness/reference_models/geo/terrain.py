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

"""Terrain driver for access to USGS 1 arcsecond DEM (Digital Elevation Model) data.

Original data available at: https://nationalmap.gov/3DEP/.
"""

#
# This module uses the 1" USGS 3DEP data, and assumes that:
# - the data has been stored in 1x1 degree float32 ('GridFloat') format
# - stored with file name <*nXXwYYY*.flt> where XX and YYY are the latitude
#   and longitude of the northwest corner of the tiles
# - there is a standard 6-pixel overlap between tiles
# The terrain tiles are stored in the directory referenced by:
#     CONFIG.GetTerrainDir()

import numpy as np
import os
import time
import threading

from reference_models.geo import tiles
from reference_models.geo import vincenty
from reference_models.geo import CONFIG


_RADIUS_EARTH_METERS = 6378.e3 # Mean radius of the Earth in km
_NUM_PIXEL_OVERLAP = 6 # Number of pixel overlap in tiles
_TILE_BASE_DIM = 3600
_TILE_DIM = _TILE_BASE_DIM + 2 * _NUM_PIXEL_OVERLAP # Dimension of a tile
_TILES_KEYS = tiles.NED_TILES

class TerrainDriver:
  """TerrainDriver class to retrieve elevation data.

  Keeps a LRU cache of most recent needed tiles.
  For best performance it is best to:
   - group request in neighboring regions so that tiles eviction is reduced
   - set the cache_size to the appropriate value for the region size.
  One tile being 1x1 degrees typically covers around 110km x 90km in continental US.

  Attributes:
    cache_size (int): maximum number of tiles cached in memory.
      Memory usage is about 50MB per tile.
    stats (|tile.TileStats|): a tile statistic counter.

  Typical usage:
    # Initialize driver
    driver = TerrainDriver(cache_size=8)

    # Get the altitude in one or several locations
    altitudes = driver.GetTerrainElevation(lat, lon, do_interp=True)

    # Get profile between 2 location with target resolution 30m
    its_profile = driver.TerrainProfile(lat1, lon1, lat2, lon2,
                                        target_res_meters=30, max_points=1501)

    # Compute the HAAT(Height above average terrain) for a given point
    haat = driver.ComputeNormalizedHaat(lat, lon)

    # Manage driver statistics. Useful to understand/optimize cache usage/size
    driver.stats.Report()  # simple statistic reporting
    driver.stats.Reset()   # reset the statistic counter
  """
  def __init__(self, terrain_directory=None, cache_size=8):
    self.SetTerrainDirectory(terrain_directory)
    self.SetCacheSize(cache_size)
    # Keep a small tile cache, LRU fashion
    self._tile_cache = {}
    self._tile_lru = {}
    self.stats = tiles.TileStats('ned')
    self._lock = threading.Lock()
    self.do_flat = False

  def SetTerrainDirectory(self, terrain_directory):
    """Configures the terrain data directory."""
    self._terrain_dir = terrain_directory
    if self._terrain_dir is None:
      self._terrain_dir = CONFIG.GetTerrainDir()

  def SetFlatEarthMode(self, do_flat=False):
    """Sets the driver in flat-earth mode.

    This is an option to always return zero altitude, to be used for testing
    and debugging. Not to be used in normal operations.

    Inputs:
      do_flat (bool): if True, the driver always return altitude 0 everywhere.
    """
    self.do_flat = do_flat

  def SetCacheSize(self, cache_size):
    """Configures the cache size."""
    if cache_size < 1: cache_size = 1
    self.cache_size = cache_size

  def _CacheLruUpdate(self, key):
    """Updates the cache LRU."""
    self._tile_lru[key] = time.time()

  def GetTile(self, ilat, ilon):
    """Returns a given tile as a 2D array, or None if unmanaged tile.

    This routine manages the tile cache.
    For tiles not in the database, returns None.
    If a tile in the database cannot be read, raises an exception.

    Inputs:
      ilat, ilon (int): integer coordinates of NW corner.

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

      # Load a tile in memory and manage the cache.
      encoding = '%c%02d%c%03d' % (
          'sn'[ilat >= 0], abs(ilat),
          'we'[ilon >= 0], abs(ilon))

      tile_name1 = 'usgs_ned_1_' + encoding + '_gridfloat_std.flt'
      tile_name2 = 'float' + encoding + '_1_std.flt'
      tile_name = (tile_name1
                   if os.path.isfile(os.path.join(self._terrain_dir, tile_name1))
                   else tile_name2)

      try:
        self._tile_cache[key] = np.fromfile(
            os.path.join(self._terrain_dir, tile_name),
            dtype=np.float32).reshape(_TILE_DIM, _TILE_DIM)
      except IOError:
        raise IOError('NED Tile (%d,%d) not found.' % (ilat, ilon))

      # Check cache size and evict oldest
      if len(self._tile_cache) > self.cache_size:
        key_to_evict = min(self._tile_lru, key=self._tile_lru.get)
        self._tile_cache.pop(key_to_evict)
        self._tile_lru.pop(key_to_evict)
      self._CacheLruUpdate(key)
      self.stats.UpdateForTileLoad(ilat, ilon)

      return self._tile_cache[key]

  def GetTerrainElevation(self, lat, lon, do_interp=True):
    """Retrieves the elevation for one or several points.

    This function is vectorized for efficiency.

    Inputs:
      lat, lon (scalar or iterables such as list or ndarray): coordinates of
        points to read (degrees).
      do_interp (bool): if True, the elevation is bilinearly interpolated.

    Returns:
      the terrain elevation(s) as:
        - a scalar if the input point is scalar.
        - a ndarray of elevations, if the input lat/lon are iterables.
    """
    is_scalar = np.isscalar(lat)
    lat = np.atleast_1d(lat)
    lon = np.atleast_1d(lon)

    ilat = np.ceil(lat)
    ilon = np.floor(lon)
    alt = np.zeros(len(lat))

    if self.do_flat:
      return alt[0]+10 if is_scalar else alt+10

    # Find the coordinates of the lat/lon in the tile file,
    # in floating point units.
    float_x = _NUM_PIXEL_OVERLAP + _TILE_BASE_DIM * (lon - ilon)
    float_y = _NUM_PIXEL_OVERLAP + _TILE_BASE_DIM * (ilat - lat)
    if do_interp:
      # Compensate for the half-pixel offset of the center from the edge.
      float_x -= 0.5
      float_y -= 0.5
      # Bilinear interpolation
      xm = np.floor(float_x).astype(int)
      xp = xm + 1
      ym = np.floor(float_y).astype(int)
      yp = ym + 1
      # Calculate the areas used for weighting
      alpha_x, alpha_y = (float_x-xm), (float_y-ym)
      area_xm_ym = alpha_x * alpha_y
      area_xm_yp = alpha_x * (1-alpha_y)
      area_xp_yp = (1-alpha_x) * (1-alpha_y)
      area_xp_ym = (1-alpha_x) * alpha_y
    else:
      ix = float_x.astype(int)
      iy = float_y.astype(int)

    # Find iteratively the subsets on the same tile
    # Use a complex number to pack the lat lon because
    # np.unique with axis option supported only on recent numpy
    # It would be:
    #  ilatlon = np.column_stack((ilat, ilon))
    #  unique_ilatlon = np.unique(ilatlon, axis=0)
    ilatlon = ilat + 1j*ilon
    unique_ilatlon = np.unique(ilatlon)
    for key in unique_ilatlon:
      tile_cache = self.GetTile(key.real, key.imag)
      if tile_cache is None:
        # Nothing to set, all values already at 0
        continue

      idx = np.where(ilatlon == key)[0]
      if do_interp:
        ymxm = tile_cache[ym[idx], xm[idx]]
        ymxp = tile_cache[ym[idx], xp[idx]]
        ypxm = tile_cache[yp[idx], xm[idx]]
        ypxp = tile_cache[yp[idx], xp[idx]]
        ymxm[ymxm < -900] = 0.
        ymxp[ymxp < -900] = 0.
        ypxm[ypxm < -900] = 0.
        ypxp[ypxp < -900] = 0.

        # Weight each of the four grid points by the opposite area
        alt[idx] = (area_xm_ym[idx] * ypxp + area_xm_yp[idx] * ymxp
                    + area_xp_yp[idx] * ymxm + area_xp_ym[idx] * ypxm)
      else:
        # Use the elevation of the nearest point
        alt[idx] = tile_cache[iy[idx], ix[idx]]

    if not do_interp:
      alt[alt < -900] = 0.

    return alt[0] if is_scalar else alt

  def TerrainProfile(self, lat1, lon1, lat2, lon2,
                     target_res_meter=-1,
                     target_res_arcsec=1,
                     do_interp=True,
                     max_points=-1):
    """Returns the terrain profile between two points.

    The path is calculated using Vincenty method for obtaining the geodesic
    between the 2 points. The profile is returned at equally spaced points
    along the geodesic as close as possible of the target resolution.
    The target resolution can be either passed in meters, or in arcseconds
    (in which case it is converted to an equivalent resolution at equator).

    Inputs:
      lat1, lon1: coordinates of starting point (in degrees).
      lat2, lon2: coordinates of final point (in degrees).
      target_res_meter: target resolution between points (in meters).
        If unspecified, uses 'target_res_arcsec' instead.
      target_res_arcsec: target resolution between 2 point (in arcsec).
        Only used if 'target_res_meter' unspecified.
      do_interp: if True (default), use bilinear interpolation on terrain data.
      max_points: if positive, resolution extended if number of points is beyond
                  this number.

    Returns:
      an elevation profile in the ITS format as an array:
         elev[0] = number of terrain points - 1 (i.e., number of intervals)
         elev[1] = distance between sample points (meters)
         elev[2]...elev[npts+1] = Terrain elevation (meters)
    """

    if target_res_meter < 0:
      target_res_meter = _RADIUS_EARTH_METERS * np.radians(target_res_arcsec/3600.)

    # Distance between end points (m)
    dist, _, _ = vincenty.GeodesicDistanceBearing(lat1, lon1, lat2, lon2)
    dist *= 1000.

    num_points = np.ceil(dist/float(target_res_meter)) + 1
    if max_points > 0 and num_points > max_points:
      num_points = max_points
    if num_points < 2:
      num_points = 2

    resolution = dist / float(num_points-1)
    lats, lons = vincenty.GeodesicSampling(lat1, lon1, lat2, lon2, num_points)
    elev = [num_points-1, resolution]
    elev.extend(self.GetTerrainElevation(lats, lons, do_interp))
    return elev

  def ComputeNormalizedHaat(self, lat, lon):
    """Computes normalized HAAT (Height Above Average Terrain).

    Args:
      lat, lon: point coordinates (in degrees).

    Returns:
      a tuple of
        the HAAT for an antenna at height 0 above ground level.
        the terrain altitude at given location
    """
    radial_angles = np.linspace(0, 360, 8., endpoint=False)
    distances_km = np.linspace(3, 16, 50)
    all_lat = [lat]
    all_lon = [lon]
    for bearing in radial_angles:
      lats, lons, _ = vincenty.GeodesicPoints(lat, lon, distances_km, bearing)
      all_lat.extend(lats)
      all_lon.extend(lons)

    all_lat = np.array(all_lat)
    all_lon = np.array(all_lon)
    altitudes = self.GetTerrainElevation(all_lat, all_lon)
    return altitudes[0] - np.mean(altitudes[1:]), altitudes[0]
