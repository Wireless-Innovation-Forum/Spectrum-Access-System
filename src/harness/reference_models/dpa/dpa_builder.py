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

"""DPA (Dynamic Protection Area) protection points builder.

This builder allows to get the protection points for a given DPA.
It is used in particular by the dpa_mr.BuildDpa() routine to create
a complete Dpa() object holding all protection points.

This builder supports several methods for getting the protection points:

 - reading the points from a predefined MultiPoint GeoJson.
 - auto building the points using a registered builder method.

A 'default' method is provided. See DpaProtectionMethod() docstring.
To register a new buider method, use:
  RegisterMethod('mymethod', mymethod_fn)
"""
import ast
from collections import namedtuple
import json
import os

import numpy as np
import shapely.geometry as sgeo

from reference_models.geo import zones
from reference_models.geo import utils


# A protection point
ProtectionPoint = namedtuple('ProtectionPoint',
                             ['longitude', 'latitude'])


# The registered methods for protection points generation
_builder_methods = {}

def RegisterMethod(name, fn):
  """Register a DPA protection points builder method.

  Args:
    name: The name of the method.
    fn: The function implementing the method.
      The function shall have the following prototype:
        fn(dpa_name, dpa_geometry, *args)
      where:
        dpa_name: The DPA name
        dpa_geometry: The DPA geometry as a |shapely.Polygon/MultiPolygon or Point|.
        *args: The other arguments of the function,
  """
  _builder_methods[name.lower()] = fn


def DpaProtectionPoints(dpa_name, dpa_geometry, protection_points_method=None):
  """Gets the protection points for a DPA.

  Args:
    dpa_name: The DPA name.
    dpa_geometry: The DPA geometry as a |shapely.Polygon/MultiPolygon or Point|.
    method: Three ways are supported for getting the protection points:
      + a path pointing to the file holding the protected points location defined as a
        geojson MultiPoint or Point geometry. The path can be either absolute or relative
        to the running script (normally the `harness/` directory).
      + 'default(<parameters>)': A simple default method. Parameters is a tuple defining
        the number of points to use for different part of the DPA:
          num_pts_front_border: Number of points in the front border
          num_pts_back_border: Number of points in the back border
          num_pts_front_zone: Number of points in the front zone
          num_pts_back_zone: Number of points in the back zone
          front_us_border_buffer_km: Buffering of US border for delimiting front/back.
          min_dist_front_border_pts_km: Minimum distance between front border points (km).
          min_dist_back_border_pts_km: Minimum distance between back border points (km).
          min_dist_front_zone_pts_km: Minimum distance between front zone points (km).
          min_dist_back_zone_pts_km: Minimum distance between back zone points (km).
        Example of encoding:
          'default (200,50,20,5)'
        Note the default values are (25, 10, 10, 5, 40, 0.2, 1, 0.5, 3)
        Only the passed parameters will be redefined.
        The result are only approximate (actual distance and number of points may differ).
      + other 'my_method(p1, p2, ..pk)': The 'my_method` will be used, and passing to it
        the parameters p1, p2,... The method must have been registered as a builder method
        using `RegisterMethod()`.

  Returns:
     A list of protection points, each one being a (longitude, latitude) namedtuple.

  Raises:
    IOError: if the provided file cannot be found.
    ValueError: in case of other errors, such as invalid file or parameters.
  """
  def _ExtractBuilder(method):
    idx = method.find('(')
    if idx == -1:
      return None
    name = method[:idx].strip().lower()
    params = method[idx:].strip()
    params = ast.literal_eval(params)
    return name, params

  if not protection_points_method:
    return _DefaultProtectionPoints(dpa_name, dpa_geometry)

  builder = _ExtractBuilder(protection_points_method)
  if builder:
    # Custom or default builder
    name, params = builder
    builder_fn = _builder_methods[name]
    protection_points = builder_fn(dpa_name, dpa_geometry, *params)

  else:
    # Using a geojson file
    protection_points_file = protection_points_method
    if not os.path.isfile(protection_points_file):
      raise IOError('Protected point definition file for DPA `%s` not found at location:'
                    '%s' % (dpa_name, protection_points_file))
    with open(protection_points_file, 'r') as fd:
      mpoints = utils.ToShapely(json.load(fd))
    if isinstance(mpoints, sgeo.Point):
      mpoints = sgeo.MultiPoint([mpoints])
    if not isinstance(mpoints, sgeo.MultiPoint):
      raise ValueError('Protected point definition file for DPA `%s` not a valid MultiPoint'
                       ' geoJSON file.' % dpa_name)
    protection_points = [ProtectionPoint(longitude=pt.x, latitude=pt.y)
                         for pt in mpoints]

  # Check validity of generated points
  if isinstance(dpa_geometry, sgeo.Point):
    if len(protection_points) != 1:
      raise ValueError('Multiple protection points for single point DPA `%s`.' % dpa_name)
    pt = sgeo.Point(protection_points[0].longitude, protection_points[0].latitude)
    if not pt.within(dpa_geometry.buffer(0.0005)):
      raise ValueError('Point for single point DPA `%s` is outside zone: %.5f %.5f'
                       % (dpa_name, pt.x, pt.y))
  else:
    mpoint = sgeo.MultiPoint([(pt.longitude, pt.latitude) for pt in protection_points])
    mpoint_inside = dpa_geometry.buffer(0.0005).intersection(mpoint)
    if (not isinstance(mpoint, sgeo.Point) and not isinstance(mpoint_inside, sgeo.Point)):
      if len(mpoint) != len(mpoint_inside):
        raise ValueError('Some points for DPA `%s` are outside zone.' % dpa_name)

  if not protection_points:
    raise ValueError('No valid points generated for DPA `%s`.' % dpa_name)

  return protection_points


