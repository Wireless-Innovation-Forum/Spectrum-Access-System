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

import logging
import math
import numpy as np
import os
import time

from reference_models.geo import vincenty
from reference_models.geo import CONFIG


_RADIUS_EARTH_METERS = 6378.e3 # Mean radius of the Earth in km
_NUM_PIXEL_OVERLAP = 6 # Number of pixel overlap in tiles
_TILE_BASE_DIM = 3600
_TILE_DIM = _TILE_BASE_DIM + 2 * _NUM_PIXEL_OVERLAP # Dimension of a tile


class TerrainDriver:
  """TerrainDriver class to retrieve elevation data.

  Keeps a LRU cache of most recent needed tiles.

  Typical usage:
    # Initialize driver
    driver = TerrainDriver(cache_size=4)

    # Get the altitude in one or several locations
    altitudes = driver.GetTerrainElevation(lat, lon, do_interp=True)

    # Get profile between 2 location with target resolution 30m
    its_profile = driver.TerrainProfile(lat1, lon1, lat2, lon2,
                                        target_res_meters=30, max_points=1501)
  """
  def __init__(self, terrain_directory=None, cache_size=4):
    self.SetTerrainDirectory(terrain_directory)
    self.SetCacheSize(cache_size)
    # Keep a small tile cache, LRU fashion
    self._tile_cache = {}
    self._tile_lru = {}

  def SetTerrainDirectory(self, terrain_directory):
    """Configures the terrain data directory."""
    self._terrain_dir = terrain_directory
    if self._terrain_dir is None:
      self._terrain_dir = CONFIG.GetTerrainDir()

  def SetCacheSize(self, cache_size):
    """Configures the cache size."""
    if cache_size < 1: cache_size = 1
    self.cache_size = cache_size

  def _CacheLruUpdate(self, key):
    """Updates the cache LRU."""
    self._tile_lru[key] = time.time()

  def _CacheGridTile(self, ilat, ilon):
    """Reads and cache a tile.

    If the file does not exist or cannot be read, it initializes it to all zero.

    Input:
      ilat, ilon: coordinate of NW corner (tile key).

    Returns:
      The tiled cache if ok.
      None if tile cannot be read (a zero tile is still created).
    """
    encoding = '%c%02d%c%03d' % (
        'sn'[ilat >= 0], abs(ilat),
        'we'[ilon >= 0], abs(ilon))

    tile_name1 = 'usgs_ned_1_' + encoding + '_gridfloat_std.flt'
    tile_name2 = 'float' + encoding + '_1_std.flt'

    tile_name = (tile_name1
                 if os.path.isfile(os.path.join(self._terrain_dir, tile_name1))
                 else tile_name2)

    key = (ilat, ilon)
    # Check cache size and evict oldest
    if len(self._tile_cache) >= self.cache_size:
      key_to_evict = min(self._tile_lru, key=self._tile_lru.get)
      del self._tile_cache[key_to_evict]
      del self._tile_lru[key_to_evict]

    self._CacheLruUpdate(key)
    try:
      self._tile_cache[key] = np.fromfile(os.path.join(self._terrain_dir, tile_name),
                                          dtype=np.float32).reshape(_TILE_DIM, _TILE_DIM)
      return self._tile_cache[key]
    except:
      self._tile_cache[key] = np.zeros((_TILE_DIM, _TILE_DIM))
      logging.warning('No terrain file %s. Setting elevations to 0. ' % tile_name)
      return None

  def _GetTerrainElevationPoint(self, lat, lon, do_interp=True):
    """Retrieves the elevation of a given lat/lon.

    Inputs:
      lat,lon: coordinated of point to read.
      do_interp: if True, the elevation is bilinearly interpolated.

    Returns:
      the elevation of the given point.
    """
    ilat = math.ceil(lat)
    ilon = math.floor(lon)
    try:
      tile_cache = self._tile_cache[(ilat, ilon)]
      self._CacheLruUpdate((key.real, key.imag))
    except:
      tile_cache = self._CacheGridTile(ilat, ilon)
      if tile_cache is None:
        return 0.0

    # Find the coordinates of this lat/lon in the tile file,
    # in floating point units.
    float_x = _NUM_PIXEL_OVERLAP + _TILE_BASE_DIM * (lon - ilon)
    float_y = _NUM_PIXEL_OVERLAP + _TILE_BASE_DIM * (ilat - lat)

    if do_interp:
      # Compensate for the half-pixel offset of the center from the edge.
      float_x -= 0.5
      float_y -= 0.5
      # Bilinear interpolation
      xm = math.floor(float_x)
      xp = xm + 1
      ym = math.floor(float_y)
      yp = ym + 1

      # Calculate the areas used for weighting
      alpha_x, alpha_y = (float_x-xm), (float_y-ym)
      area_xm_ym = alpha_x * alpha_y
      area_xm_yp = alpha_x * (1-alpha_y)
      area_xp_yp = (1-alpha_x) * (1-alpha_y)
      area_xp_ym = (1-alpha_x) * alpha_y

      # Fix 'invalid values' (normally -999) which occurs in area
      # without data, and usually at sea
      # Note: Best would be to preprocess data tiles
      ymxm = tile_cache[ym, xm]
      ymxp = tile_cache[ym, xp]
      ypxm = tile_cache[yp, xm]
      ypxp = tile_cache[yp, xp]
      if ymxm < -900: ymxm = 0.
      if ymxp < -900: ymxp = 0.
      if ypxm < -900: ypxm = 0.
      if ypxp < -900: ypxp = 0.

      # Weight each of the four grid points by the opposite area
      return (area_xm_ym * ypxp + area_xm_yp * ymxp
              + area_xp_yp * ymxm + area_xp_ym * ypxm)

    else:
      # Return the elevation of the nearest point
      ix = int(float_x)
      iy = int(float_y)
      val = tile_cache[iy, ix]
      return val if val > -900 else 0.0

  def GetTerrainElevation(self, lat, lon, do_interp=True):
    """Retrieves the elevation of one or several points.

    This function is vectorized for efficiency.

    Inputs:
      lat, lon: coordinates of points to read (scalar or
        iterable such as list or ndarray)
      do_interp: if True, the elevation is bilinearly interpolated.

    Returns:
      an elevation if the input point is unique
      a ndarray of elevations of the given points, if the input lat/lon are ndarray
      a list of elevations in other iterable cases.
    """
    if np.isscalar(lat):
      return self._GetTerrainElevationPoint(lat, lon, do_interp)

    lat = np.asarray(lat)
    lon = np.asarray(lon)
    ilat = np.ceil(lat)
    ilon = np.floor(lon)
    alt = np.zeros(len(lat))

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
      try:
        tile_cache = self._tile_cache[(key.real, key.imag)]
        self._CacheLruUpdate((key.real, key.imag))
      except:
        tile_cache = self._CacheGridTile(key.real, key.imag)
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

    if isinstance(lat, np.ndarray):
      return alt
    else:
      return list(alt)


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
      lat1, lon1: coordinates of starting point (in degrees)
      lat2, lon2: coordinates of final point (in degrees)
      target_res_meter: target resolution between points (in meters). Default -1
      target_res_arcsec: target resolution between 2 point (in arcsec). Default 1
      do_interp: if True (default), use bilinear interpolation on terrain data
      max_points: if positive, resolution extended if number of points is beyond
                  this number

    Returns:
      an elevation profile in the ITS format as an array:
         elev[0] = number of terrain points - 1 (i.e., number of intervals)
         elev[1] = distance between sample points (meters)
         elev[2]...elev[npts+1] = Terrain elevation (meters)
    """

    if target_res_meter < 0:
      target_res_meter = _RADIUS_EARTH_METERS * math.radians(target_res_arcsec/3600.)

    # Distance between end points (m)
    dist, _, _ = vincenty.GeodesicDistanceBearing(lat1, lon1, lat2, lon2)
    dist *= 1000.

    num_points = int(dist/target_res_meter) + 1
    if max_points > 0 and num_points > max_points:
      num_points = max_points
    if num_points < 2:
      num_points = 2

    resolution = dist / float(num_points-1)
    points = vincenty.GeodesicSampling(lat1, lon1, lat2, lon2, num_points)
    elev = [num_points-1, resolution]
    lat, lon = zip(*points)
    elev.extend(self.GetTerrainElevation(lat, lon, do_interp))
    return elev
