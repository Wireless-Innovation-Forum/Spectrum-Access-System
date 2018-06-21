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
import json
import shapely.geometry as sgeo
from shapely import ops

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
    with open(os.path.join(TEST_DIR, 'missouri.json'), 'r') as fd:
      missouri = json.load(fd)
    poly = sgeo.Polygon(missouri['geometries'][0]['coordinates'][0][0])
    area = utils.GeometryArea(poly)
    self.assertTrue(np.abs(area - official_area) < 0.0025 * official_area)

  def test_area_geojson_missouri(self):
    official_area = 180530
    with open(os.path.join(TEST_DIR, 'missouri.json'), 'r') as fd:
      missouri = json.load(fd)
    area = utils.GeometryArea(missouri)
    self.assertTrue(np.abs(area - official_area) < 0.0025 * official_area)

  def test_area_geojson_ppa(self):
    expected_area = 130.98
    with open(os.path.join(TEST_DIR, 'ppa_record_0.json'), 'r') as fd:
      ppa = json.load(fd)
    area = utils.GeometryArea(ppa['zone']['features'][0]['geometry'])
    self.assertAlmostEqual(area, expected_area, 2)

  def test_area_geojson_geocollection_and_merge(self):
    expected_area = 3535
    expected_real_area = expected_area * 2/3.
    with open(os.path.join(TEST_DIR, 'test_geocollection.json'), 'r') as fd:
      multigeo = json.load(fd)
    area = utils.GeometryArea(multigeo)
    self.assertAlmostEqual(area, expected_area, 0)
    area = utils.GeometryArea(multigeo, merge_geometries=True)
    self.assertAlmostEqual(area, expected_real_area, 0)

  def test_degenerate_shapes(self):
    # Test all degenerate shapes (points, lines) have area zero
    points = sgeo.MultiPoint([(4, 59), (6, 59), (6, 61), (4, 61)])
    line = sgeo.LineString([(4, 59), (6, 59), (6, 61), (4, 61)])
    ring = sgeo.LinearRing([(4, 59), (6, 59), (6, 61), (4, 61)])
    self.assertEqual(utils.GeometryArea(points), 0)
    self.assertEqual(utils.GeometryArea(line), 0)
    self.assertEqual(utils.GeometryArea(ring), 0)

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

  def test_grid_point_and_null(self):
    poly = sgeo.Polygon([(1.9, 0.9), (2.1, 0.9), (2.1, 1.1), (1.9, 1.1)])
    exp_pts = [(2.0, 1.0)]
    pts = utils.GridPolygon(poly, res_arcsec=900.)
    self.assertListEqual(pts, exp_pts)
    pts = utils.GridPolygon(poly, res_arcsec=7200.)
    self.assertListEqual(pts, [])

  def test_grid_simple(self):
    poly = sgeo.Polygon([(1.9, 3.9), (3.1, 3.9), (3.1, 4.4),
                         (2.5, 4.5), (2.4, 5.1), (1.9, 5.1)])
    exp_pts = {(2.0, 4.0), (2.5, 4.0), (3.0, 4.0),
               (2.0, 4.5), (2.5, 4.5), (2.0, 5.0)}
    pts = utils.GridPolygon(poly, res_arcsec=1800.)
    self.assertSetEqual(set(pts), exp_pts)

  def test_grid_border_included(self):
    poly = sgeo.Polygon([(-108.05, 42.25),
                         (-107.90, 42.25),
                         (-107.90, 42.20),
                         (-108.05, 42.20),
                         (-108.05, 42.25)])
    pts = utils.GridPolygon(poly, res_arcsec=2.)
    self.assertEqual(len(pts), (1800*0.15+1) * (1800*0.05+1))
    self.assertAlmostEqual(pts[0][0], -108.05, 10)
    self.assertAlmostEqual(pts[0][1], 42.20, 10)
    self.assertAlmostEqual(pts[-1][0], -107.90, 10)
    self.assertAlmostEqual(pts[-1][1], 42.25, 10)

  def test_grid_simple_with_hole(self):
    poly = sgeo.Polygon([(1.9, 3.9), (3.1, 3.9), (3.1, 4.4),
                         (2.5, 4.5), (2.4, 5.1), (1.9, 5.1)],
                        [[(1.95, 3.95), (2.05, 3.95), (2.05, 4.4)]])
    exp_pts = {(2.5, 4.0), (3.0, 4.0),
               (2.0, 4.5), (2.5, 4.5), (2.0, 5.0)}
    pts = utils.GridPolygon(poly, res_arcsec=1800.)
    self.assertSetEqual(set(pts), exp_pts)

  def test_grid_complex(self):
    with open(os.path.join(TEST_DIR, 'test_geocollection.json'), 'r') as fd:
      json_geo = json.load(fd)

    shape_geo = utils.ToShapely(json_geo)
    exp_pts = {(-95, 40), (-95.5, 40.5), (-95.5, 40),
               (-96, 40), (-96.5, 40.5), (-96.5, 40)}
    pts = utils.GridPolygon(json_geo, res_arcsec=1800)
    self.assertSetEqual(set(pts), exp_pts)

    pts = utils.GridPolygon(shape_geo, res_arcsec=1800)
    self.assertSetEqual(set(pts), exp_pts)

    pts = utils.GridPolygon(ops.unary_union(shape_geo), res_arcsec=1800)
    self.assertSetEqual(set(pts), exp_pts)

  def test_polygons_equal(self):
    poly_ref = sgeo.Point(0,0).buffer(1)

    poly = sgeo.Point(0,0).buffer(1)
    self.assertTrue(utils.PolygonsAlmostEqual(poly_ref, poly, 1e-6))

    poly = sgeo.Point(0,0).buffer(1.1)
    self.assertTrue(utils.PolygonsAlmostEqual(poly_ref, poly, 21.2))

    poly = sgeo.Point(0,0).buffer(1.1)
    self.assertFalse(utils.PolygonsAlmostEqual(poly_ref, poly, 20.8))

    poly = sgeo.Point(0, 0.1).buffer(1)
    self.assertTrue(utils.PolygonsAlmostEqual(poly_ref, poly, 15))

  def test_polygon_correct_geojson_winding(self):
    poly_with_hole = {'type': 'Polygon',
                      'coordinates': [
                          [[-97.23, 38.86], [-97.31, 38.76], [-97.16, 38.73],
                           [-97.16, 38.86], [-97.23, 38.86]],
                          [[-97.21, 38.82], [-97.18, 38.81], [-97.19, 38.78],
                           [-97.22, 38.78], [-97.21, 38.82]]]}
    self.assertTrue(utils.HasCorrectGeoJsonWinding(poly_with_hole))

    poly_with_hole['coordinates'][0] = list(reversed(poly_with_hole['coordinates'][0]))
    self.assertFalse(utils.HasCorrectGeoJsonWinding(poly_with_hole))

    poly_with_hole['coordinates'][1] = list(reversed(poly_with_hole['coordinates'][1]))
    self.assertFalse(utils.HasCorrectGeoJsonWinding(poly_with_hole))

    poly_with_hole['coordinates'][0] = list(reversed(poly_with_hole['coordinates'][0]))
    self.assertFalse(utils.HasCorrectGeoJsonWinding(poly_with_hole))

  def test_json_polygon_corrected_winding(self):
    poly_with_hole = {'type': 'Polygon',
                      'coordinates': [
                          [[-97.23, 38.86], [-97.31, 38.76], [-97.16, 38.73],
                           [-97.16, 38.86], [-97.23, 38.86]],
                          [[-97.21, 38.82], [-97.18, 38.81], [-97.19, 38.78],
                           [-97.22, 38.78], [-97.21, 38.82]]]}
    poly_with_hole['coordinates'][0].reverse()
    poly_with_hole['coordinates'][1].reverse()

    corr_poly = utils.InsureGeoJsonWinding(poly_with_hole)
    self.assertDictEqual(corr_poly, poly_with_hole)

    poly_str = json.dumps(poly_with_hole)
    corr_poly = utils.InsureGeoJsonWinding(poly_str)
    self.assertIsInstance(corr_poly, str)
    self.assertDictEqual(json.loads(corr_poly), poly_with_hole)

  def test_json_multicollection_correct_winding(self):
    with open(os.path.join(TEST_DIR, 'test_geocollection.json'), 'r') as fd:
      json_geo = json.load(fd)
    json_geo['geometries'][0]['coordinates'][0].reverse()
    json_geo['geometries'][1]['coordinates'][0].reverse()

    self.assertFalse(utils.HasCorrectGeoJsonWinding(json_geo))
    corr_poly = utils.InsureGeoJsonWinding(json_geo)
    self.assertTrue(utils.HasCorrectGeoJsonWinding(json_geo))

  def test_togeojson_with_correct_winding(self):
    loop = [[-95.0, 40.0], [-95.5, 40.5], [-95.5, 40.0], [-95.0, 40.0]]
    hole = [[-95.2, 40.2], [-95.3, 40.3], [-95.3, 40.2], [-95.2, 40.2]]
    poly = sgeo.Polygon(loop, [hole])

    json_poly = json.loads(utils.ToGeoJson(poly))
    self.assertIn('type', json_poly)
    self.assertEqual(json_poly['type'], 'Polygon')
    self.assertIn('coordinates', json_poly)
    self.assertTrue(json_poly['coordinates'] == [loop, list(reversed(hole))])

  def test_togeojson_with_multi_polygon(self):
    loop1 = [[-95.0, 40.0], [-95.5, 40.5], [-95.5, 40.0], [-95.0, 40.0]]
    loop2 = [[-95.2, 40.2], [-95.3, 40.2], [-95.3, 40.3], [-95.2, 40.2]]
    mpoly = sgeo.MultiPolygon([sgeo.Polygon(loop1), sgeo.Polygon(loop2)])

    json_poly = json.loads(utils.ToGeoJson(mpoly))
    self.assertIn('type', json_poly)
    self.assertEqual(json_poly['type'], 'MultiPolygon')
    self.assertIn('coordinates', json_poly)
    self.assertTrue(json_poly['coordinates'] == [[loop1], [list(reversed(loop2))]])

  def test_toshapely(self):
    poly = sgeo.Point(0, 0).buffer(1)
    poly_json = utils.ToGeoJson(poly)

    # Test for a generic geometry object.
    poly2 = utils.ToShapely(poly)
    self.assertEqual(poly2.difference(poly).area, 0)
    self.assertEqual(poly.difference(poly2).area, 0)

    # Test for a string geojson.
    poly2 = utils.ToShapely(poly_json)
    self.assertEqual(poly2.difference(poly).area, 0)
    self.assertEqual(poly.difference(poly2).area, 0)

  def test_closest_border_point(self):
    # Specific point 4km away from border
    res0 = utils.GetClosestCanadianBorderPoint(42.040967, -83.197932, 3.5)
    self.assertTrue(res0 is None)
    res0 = utils.GetClosestCanadianBorderPoint(42.040967, -83.197932, 3.99)
    self.assertTrue(res0 is None)
    res1 = utils.GetClosestCanadianBorderPoint(42.040967, -83.197932, 30)
    self.assertAlmostEqual(res1[0], 42.04095, 4)
    self.assertAlmostEqual(res1[1], -83.14962, 4)
    self.assertAlmostEqual(res1[2], 4.0, 3)
    self.assertAlmostEqual(res1[3], 90, 2)

  def test_check_sharing_zone(self):
    # Less than 8km
    status, _, _ = utils.CheckCbsdInBorderSharingZone(42.040967, -83.197932,
                                                      270, 65)
    self.assertTrue(status)
    status, lat, lon = utils.CheckCbsdInBorderSharingZone(42.040967, -83.197932,
                                                          90, 65)
    self.assertTrue(status)
    self.assertAlmostEqual(lat, 42.04095, 4)
    self.assertAlmostEqual(lon, -83.14962, 4)
    # At 57km
    status, _, _ = utils.CheckCbsdInBorderSharingZone(42.0389, -83.838,
                                                      90, 65)
    self.assertFalse(status)
    # At 20km
    status, lat, lon = utils.CheckCbsdInBorderSharingZone(42.0407, -83.3912,
                                                          90, 65)
    self.assertTrue(status)
    self.assertAlmostEqual(lat, 42.04095, 4)
    self.assertAlmostEqual(lon, -83.14962, 4)
    status, lat, lon = utils.CheckCbsdInBorderSharingZone(42.0407, -83.3912,
                                                          270, 65)
    self.assertFalse(status)
    status, lat, lon = utils.CheckCbsdInBorderSharingZone(42.0407, -83.3912,
                                                          350-32.7, 65)
    self.assertFalse(status)
    status, lat, lon = utils.CheckCbsdInBorderSharingZone(42.0407, -83.3912,
                                                          350-32.3, 65)
    self.assertTrue(status)
    status, lat, lon = utils.CheckCbsdInBorderSharingZone(42.0407, -83.3912,
                                                          270, 360)
    self.assertTrue(status)

  def test_insure_feature_collection(self):
    with open(os.path.join(TEST_DIR, 'ppa_record_0.json'), 'r') as fd:
      ppa = json.load(fd)
    feature_col = ppa['zone']
    feature_col_str = json.dumps(feature_col)
    feature = ppa['zone']['features'][0]
    geometry = ppa['zone']['features'][0]['geometry']
    geometry_str = json.dumps(geometry)
    self.assertDictEqual(utils.InsureFeatureCollection(feature_col, as_dict=True),
                          feature_col)
    self.assertDictEqual(utils.InsureFeatureCollection(feature_col_str, as_dict=True),
                          feature_col)
    self.assertDictEqual(utils.InsureFeatureCollection(feature, as_dict=True),
                          feature_col)
    self.assertDictEqual(utils.InsureFeatureCollection(geometry, as_dict=True),
                          feature_col)
    self.assertDictEqual(utils.InsureFeatureCollection(geometry_str, as_dict=True),
                          feature_col)
    self.assertEqual(utils.InsureFeatureCollection(geometry),
                      feature_col_str)
    self.assertEqual(utils.InsureFeatureCollection(geometry_str),
                      feature_col_str)

  def test_shrinks_polygon(self):
    with open(os.path.join(TEST_DIR, 'test_shrink.json'), 'r') as fd:
      ppa = json.load(fd)
    geometry = ppa['features'][0]['geometry']
    self.assertTrue(geometry['type'], 'Polygon')
    spoly = utils.ToShapely(geometry)
    mpoly = sgeo.MultiPolygon([sgeo.Point(0,0).buffer(1),
                               sgeo.Point(2,0).buffer(0.1)])
    poly1 = utils.ShrinkAndCleanPolygon(geometry, 1e-2)
    poly2 = utils.ShrinkAndCleanPolygon(spoly, 1e-2)
    self.assertTrue(poly2.area < spoly.area)
    with self.assertRaises(ValueError):
      poly = utils.ShrinkAndCleanPolygon(mpoly, 1e-2)
    self.assertEqual(poly1['type'], 'Polygon')
    self.assertTrue(isinstance(poly2, sgeo.Polygon))
    spoly1 = utils.ToShapely(poly1)
    self.assertEqual(poly2.difference(spoly1).area, 0)
    self.assertEqual(spoly1.difference(poly2).area, 0)


if __name__ == '__main__':
  unittest.main()
