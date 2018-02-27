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
from shapely import ops
import numpy as np

WGS_EQUATORIAL_RADIUS_KM2 = 6378.137
WGS_POLAR_RADIUS_KM2 = 6356.753


def GeoJsonToShapelyGeometry(geo):
  """Returns a |shapely| geometry from a GeoJSON geometry.

  The structure of the GeoJSON is kept and both Geometry collections
  and MultiPolygons are kept as is. To dissolve them, use the
  `shapely.ops.unary_union()` routine.

  Args:
    geo: a dict representing a GeoJSON geometry.
  """
  if 'geometries' in geo:
    return sgeo.GeometryCollection([GeoJsonToShapelyGeometry(g)
                                    for g in geo['geometries']])
  geo = sgeo.shape(geo)
  if isinstance(geo, sgeo.Polygon) or isinstance(geo, sgeo.MultiPolygon):
    geo = geo.buffer(0)
  return geo


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


def GeometryArea(geo, merge_geometries=False):
  """Returns the approximate area of a geometry on earth (in km2).

  This uses the approximate formula on spheroid derived from:
    Robert. G. Chamberlain and William H. Duquette
    "Some Algorithms for Polygons on a Sphere",
    See: https://trs-new.jpl.nasa.gov/bitstream/handle/2014/40409/JPL%20Pub%2007-3%20%20w%20Errata.pdf
  An additional small correction is performed to account partially for the earth
  ellipsoid.

  Args:
    geo: A geometry defined in WGS84 or NAD83 coordinates (degrees) either:
      - a shapely geometry (Polygon, MultiPolygon, etc..)
      - a GeoJSON geometry (dict), representing either a basic geometry or
        a GeometryCollection.
    merge_geometries (bool): If True, then multi geometries will be unioned to
     dissolve intersection prior to the area calculation.

  Returns:
    (float) The approximate area within the geometry (in square kilometers).
  """
  if isinstance(geo, dict):
    geo = GeoJsonToShapelyGeometry(geo)
    if merge_geometries:
      geo = ops.unary_union(geo)
    return GeometryArea(geo)
  elif (isinstance(geo, sgeo.Point) or
        isinstance(geo, sgeo.LineString) or
        isinstance(geo, sgeo.LinearRing)):
        # Lines, rings and points have null area
    return 0.
  elif isinstance(geo, sgeo.Polygon):
    return (_RingArea(geo.exterior.xy[1], geo.exterior.xy[0])
            - sum(_RingArea(interior.xy[1], interior.xy[0])
                  for interior in geo.interiors))
  else:
    # Multi geometries
    if merge_geometries:
      geo = ops.unary_union(geo)
      # Test if dissolved into a simple geometry.
      try:
        iter(geo)
      except TypeError:
        return GeometryArea(geo)
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
                 if GeometryArea(sgeo.Polygon(interior)) > min_hole_area_km2]
    if len(interiors) == len(poly.interiors):
      return poly
    else:
      return sgeo.Polygon(poly.exterior, interiors)
  elif isinstance(poly, sgeo.MultiPolygon):
    return sgeo.MultiPolygon([PolyWithoutSmallHoles(p, min_hole_area_km2)
                              for p in poly])
  else:
    raise ValueError('Input geometry is not a shapely Polygon or MultiPolygon')
