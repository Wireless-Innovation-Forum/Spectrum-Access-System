#    Copyright 2024 SAS Project Authors. All Rights Reserved.
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
import unittest

from reference_models.tools import testutils
from reference_models.geo import drive

from reference_models.propagation import p2108


TERRAIN_TEST_DIR = os.path.join(os.path.dirname(__file__),
                                '..', 'geo', 'testdata', 'ned')


class TestP2108(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.unzip_files = testutils.UnzipTestDir(TERRAIN_TEST_DIR)

  @classmethod
  def tearDownClass(cls):
    testutils.RemoveFiles(TERRAIN_TEST_DIR, cls.unzip_files)

  def setUp(self):
    # Reconfigure the drivers to point to geo/testdata directories
    drive.ConfigureTerrainDriver(terrain_dir=TERRAIN_TEST_DIR)

  def test_height_greater_than_6m(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2 = 37.765786, -122.466966
    res = p2108.calc_P2108(lat1, lng1, height1, lat2, lng2, False)
    self.assertEqual(res, 0)

  def test_distance_less_than_250m(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 5.0
    lat2, lng2 = 37.758049, -122.506323  # 246m away

    res = p2108.calc_P2108(lat1, lng1, height1, lat2, lng2, False)
    self.assertEqual(res, 0)

  def test_distance_greater_than_2km(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 5.0
    lat2, lng2 = 37.760484, -122.486052  # 2.02km away

    res = p2108.calc_P2108(lat1, lng1, height1, lat2, lng2, False)
    self.assertEqual(res, p2108.P2108_LOSS_2KM)

  def test_height_amsl(self):
    lat1, lng1, height1 = 37.740835, -122.500203, 37.7  # altitude=31.84m
    lat2, lng2 = 37.741432, -122.489361  # 958m away

    res = p2108.calc_P2108(lat1, lng1, height1, lat2, lng2, True)
    self.assertAlmostEqual(res, 30.147542, 4)

  def test_p2108_1km(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 3.0
    lat2, lng2 = 37.754629, -122.497366  # 1.01km away

    res = p2108.calc_P2108(lat1, lng1, height1, lat2, lng2, False)
    self.assertAlmostEqual(res, 30.221403, 4)


if __name__ == '__main__':
  unittest.main()
