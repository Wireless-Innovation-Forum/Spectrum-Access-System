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

"""Useful geo routines. Outside regular use"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import shapely.geometry as sgeo
from shapely import affinity

from reference_models.geo import utils
from reference_models.geo import vincenty


# Earth ellipsoidal parameters.
_EARTH_MEAN_RADIUS_KM = 6371.0088  # By IUGG
_WGS_EQUATORIAL_RADIUS_KM2 = 6378.137
_WGS_POLAR_RADIUS_KM2 = 6356.753
_EQUATORIAL_DIST_PER_DEGREE = 2 * np.pi * _WGS_EQUATORIAL_RADIUS_KM2 / 360
_POLAR_DIST_PER_DEGREE = 2 * np.pi * _WGS_POLAR_RADIUS_KM2 / 360


def _ProjectEqc(geometry, ref_latitude=None):
  """Projects a geometry using equirectangular projection.

  Args:
    geometry: A |shapely| geometry with lon,lat coordinates.
    ref_latitude: A reference latitude for the Eqc projection. If None, using
      the centroid of the geometry.
  Returns:
    A tuple of:
      the same geometry in equirectangular projection.
      the reference latitude parameter used for the equirectangular projection.
  """
  if ref_latitude is None:
    ref_latitude = geometry.centroid.y
  geometry = affinity.affine_transform(
      geometry,
      (_EQUATORIAL_DIST_PER_DEGREE * np.cos(np.radians(ref_latitude)), 0.0,
       0.0, _POLAR_DIST_PER_DEGREE,
       0, 0))
  return geometry, ref_latitude


def _InvProjectEqc(geometry, ref_latitude):
  """Returns the inverse equirectangular projection of a geometry.

  Args:
    geometry: A |shapely| geometry with lon,lat coordinates.
    ref_latitude: The reference latitude of the equirectangular projection.
  """
  geometry = affinity.affine_transform(
      geometry,
      (1./(_EQUATORIAL_DIST_PER_DEGREE * np.cos(np.radians(ref_latitude))), 0.0,
       0.0, 1./_POLAR_DIST_PER_DEGREE,
       0, 0))
  return geometry


def Buffer(geometry, distance_km, ref_latitude=None, **kwargs):
  """Returns a geometry with an enveloppe at a given distance (in km).

  This uses the traditional shapely `buffer` method but on the reprojected
  geometry. As such this is somewhat approximate depending on the size of the
  geometry and the buffering distance.

  Args:
    geometry: A |shapely| or geojson geometry.
    distance_km: The buffering distance in km.
    ref_latitude: A reference latitude for the Eqc projection. If None, using
      the centroid of the geometry.
    **kwargs: The optional parameters forwarded to the shapely `buffer` routine:
      (for example: resolution, cap_style, join_style)
  """
  geom = utils.ToShapely(geometry)
  proj_geom, ref_latitude = _ProjectEqc(geom, ref_latitude)
  proj_geom = proj_geom.buffer(distance_km, **kwargs)
  geom = _InvProjectEqc(proj_geom, ref_latitude)
  if isinstance(geometry, sgeo.base.BaseGeometry):
    return geom
  else:
    return utils.ToGeoJson(geom, as_dict=isinstance(geometry, dict))


def GridPolygonApprox(poly, res_km):
  """Grids a polygon or multi-polygon with approximate resolution (in km).

  This is a replacement of `geo.utils.GridPolygon()` for gridding with
  approximate metric distance on both latitude and longitude directions. The
  regular gridding is still done in PlateCarree (equirectangular) projection,
  but with different steps in degrees in lat and long direction.
  Points falling in the boundary of polygon will be included.

  Args:
    poly: A Polygon or MultiPolygon in WGS84 or NAD83, defined either as a
      shapely, GeoJSON (dict or str) or generic  geometry.
      A generic geometry is any object implementing the __geo_interface__
      protocol.
    res_km: The resolution (in km) used for gridding.

  Returns:
    A list of (lon, lat) defining the grid points.
  """
  poly = utils.ToShapely(poly)
  bound_area = ((poly.bounds[2] - poly.bounds[0]) *
                (poly.bounds[3] - poly.bounds[1]))
  if isinstance(poly, sgeo.MultiPolygon) and poly.area < bound_area * 0.01:
    # For largely disjoint polygons, we process per polygon
    # to avoid inefficiencies if polygons largely disjoint.
    pts = ops.unary_union(
        [sgeo.asMultiPoint(GridPolygonApprox(p, res_km))
         for p in poly])
    return [(p.x, p.y) for p in pts]

  # Note: using as reference the min latitude, ie actual resolution < res_km.
  # This is to match NTIA procedure.
  ref_latitude = poly.bounds[1]  # ref_latitude = poly.centroid.y
  res_lat = res_km / _POLAR_DIST_PER_DEGREE
  res_lng = res_km / (
      _EQUATORIAL_DIST_PER_DEGREE * np.cos(np.radians(ref_latitude)))
  bounds = poly.bounds
  lng_min = np.floor(bounds[0] / res_lng) * res_lng
  lat_min = np.floor(bounds[1] / res_lat) * res_lat
  lng_max = np.ceil(bounds[2] / res_lng) * res_lng + res_lng/2.
  lat_max = np.ceil(bounds[3] / res_lat) * res_lat + res_lat/2.
  # The mesh creation is conceptually equivalent to
  # mesh_lng, mesh_lat = np.mgrid[lng_min:lng_max:res_lng,
  #                               lat_min:lat_max:res_lat]
  # but without the floating point accumulation errors
  mesh_lng, mesh_lat = np.meshgrid(
      np.arange(np.floor((lng_max - lng_min) / res_lng) + 1),
      np.arange(np.floor((lat_max - lat_min) / res_lat) + 1),
      indexing='ij')
  mesh_lng = lng_min + mesh_lng * res_lng
  mesh_lat = lat_min + mesh_lat * res_lat
  points = np.vstack((mesh_lng.ravel(), mesh_lat.ravel())).T
  # Performs slight buffering by 1mm to include border points in case they fall
  # exactly on a multiple of
  pts = poly.buffer(1e-8).intersection(sgeo.asMultiPoint(points))
  if isinstance(pts, sgeo.Point):
    return [(pts.x, pts.y)]
  return [(p.x, p.y) for p in pts]


def SampleLine(line, res_km, ref_latitude=None,
               equal_intervals=False, precision=5, ratio=1.0):
  """Samples a line with approximate resolution (in km).

  Args:
    line: A shapely or GeoJSON |LineString|.
    res_km: The resolution (in km).
    ref_latitude: A reference latitude for the Eqc projection. If None, using
      the centroid of the line.
    equal_intervals: If True, all intervals are equal to finish on the edges.
    precision: Simplify final coordinates with provided precision.
    ratio: Only span the given line length.
  Returns:
    A list of (lon, lat) along the line every `res_km`.
  """
  line = utils.ToShapely(line)
  proj_line, ref_latitude = _ProjectEqc(line, ref_latitude)
  if not equal_intervals:
    points = sgeo.MultiPoint(
        [proj_line.interpolate(dist)
         for dist in np.arange(0, ratio * proj_line.length - 1e-6, res_km)])
  else:
    n_intervals = ratio * proj_line.length // res_km
    points = sgeo.MultiPoint(
        [proj_line.interpolate(dist)
         for dist in np.linspace(0, ratio * proj_line.length, n_intervals)])
  points = _InvProjectEqc(points, ref_latitude)
  return [(round(p.x, precision), round(p.y, precision)) for p in points]


def AreaPlateCarreePixel(res_arcsec, ref_latitude):
  """Returns the approximate area in km of a Plate Carree pixel of size `res_arcsec`."""
  return np.cos(np.radians(ref_latitude)) * (
      2 * np.pi * _EARTH_MEAN_RADIUS_KM * res_arcsec / (360 * 3600))**2


def ReplaceVincentyDistanceByHaversine():
  """Replaces Vincenty distance routines by Haversine great circle routines."""
  vincenty.GeodesicDistanceBearing = GreatCircleDistanceBearing
  vincenty.GeodesicPoint = GreatCirclePoint
  vincenty.GeodesicPoints = GreatCirclePoints


# pylint: disable=unused-argument
# Great Circle methods in replacement of Vincenty methods.
# A good description of Haversine formula in their numerical stable version
# can be found at : https://www.movable-type.co.uk/scripts/latlong.html
def GreatCircleDistanceBearing(lat1, lon1, lat2, lon2, accuracy=None):
  """Calculates distance and bearings between points on earth.

  This uses Haversine method considering the earth as a sphere.
    See: https://en.wikipedia.org/wiki/Haversine_formula
  This routine is designed to be a pure replacement of the similar
  'google3.third_party.winnforum_sas.vincenty.GeodesicDistanceBearing()'
  which uses the more precise Vincenty-based formula but is much slower.
  It also goes beyond the vincenty implementation as it supports sequence
  of points, either on the initial, final points or both.

  Args:
    lat1 (float or iterable of float): The initial point(s) latitude (degrees).
    lon1 (float or iterable of float): The initial point(s) longitude (degrees).
    lat2 (float or iterable of float): The final point(s) latitude (degrees).
    lon2 (float or iterable of float): The final point(s) longitude (degrees).
    accuracy: (unused) For compatibility with vincenty method prototype.

  Returns:
    A tuple of distance (km), direct bearing and back bearing (degrees). If
    an iterable of points are passed as input, ndarray are returned.
  """
  if lat1 == lat2 and lon1 == lon2:
    return 0, 0, -180
  lat1 = np.deg2rad(lat1)
  lat2 = np.deg2rad(lat2)
  delta_lat = lat2 - lat1
  delta_lon = np.deg2rad(lon2) - np.deg2rad(lon1)
  sin_lat1 = np.sin(lat1)
  cos_lat1 = np.cos(lat1)
  sin_lat2 = np.sin(lat2)
  cos_lat2 = np.cos(lat2)

  phi = (
      np.sin(delta_lat / 2)**2 + cos_lat1 * cos_lat2 *
      (np.sin(delta_lon / 2)**2))
  phi = 2 * np.arctan2(np.sqrt(phi), np.sqrt(1 - phi))
  distance = _EARTH_MEAN_RADIUS_KM * phi

  bearing = np.rad2deg(
      np.arctan2(
          np.sin(delta_lon) * cos_lat2,
          cos_lat1 * sin_lat2 - sin_lat1 * cos_lat2 * np.cos(delta_lon)))
  rev_bearing = np.rad2deg(
      np.arctan2(-np.sin(delta_lon) * cos_lat1,
                 cos_lat2 * sin_lat1 - sin_lat2 * cos_lat1 * np.cos(delta_lon)))
  if np.isscalar(bearing):
    if bearing < 0:
      bearing += 360
    if rev_bearing < 0:
      rev_bearing += 360
  else:
    bearing[bearing < 0] += 360
    rev_bearing[rev_bearing < 0] += 360

  return distance, bearing, rev_bearing


def GreatCirclePoint(lat, lon, dist_km, bearing, accuracy=None):
  """Computes the coordinates of a point towards a bearing at given distance.

  This uses Haversine method considering the earth as a sphere.
    See: https://en.wikipedia.org/wiki/Haversine_formula
  This routine is designed to be a pure replacement of the similar
  'google3.third_party.winnforum_sas.vincenty.GeodesicDistanceBearing()'
  which uses the more precise Vincenty-based formula but is much slower.

  Args:
    lat (float): The initial point latitude (degrees).
    lon (float): The initial point longitude (degrees).
    dist_km (float): The distance of the target point (km).
    bearing (float): The bearing angle (in degrees)
    accuracy (unused): For compatibility with vincenty method prototype.

  Returns:
    A tuple of the final point latitude, longitude and final reverse bearing,
    all in degrees.
  """
  tgt_lat, tgt_lon, rev_bearing = GreatCirclePoints(lat, lon, [dist_km],
                                                    bearing)
  return tgt_lat[0], tgt_lon[0], rev_bearing[0]


def GreatCirclePoints(lat, lon, distances_km, bearing, accuracy=None):
  """Computes the coordinates of points towards a bearing at several distances.

  This uses Haversine method considering the earth as a sphere.
    See: https://en.wikipedia.org/wiki/Haversine_formula
  This routine is designed to be a pure replacement of the similar
  'google3.third_party.winnforum_sas.vincenty.GeodesicPoints()'
  which uses the more precise Vincenty-based formula but is much slower.

  This routine is similar to `GreatCirclePoint` but can take any coherent
  sequence of values for the initial point, distances or bearing, and
  perform an efficient vectorized operation internally. 'Coherent' means that
  either only one of the input is a sequence, or several are with the same
  shapes.

  Args:
    lat: The initial point latitude (degrees).
    lon: The initial point longitude (degrees).
    distances_km (iterable of float): A sequence of distance of the target
      points (in km). Can be for example a ndarray or a list.
    bearing (float or iterable of float): The bearing angle (in degrees).
    accuracy (unused): For compatibility with vincenty method prototype.

  Returns:
    A tuple of the points latitude, longitude and reverse bearing, all in
    degrees. If one of the input is a ndarray, ndarray are returned,
    otherwise lists are returned.
  """
  is_array = (
      isinstance(distances_km, np.ndarray) or isinstance(bearing, np.ndarray) or
      isinstance(lat, np.ndarray))
  lat = np.deg2rad(lat)
  lon = np.deg2rad(lon)
  bearing = np.deg2rad(bearing)
  norm_distances = np.asarray(distances_km) / _EARTH_MEAN_RADIUS_KM
  tgt_lat = np.arcsin(
      np.sin(lat) * np.cos(norm_distances) +
      np.cos(lat) * np.sin(norm_distances) * np.cos(bearing))
  tgt_lon = lon + np.arctan2(
      np.sin(bearing) * np.sin(norm_distances) * np.cos(lat),
      np.cos(norm_distances) - np.sin(lat) * np.sin(tgt_lat))
  rev_bearing = np.rad2deg(
      np.arctan2(-np.sin(tgt_lon - lon) * np.cos(lat),
                 np.cos(tgt_lat) * np.sin(lat) -
                 np.sin(tgt_lat) * np.cos(lat) * np.cos(tgt_lon - lon)))
  tgt_lat = np.rad2deg(tgt_lat)
  tgt_lon = np.rad2deg(tgt_lon)
  rev_bearing[rev_bearing < 0] += 360

  if is_array:
    return tgt_lat, tgt_lon, rev_bearing
  else:
    return list(tgt_lat), list(tgt_lon), list(rev_bearing)
