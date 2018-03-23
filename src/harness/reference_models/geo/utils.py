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

"""Utility geometry routines.
"""

import json
import shapely.geometry as sgeo
import shapely.ops as ops
import numpy as np

WGS_EQUATORIAL_RADIUS_KM2 = 6378.137
WGS_POLAR_RADIUS_KM2 = 6356.753


def HasCorrectGeoJsonWinding(geometry):
  """Returns True if a GeoJSON geometry has correct windings.

  A GeoJSON polygon should follow the right-hand rule with respect to the area it
  bounds, ie exterior rings are CCW and holes are CW.

  Args:
    geometry: A dict or string representing a GeoJSON geometry.

  Raises:
    ValueError: If invalid input or GeoJSON geometry type.
  """
  if isinstance(geometry, str):
    geometry = json.loads(geometry)
  if not isinstance(geometry, dict) or 'type' not in geometry:
    raise ValueError('Invalid GeoJSON geometry.')

  def _HasSinglePolygonCorrectWinding(coords):
    exterior = coords[0]
    if not sgeo.LinearRing(exterior).is_ccw:
      return False
    for hole in coords[1:]:
      if sgeo.LinearRing(hole).is_ccw:
        return False
    return True

  if geometry['type'] == 'Polygon':
    coords = geometry['coordinates']
    return _HasSinglePolygonCorrectWinding(coords)
  elif geometry['type'] == 'MultiPolygon':
    for coords in geometry['coordinates']:
      if not _HasSinglePolygonCorrectWinding(coords):
        return False
    return True
  elif geometry['type'] == 'GeometryCollection':
    for subgeo in geometry['geometries']:
      if not HasCorrectGeoJsonWinding(subgeo):
        return False
    return True
  else:
    return True


def InsureGeoJsonWinding(geometry):
  """Returns the input GeoJSON geometry with windings corrected.

  A GeoJSON polygon should follow the right-hand rule with respect to the area it
  bounds, ie exterior rings are CCW and holes are CW.
  Note that the input geometry may be modified in place (case of a dict).

  Args:
    geometry: A dict or string representing a GeoJSON geometry. The returned
      corrected geometry is in same format as the input (dict or str).

  Raises:
    ValueError: If invalid input or GeoJSON geometry type.
  """
  if HasCorrectGeoJsonWinding(geometry):
    return geometry

  is_str = False
  if isinstance(geometry, str):
    geometry = json.loads(geometry)
    is_str = True
  if not isinstance(geometry, dict) or 'type' not in geometry:
    raise ValueError('Invalid GeoJSON geometry.')

  def _InsureSinglePolygonCorrectWinding(coords):
    """Modifies in place the coords for correct windings."""
    exterior = coords[0]
    if not sgeo.LinearRing(exterior).is_ccw:
      exterior.reverse()
    for hole in coords[1:]:
      if sgeo.LinearRing(hole).is_ccw:
        hole.reverse()

  def _list_convert(x):
    # shapely mapping returns a nested tuple.
    return map(_list_convert, x) if isinstance(x, (tuple, list)) else x

  if 'coordinates' in geometry:
    geometry['coordinates'] = _list_convert(geometry['coordinates'])

  if geometry['type'] == 'Polygon':
    _InsureSinglePolygonCorrectWinding(geometry['coordinates'])
  elif geometry['type'] == 'MultiPolygon':
    for coords in geometry['coordinates']:
      _InsureSinglePolygonCorrectWinding(coords)
  elif geometry['type'] == 'GeometryCollection':
    for subgeo in geometry['geometries']:
      InsureGeoJsonWinding(subgeo)

  if is_str:
    geometry = json.dumps(geometry)
  return geometry


def _GeoJsonToShapelyGeometry(geometry):
  """Returns a |shapely| geometry from a GeoJSON geometry.

  Args:
    geometry: A dict or string representing a GeoJSON geometry.

  Raises:
    ValueError: If invalid GeoJSON geometry is passed.
  """
  if isinstance(geometry, str):
    geometry = json.loads(geometry)
  if not isinstance(geometry, dict) or 'type' not in geometry:
    raise ValueError('Invalid GeoJSON geometry.')

  if 'geometries' in geometry:
    return sgeo.GeometryCollection([_GeoJsonToShapelyGeometry(g)
                                    for g in geometry['geometries']])
  geometry = sgeo.shape(geometry)
  if isinstance(geometry, sgeo.Polygon) or isinstance(geometry, sgeo.MultiPolygon):
    geometry = geometry.buffer(0)
  return geometry


def ToShapely(geometry):
  """Returns a |shapely| geometry from a generic geometry or a GeoJSON.

  The original geometry structure is maintained, for example GeometryCollections
  and MultiPolygons are kept as is. To dissolve them, apply the
  `shapely.ops.unary_union()` routine on the output.

  Args:
    geometry: A generic geometry or a GeoJSON geometry (dict or str). A generic
      geometry is any object implementing the __geo_interface__ supported by all
      major geometry libraries (shapely, ..)
  """
  if isinstance(geometry, sgeo.base.BaseGeometry):
    return geometry
  try:
    return _GeoJsonToShapelyGeometry(geometry.__geo_interface__)
  except AttributeError:
    return _GeoJsonToShapelyGeometry(geometry)


