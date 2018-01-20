#    Copyright 2018 SAS Project Authors. All Rights Reserved.
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

"""Utility routines.
"""

import shapely.geometry as sgeo
import numpy as np

WGS_EQUATORIAL_RADIUS_KM2 = 6378.137
WGS_POLAR_RADIUS_KM2 = 6356.753

def _RingArea(latitudes, longitudes):
  """Returns the approximate area of a ring on earth surface (m^2).

  Args:
    latitudes (sequence of float): the latitudes along the ring vertices (degrees).
    longitudes (sequence of float): the longitudes along the ring vertices (degrees).
  """
  # This uses the approximate formula on spheroid derived from:
  #    Robert. G. Chamberlain and William H. Duquette, "Some Algorithms for Polygons on a Sphere",
  #    https://trs-new.jpl.nasa.gov/bitstream/handle/2014/40409/JPL%20Pub%2007-3%20%20w%20Errata.pdf
  #  A small correction is performed to account for the ellipsoi by using both the
  #  the equatorial radius and polar radius.
  if len(latitudes) != len(longitudes):
    raise ValueError('Inconsistent inputs')
  num_coords = len(latitudes)

  if latitudes[0] == latitudes[-1] and longitudes[0] == longitudes[-1]:
    num_coords -= 1
  latitudes = np.radians(latitudes[:num_coords])
  longitudes = np.radians(longitudes[:num_coords])
  if num_coords < 3:
    return 0.

  idx = np.arange(num_coords)
  next = idx + 1
  next[-1] = 0
  prev = idx - 1

  area = np.sum(np.sin(latitudes) * (longitudes[next] - longitudes[prev]))
  area *= 0.5 * WGS_EQUATORIAL_RADIUS_KM2 * WGS_POLAR_RADIUS_KM2
  return np.abs(area)


def GeometryArea(geo, do_ring_interior=False):
  """Returns the approximate area of a |shapely| geometry on earth (in km2).

  This uses the approximate formula on spheroid derived from:
    Robert. G. Chamberlain and William H. Duquette
    "Some Algorithms for Polygons on a Sphere",
    See: https://trs-new.jpl.nasa.gov/bitstream/handle/2014/40409/JPL%20Pub%2007-3%20%20w%20Errata.pdf
  An additional small correction is performed to account partially for the earth
  ellipsoid.

  Args:
    geo: A shapely geometry (Polygon, MultiPolygon, etc..) defined in WGS84 or
      NAD83 (lon, lat) coordinates (degrees).
    do_ring_interior (bool): If True, compute the area inside LinearRing,
      otherwise considers a LinearRing as a ine with area zero (shapely convention).

  Returns:
    (float) The approximate area within the ring (in square kilometers).
  """
  # Lines and points have null area
  if isinstance(geo, sgeo.LinearRing):
    if do_ring_interior:
      return _RingArea(geo.xy[1], geo.xy[0])
    else:
      return 0.
  elif (isinstance(geo, sgeo.Point) or
        isinstance(geo, sgeo.LineString)):
    return 0.
  elif isinstance(geo, sgeo.Polygon):
    return GeometryArea(geo.exterior, True) - sum(GeometryArea(interior, True)
                                                  for interior in geo.interiors)
  else:
    # Multi geometries
    return sum(GeometryArea(simple_shape) for simple_shape in geo)


def PolyWithoutSmallHoles(poly, min_hole_area_km2=0.5):
  """Returns input |shapely| geometry with small internal holes removed.

  Args:
    poly: A shapely polygon geometry (Polygon or MultiPolygon) defined in WGS84
       or in NAD83 (lon, lat) coordinates (degrees).
  min_hole_area_km2: the minimum area for holes to be kept (in km2).

  Returns:
    (a |shapely| geometry) The input geometry with all small holes removed.
  """
  if isinstance(poly, sgeo.Polygon):
    interiors = [interior
                 for interior in poly.interiors
                 if GeometryArea(interior, do_ring_interior=True) > min_hole_area_km2]
    if len(interiors) == len(poly.interiors):
      return poly
    else:
      return sgeo.Polygon(poly.exterior, interiors)
  elif isinstance(poly, sgeo.MultiPolygon):
    return sgeo.MultiPolygon([PolyWithoutSmallHoles(p, min_hole_area_km2)
                              for p in poly])
  else:
    raise ValueError('Input geometry is not a shapely Polygon or MultiPolygon')
