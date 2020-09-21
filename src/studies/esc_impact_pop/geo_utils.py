"""Useful geo routines."""
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