def ToGeoJson(geometry, as_dict=False):
  """Returns a GeoJSON geometry from a generic geometry.

  A generic geometry implements the __geo_interface__ as supported by all major
  geometry libraries, such as shapely, etc...

  Args:
    geometry: A generic geometry, for example a shapely geometry.
    as_dict: If True returns the GeoJSON as a dict, otherwise as a string.
  """
  json_geometry = json.dumps(InsureGeoJsonWinding(geometry.__geo_interface__))
  return json.loads(json_geometry) if as_dict else json_geometry


def GridPolygon(poly, res_arcsec):
  """Grids a polygon or multi-polygon.

  This performs regular gridding of a polygon in PlateCarree (equirectangular)
  projection (ie with fixed step in degrees in lat/lon space).
  Points falling in the boundary of polygon will be included.

  Args:
    poly: A Polygon or MultiPolygon in WGS84 or NAD83, defined either as a
      shapely, GeoJSON (dict or str) or generic  geometry.
      A generic geometry is any object implementing the __geo_interface__ protocol.
    res_arcsec: The resolution (in arcsec) used for regular gridding.

  Returns:
    A list of (lon, lat) defining the grid points.
  """
  poly = ToShapely(poly)
  bound_area = (poly.bounds[2] - poly.bounds[0]) * (poly.bounds[3] - poly.bounds[1])
  if isinstance(poly, sgeo.MultiPolygon) and poly.area < bound_area * 0.01:
    # For largely disjoint polygons, we process per polygon
    # to avoid inefficiencies if polygons largely disjoint.
    pts = ops.unary_union(
        [sgeo.asMultiPoint(GridPolygon(p, res_arcsec))
         for p in poly])
    return [(p.x, p.y) for p in pts]

  res = res_arcsec / 3600.
  bounds = poly.bounds
  lng_min = np.floor(bounds[0] / res) * res
  lat_min = np.floor(bounds[1] / res) * res
  lng_max = np.ceil(bounds[2] / res) * res + res/2
  lat_max = np.ceil(bounds[3] / res) * res + res/2
  mesh_lng, mesh_lat = np.mgrid[lng_min:lng_max:res,
                                lat_min:lat_max:res]
  points = np.vstack((mesh_lng.ravel(), mesh_lat.ravel())).T
  pts = poly.intersection(sgeo.asMultiPoint(points))
  if isinstance(pts, sgeo.Point):
    return [(pts.x, pts.y)]
  return [(p.x, p.y) for p in pts]


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


def GeometryArea(geometry, merge_geometries=False):
  """Returns the approximate area of a geometry on earth (in km2).

  This uses the approximate formula on spheroid derived from:
    Robert. G. Chamberlain and William H. Duquette
    "Some Algorithms for Polygons on a Sphere",
    See: https://trs-new.jpl.nasa.gov/bitstream/handle/2014/40409/JPL%20Pub%2007-3%20%20w%20Errata.pdf
  An additional small correction is performed to account partially for the earth
  ellipsoid.

  Args:
    geometry: A geometry defined in WGS84 or NAD83 coordinates (degrees) and
      encoded either as shapely, GeoJson (dict or str) or a generic geometry.
      A generic geometry is any object implementing the __geo_interface__ protocol.
    merge_geometries (bool): If True, then multi geometries will be unioned to
     dissolve intersection prior to the area calculation.

  Returns:
    The approximate area within the geometry (in square kilometers).
  """
  geometry = ToShapely(geometry)
  if (isinstance(geometry, sgeo.Point) or
      isinstance(geometry, sgeo.LineString) or
      isinstance(geometry, sgeo.LinearRing)):
    # Lines, rings and points have null area
    return 0.
  elif isinstance(geometry, sgeo.Polygon):
    return (_RingArea(geometry.exterior.xy[1], geometry.exterior.xy[0])
            - sum(_RingArea(interior.xy[1], interior.xy[0])
                  for interior in geometry.interiors))
  else:
    # Multi geometries
    if merge_geometries:
      geometry = ops.unary_union(geometry)
      # Test if dissolved into a simple geometry.
      try:
        iter(geometry)
      except TypeError:
        return GeometryArea(geometry)
    return sum(GeometryArea(simple_shape) for simple_shape in geometry)

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


def PolygonsAlmostEqual(poly_ref, poly, tol_perc=10):
  """Checks similarity of a polygon to a reference polygon within some tolerance.

  The check is done using method defined in WG4 Test and Certification spec,
  equation 8.3.1.

  Args:
    poly_ref, poly: Two polygons or multipolygons defined  either as shapely,
      GeoJson (dict or str) or generic geometry. A generic geometry is any
      object implementing the __geo_interface__ protocol.

  Returns:
    True if the two polygons are equal (within the tolerance), False otherwise.
  """
  poly_ref = ToShapely(poly_ref)
  poly = ToShapely(poly)
  union_polys = poly_ref.union(poly)
  intersection_polys = poly_ref.intersection(poly)
  return ((GeometryArea(union_polys) - GeometryArea(intersection_polys))
          < tol_perc/100. * GeometryArea(poly_ref))
