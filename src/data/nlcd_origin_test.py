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

import logging
import os
import numpy as np
import unittest

from reference_models.tools import testutils
import nlcd_origin as nlcd

TEST_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'geo',
                        'orig_nlcd', 'hi_landcover_wimperv_9-30-08_se5.img')
                        # 'NLCD_2011_Land_Cover_L48_20190424.ige')
logging.disable(30)


class TestNlcdOrigin(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.unzip_files = testutils.UnzipTestDir(TEST_DIR)

  @classmethod
  def tearDownClass(cls):
    testutils.RemoveFiles(TEST_DIR, cls.unzip_files)

  def verify_points(self, nlcd_driver):
    # Selected isolated pixels hand picked in SF region
    # to validate correct reading
    # Twin Peaks - SF
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.751113, lon=-122.449722)
    self.assertEqual(code, 24)
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.753571, lon=-122.44803)
    self.assertEqual(code, 22)

    # Downtown - SF
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.781941, lon=-122.404195)
    self.assertEqual(code, 23)
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.779704, lon=-122.417747)
    self.assertEqual(code, 21)

    # Bay Bridge
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.794435, lon=-122.381947)
    self.assertEqual(code, 22)
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.794715, lon=-122.382446)
    self.assertEqual(code, 11)

    # Residential Sunset - SF
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.760220, lon=-122.482720)
    self.assertEqual(code, 22)
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.750036, lon=-122.51527)
    self.assertEqual(code, 11)

  def test_full_nlcd(self):
    # Test Full NLCD mode
    nlcd_driver = nlcd.NlcdOriginDriver(TEST_DIR,
                                        data_mode=-1)
    self.verify_points(nlcd_driver)

  def test_manual_load(self):
    # Test manual mode
    nlcd_driver = nlcd.NlcdOriginDriver(TEST_DIR,
                                        data_mode=0)
    nlcd_driver.CacheTileInBox(lat_min=37.7, lat_max=37.8,
                               lon_min=-122.6, lon_max=-122.3)
    self.verify_points(nlcd_driver)

  def test_auto_load1(self):
    nlcd_driver = nlcd.NlcdOriginDriver(TEST_DIR,
                                        data_mode=2,
                                        tile_size=(0.1, 0.1))
    self.verify_points(nlcd_driver)

  def test_outside_tile(self):
    # Test manual mode
    nlcd_driver = nlcd.NlcdOriginDriver(TEST_DIR,
                                        data_mode=0)
    nlcd_driver.CacheTileInBox(lat_min=37.7, lat_max=37.8,
                               lon_min=-122.6, lon_max=-122.3)
    # Outside database tiles
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.75, lon=-121.70)
    self.assertEqual(code, 0.0)
    code = nlcd_driver.GetLandCoverCodes(
        lat=37.75, lon=-122.65)
    self.assertEqual(code, 0.0)

  def test_cache(self):
    nlcd_driver = nlcd.NlcdOriginDriver(TEST_DIR,
                                        data_mode=1,
                                        tile_size=(0.1, 0.1))
    lats = 37.5 + np.arange(0.01, 0.20, 0.01)
    lons = -122.5 + np.arange(0.01, 0.20, 0.01)
    codes1 = nlcd_driver.GetLandCoverCodes(lats, lons)
    self.assertEqual(len(nlcd_driver._tile_cache), 1)
    self.assertEqual(len(nlcd_driver._tile_lru), 1)
    nlcd_driver.data_mode = 2
    codes2 = nlcd_driver.GetLandCoverCodes(lats, lons)
    self.assertEqual(len(nlcd_driver._tile_cache), 2)
    self.assertEqual(len(nlcd_driver._tile_lru), 2)
    self.assertEqual(np.max(np.abs(codes1 - codes2)), 0)

  def test_compare_modes(self):
    nlcd_driver = nlcd.NlcdOriginDriver(TEST_DIR,
                                        data_mode=1,
                                        tile_size=(0.1, 0.1))
    lats = 37.75 + np.arange(0.01, 0.30, 0.001)
    lons = -122.45 + np.arange(0.01, 0.30, 0.001)
    codes1 = nlcd_driver.GetLandCoverCodes(lats, lons)
    nlcd_driver = nlcd.NlcdOriginDriver(TEST_DIR,
                                        data_mode=-1)
    codes2 = nlcd_driver.GetLandCoverCodes(lats, lons)
    self.assertEqual(np.max(np.abs(codes1 - codes2)), 0)


if __name__ == '__main__':
  unittest.main()
