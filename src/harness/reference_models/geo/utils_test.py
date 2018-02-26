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


import numpy as np
import os
import unittest
import geojson
import shapely.geometry as sgeo

from reference_models.geo import utils

TEST_DIR = os.path.join(os.path.dirname(__file__),'testdata', 'json')

class TestUtils(unittest.TestCase):

  def test_area_simple_square(self):
    # Use a small sw=quare centered around 60degree latitude, so radius is half
    # on the longitude
    square = sgeo.Polygon([(4, 59), (6, 59), (6, 61), (4, 61)])
    area = utils.GeometryArea(square)
    self.assertAlmostEqual(area, 24699.71, 2)

  def test_complex_polygons(self):
    square = sgeo.Polygon([(4, 59), (6, 59), (6, 61), (4, 61)])
    hole = sgeo.Polygon([(5, 60), (5.1, 60.1), (5, 60.2)])
    square_with_hole = sgeo.Polygon(square.exterior, [hole.exterior])
    multipoly = sgeo.MultiPolygon([square_with_hole, hole])
    self.assertAlmostEqual(utils.GeometryArea(square_with_hole),
                           utils.GeometryArea(square) - utils.GeometryArea(hole), 7)
    self.assertAlmostEqual(utils.GeometryArea(multipoly), 24699.71, 2)

  def test_area_missouri(self):
    # The real Missouri area is 180530 km2. Make sure we are within 0.25%
    official_area = 180530
    with open(os.path.join(TEST_DIR, 'missouri.json')) as fd:
      missouri = geojson.load(fd)
      poly = sgeo.Polygon(missouri['geometries'][0]['coordinates'][0][0])
      area = utils.GeometryArea(poly)
      self.assertTrue(np.abs(area - official_area) < 0.0025 * official_area)

  def test_degenerate_shapes(self):
    # Test all degenerate shapes (points, lines) have area zero
    points = sgeo.MultiPoint([(4, 59), (6, 59), (6, 61), (4, 61)])
    line = sgeo.LineString([(4, 59), (6, 59), (6, 61), (4, 61)])
    ring = sgeo.LinearRing([(4, 59), (6, 59), (6, 61), (4, 61)])
    self.assertEqual(utils.GeometryArea(points), 0)
    self.assertEqual(utils.GeometryArea(line), 0)
    self.assertEqual(utils.GeometryArea(ring), 0)
    # test special closed ring mode
    self.assertAlmostEqual(utils.GeometryArea(ring, True), 24700, 0)

  def test_remove_small_holes(self):
    # Test all degenerate shapes (points, lines) have area zero
    # Use a small sw=quare centered around 60degree latitude, so radius is half
    # on the longitude
    square = sgeo.Polygon([(4, 59), (6, 59), (6, 61), (4, 61)])
    hole = sgeo.Polygon([(5, 60), (5.01, 60.01), (5, 60.02)])
    square_with_hole = sgeo.Polygon([(4, 59), (6, 59), (6, 61), (4, 61)],
                                    [[(5, 60), (5.01, 60.01), (5, 60.02)]])
    square_cleaned = utils.PolyWithoutSmallHoles(square_with_hole,
                                                 min_hole_area_km2= 0.62)
    multipoly = sgeo.MultiPolygon([square_with_hole, hole])
    multipoly_cleaned = utils.PolyWithoutSmallHoles(multipoly,
                                                    min_hole_area_km2= 0.62)
    area = utils.GeometryArea(square)
    area_with_hole = utils.GeometryArea(square_with_hole)
    self.assertAlmostEqual(area - area_with_hole, 0.617, 3)
    self.assertEqual(square, square_cleaned)
    self.assertEqual(multipoly_cleaned, sgeo.MultiPolygon([square, hole]))

if __name__ == '__main__':
  unittest.main()
