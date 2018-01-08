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

import os
import logging
import numpy as np
import unittest
import shutil

from reference_models.geo import testutils
from reference_models.geo import terrain


TEST_DIR = os.path.join(os.path.dirname(__file__),'testdata', 'ned')
logging.disable(30)


class TestTerrain(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.unzip_files = testutils.UnzipTestDir(TEST_DIR)
    # Copy the tile to simulate neighboring tile
    new_tile = "floatn37w123_1_std.flt"
    shutil.copyfile(os.path.join(TEST_DIR, "floatn38w123_1_std.flt"),
                    os.path.join(TEST_DIR, new_tile))
    cls.unzip_files.append(new_tile)

  @classmethod
  def tearDownClass(cls):
    testutils.RemoveFiles(TEST_DIR, cls.unzip_files)

  def setUp(self):
    self.terrain_driver = terrain.TerrainDriver(TEST_DIR)

  def test_get_elevation(self):
    # Twin Peaks - SF
    h = self.terrain_driver.GetTerrainElevation(
        lat=37.751458, lon=-122.447831, do_interp=False)
    self.assertAlmostEqual(h, 275.45, 2)
    # Pacific Ocean SF - In the sea
    h = self.terrain_driver.GetTerrainElevation(
        lat=37.750036, lon=-122.51527, do_interp=False)
    self.assertAlmostEqual(h, 0.0, 1)
    # Ocean - far away from the coast
    h = self.terrain_driver.GetTerrainElevation(
        lat=37.750036, lon=-122.999, do_interp=False)
    self.assertEqual(h, 0.0)

  def test_outside_grid(self):
    # Outside database tiles
    h = self.terrain_driver.GetTerrainElevation(
        lat=37.75, lon=-121.9999, do_interp=False)
    self.assertEqual(h, 0.0)

  def test_interpolation(self):
    # Interpolation test
    lat,lon = 37.75-0.5/3600., -122.5-0.5/3600.
    h00 = self.terrain_driver.GetTerrainElevation(
        lat=lat, lon=lon, do_interp=False)
    h01 = self.terrain_driver.GetTerrainElevation(
        lat=lat, lon=lon+1/3600., do_interp=False)
    h10 = self.terrain_driver.GetTerrainElevation(
        lat=lat+1/3600., lon=lon, do_interp=False)
    h11 = self.terrain_driver.GetTerrainElevation(
        lat=lat+1/3600., lon=lon+1/3600., do_interp=False)
    # On exact points
    ha = self.terrain_driver.GetTerrainElevation(
        lat=lat, lon=lon, do_interp=True)
    hb = self.terrain_driver.GetTerrainElevation(
        lat=lat+1/3600., lon=lon+1/3600., do_interp=True)

    self.assertAlmostEqual(ha, h00, 10)
    self.assertAlmostEqual(hb, h11, 10)
    # In the middle
    hc =self.terrain_driver.GetTerrainElevation(
        lat=37.75, lon=-122.5, do_interp=True)
    exp_h = sum([h00, h01, h10, h11])/4.
    self.assertAlmostEqual(hc, exp_h, 10)

  def test_multipoints(self):
    lats = 37 + np.arange(0, 0.99, 0.01)
    lons = -122.99 + np.arange(0, 0.99, 0.01)

    elev1a = np.array([self.terrain_driver.GetTerrainElevation(lat, lon, False)
                       for (lat, lon) in zip(lats, lons)])
    elev1b = self.terrain_driver.GetTerrainElevation(lats, lons, False)
    self.assertEqual(np.max(np.abs(elev1a - elev1b)), 0)

    elev2a = np.array([self.terrain_driver.GetTerrainElevation(lat, lon, True)
                       for (lat, lon) in zip(lats, lons)])
    elev2b = self.terrain_driver.GetTerrainElevation(lats, lons, True)
    self.assertEqual(np.max(np.abs(elev2a - elev2b)), 0)

  def test_multi_twotiles(self):
    lats = 36.5 + np.arange(0.01, 0.99, 0.01)
    lons = -122.99 + np.arange(0.01, 0.99, 0.01)

    elev1a = np.array([self.terrain_driver.GetTerrainElevation(lat, lon, False)
                       for (lat, lon) in zip(lats, lons)])
    elev1b = self.terrain_driver.GetTerrainElevation(lats, lons, False)
    self.assertEqual(np.max(np.abs(elev1a - elev1b)), 0)

    elev2a = np.array([self.terrain_driver.GetTerrainElevation(lat, lon, True)
                       for (lat, lon) in zip(lats, lons)])
    elev2b = self.terrain_driver.GetTerrainElevation(lats, lons, True)
    self.assertEqual(np.max(np.abs(elev2a - elev2b)), 0)

  def test_cache(self):
    lats = 36.5 + np.arange(0.01, 0.99, 0.01)
    lons = -122.99 + np.arange(0.01, 0.99, 0.01)
    self.terrain_driver.SetCacheSize(1)
    elev = self.terrain_driver.GetTerrainElevation(lats, lons, False)
    self.assertEqual(len(self.terrain_driver._tile_cache), 1)
    self.assertEqual(len(self.terrain_driver._tile_lru), 1)

    self.terrain_driver.SetCacheSize(2)
    elev = self.terrain_driver.GetTerrainElevation(lats, lons, False)
    self.assertEqual(len(self.terrain_driver._tile_cache), 2)
    self.assertEqual(len(self.terrain_driver._tile_lru), 2)


  def test_haat(self):
    # Twin Peaks - SF
    haat, h0 = self.terrain_driver.ComputeNormalizedHaat(
        lat=37.751458, lon=-122.447831)
    self.assertAlmostEqual(haat, 249.81, 2)
    self.assertAlmostEqual(h0, 274.69, 2)
    # Ocean - far away from the coast
    haat, h0 = self.terrain_driver.ComputeNormalizedHaat(
        lat=37.50, lon=-122.999)
    self.assertEqual(haat, 0.0)
    self.assertEqual(h0, 0.0)

if __name__ == '__main__':
  unittest.main()
