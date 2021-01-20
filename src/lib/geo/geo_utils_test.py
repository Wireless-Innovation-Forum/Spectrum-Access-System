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

"""Unit test for the geo_utils.py library."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import unittest

import numpy as np
import shapely.geometry as sgeo

from geo import geo_utils
from reference_models.geo import utils


class TestGeoUtils(unittest.TestCase):

  def assertSeqAlmostEqual(self, in1, in2, places=7):
    """Asserts if 2 (possibly nested) sequences are almost equal."""
    for i1, i2 in zip(in1, in2):
      try:
        iter(i1)
      except TypeError:
        self.assertAlmostEqual(i1, i2, places)
      else:
        for k1, k2 in zip(i1, i2):
          self.assertAlmostEqual(k1, k2, places)

  def test_buffer_point(self):
    pt = sgeo.Point(-110, 40)
    circle = geo_utils.Buffer(pt, 20, resolution=256)
    area = utils.GeometryArea(circle)
    self.assertLess(np.abs(area - np.pi*20**2), 0.001 * area)

  def test_buffer_poly(self):
    pt = sgeo.Point(-110, 40)
    circle = geo_utils.Buffer(pt, 20, resolution=256)
    circle = geo_utils.Buffer(circle, 10, resolution=256)
    area = utils.GeometryArea(circle)
    self.assertLess(np.abs(area - np.pi*30**2), 0.001 * area)

  def test_shrink_poly(self):
    pt = sgeo.Point(-110, 40)
    circle = geo_utils.Buffer(pt, 20, resolution=256)
    circle = geo_utils.Buffer(circle, -10, resolution=256)
    area = utils.GeometryArea(circle)
    self.assertLess(np.abs(area - np.pi*10**2), 0.001 * area)

  def test_buffer_json_poly(self):
    pt = sgeo.Point(-110, 40)
    circle = geo_utils.Buffer(pt, 20)
    json_circle = utils.ToGeoJson(circle)
    json_circle = geo_utils.Buffer(json_circle, 10)
    area = utils.GeometryArea(json_circle)
    self.assertLess(np.abs(area - np.pi*30**2), 0.002 * area)

  def test_grid_polygon_approx(self):
    poly = sgeo.Polygon([(0, 59), (0, 61), (2, 61), (2, 59)])
    pts = geo_utils.GridPolygonApprox(poly, res_km=100.)
    self.assertEqual(len(pts), 4)
    self.assertSeqAlmostEqual(pts, [(0, 59.4883), (0, 60.3896),
                                    (1.7442, 59.4883), (1.7442, 60.3896)], 4)
    pts = geo_utils.GridPolygonApprox(poly, res_km=110.95)
    self.assertEqual(len(pts), 4)
    self.assertSeqAlmostEqual(pts, [(0, 59.), (0, 60.),
                                    (1.935, 59.), (1.935, 60.)], 2)

  def test_sample_line(self):
    line = sgeo.LineString([(0, 50), (0, 60), (40, 60), (40, 70)])
    pts = geo_utils.SampleLine(line, 10*110.946)
    self.assertEqual(len(pts), 5)
    self.assertSeqAlmostEqual(pts, [(0, 50), (0, 60.),
                                    (19.933, 60.), (39.866, 60)], 3)

if __name__ == '__main__':
  unittest.main()