# DPA 'default' builder
# Caching of the extended us_border
_us_border_ext = None
_us_border_ext_buffer = None

def _DefaultProtectionPoints(dpa_name,
                             dpa_geometry,
                             num_pts_front_border=25,
                             num_pts_back_border=10,
                             num_pts_front_zone=10,
                             num_pts_back_zone=5,
                             front_us_border_buffer_km=40,
                             min_dist_front_border_pts_km=0.2,
                             min_dist_back_border_pts_km=1.,
                             min_dist_front_zone_pts_km=0.5,
                             min_dist_back_zone_pts_km=3.):
  """Returns a default list of DPA protection points.

  This creates a default set of points by regular sampling of the contour and gridding
  the interior of the DPA zone. The contour and zone are separated in front and back,
  using the US border (with a buffer) as the delimitation.
  Approximate minimum distance can be specified to avoid too many points for small
  inland DPAs. Single point DPA are obviously protected by a single point.

  Args:
    dpa_geometry: The DPA geometry as a |shapely.Polygon/MultiPolygon or Point|.
    num_pts_front_border: Number of points in the front border.
    num_pts_back_border: Number of points in the back border.
    num_pts_front_zone: Number of points in the front zone.
    num_pts_back_zone: Number of points in the back zone.
    front_us_border_buffer_km: Buffering of US border for delimiting front/back.
    min_dist_front_border_pts_km: Minimum distance between front border points (km).
    min_dist_back_border_pts_km: Minimum distance between back border points (km).
    min_dist_front_zone_pts_km: Minimum distance between front zone points (km).
    min_dist_back_zone_pts_km: Minimum distance between back zone points (km).
  """
  def SampleLine(line, num_points, min_step_arcsec):
    step = line.length / float(num_points)
    min_step = min_step_arcsec / 3600.
    if step < min_step:
      num_points = max(1, int(line.length / min_step))
      step = line.length / float(num_points)
    return [line.interpolate(dist)
            for dist in np.arange(0, line.length-step/2., step)]

  def CvtKmToArcSec(dist_km, ref_geo):
    EQUATORIAL_RADIUS_KM = 6378.
    return dist_km / (EQUATORIAL_RADIUS_KM * 2 * np.pi / 360.
                      * np.cos(ref_geo.centroid.y * np.pi / 180.)) * 3600.

  # Case of DPA points
  if isinstance(dpa_geometry, sgeo.Point):
    return [ProtectionPoint(longitude=dpa_geometry.x, latitude=dpa_geometry.y)]

  # Sanity checks
  num_pts_front_border = max(num_pts_front_border, 1) # at least one

  # Case of Polygon/MultiPolygon
  global _us_border_ext
  global _us_border_ext_buffer
  if _us_border_ext is None or _us_border_ext_buffer != front_us_border_buffer_km:
    us_border = zones.GetUsBorder()
    _us_border_ext = us_border.buffer(CvtKmToArcSec(front_us_border_buffer_km, us_border)
                                      / 3600.)
    _us_border_ext_buffer = front_us_border_buffer_km

  front_border = dpa_geometry.boundary.intersection(_us_border_ext)
  back_border = dpa_geometry.boundary.difference(_us_border_ext)
  front_zone = dpa_geometry.intersection(_us_border_ext)
  back_zone = dpa_geometry.difference(_us_border_ext)

  # Obtain an approximate grid step, insuring a minimum separation between zone points
  step_front_dpa_arcsec = CvtKmToArcSec(min_dist_front_zone_pts_km, dpa_geometry)
  if num_pts_front_zone != 0:
    step_front_dpa_arcsec = max(np.sqrt(front_zone.area / num_pts_front_zone) * 3600.,
                                step_front_dpa_arcsec)
  step_back_dpa_arcsec = CvtKmToArcSec(min_dist_back_zone_pts_km, dpa_geometry)
  if num_pts_back_zone != 0:
    step_back_dpa_arcsec = max(np.sqrt(back_zone.area / num_pts_back_zone) * 3600.,
                               step_back_dpa_arcsec)

  # Obtain the number of points in the border, insuring a minimum separation
  min_step_front_border = CvtKmToArcSec(min_dist_front_border_pts_km, dpa_geometry)
  min_step_back_border = CvtKmToArcSec(min_dist_back_border_pts_km, dpa_geometry)

  front_border_pts = [] if not front_border else [
      ProtectionPoint(longitude=pt.x, latitude=pt.y)
      for pt in SampleLine(front_border, num_pts_front_border, min_step_front_border)]
  back_border_pts = [] if (not back_border or num_pts_back_border == 0) else [
      ProtectionPoint(longitude=pt.x, latitude=pt.y)
      for pt in SampleLine(back_border, num_pts_back_border, min_step_back_border)]
  front_zone_pts = [] if (not front_zone or num_pts_front_zone == 0) else [
      ProtectionPoint(longitude=pt[0], latitude=pt[1])
      for pt in utils.GridPolygon(front_zone, step_front_dpa_arcsec)]
  back_zone_pts = [] if (not back_zone or num_pts_back_zone == 0) else [
      ProtectionPoint(longitude=pt[0], latitude=pt[1])
      for pt in utils.GridPolygon(back_zone, step_back_dpa_arcsec)]

  return front_border_pts + front_zone_pts + back_border_pts + back_zone_pts


# Register the default method
RegisterMethod('default', _DefaultProtectionPoints)
