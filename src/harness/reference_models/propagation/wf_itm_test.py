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
import numpy as np
import unittest

from reference_models.geo import testutils
from reference_models.geo import drive

from reference_models.propagation import wf_itm

TERRAIN_TEST_DIR = os.path.join(os.path.dirname(__file__),
                                '..', 'geo', 'testdata', 'ned')
ITU_TEST_DIR = os.path.join(os.path.dirname(__file__),
                            '..', 'geo', 'testdata', 'itu')


class TestWfItm(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.unzip_files = testutils.UnzipTestDir(TERRAIN_TEST_DIR)
    # Mocking the ITU drivers to always return fixed values
    drive.climate_driver.TropoClim = lambda lat, lon: 5
    drive.refract_driver.Refractivity = lambda lat, lon: 314

  @classmethod
  def tearDownClass(cls):
    testutils.RemoveFiles(TERRAIN_TEST_DIR, cls.unzip_files)

  def setUp(self):
    # Reconfigure the drivers to point to geo/testdata directories
    drive.ConfigureTerrainDriver(terrain_dir=TERRAIN_TEST_DIR)
    drive.ConfigureItuDrivers(itu_dir=ITU_TEST_DIR)

  def test_los_mode(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.756559, -122.507882, 10.0
    reliability = 0.5
    res = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                        reliability=reliability, freq_mhz=3625.)
    self.assertAlmostEqual(res.db_loss, 78.7408, 4)
    self.assertAlmostEqual(res.incidence_angles.ver_cbsd, -res.incidence_angles.ver_rx, 3)
    self.assertEqual(res.internals['itm_err_num'], wf_itm.ItmErrorCode.OTHER)  # LOS mode

  def test_op_mode(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.754406, -122.388342, 10.0
    reliabilities = [0.1, 0.5, 0.9]
    expected_losses = [213.68, 214.26, 214.62]

    for rel, exp_loss in zip(reliabilities, expected_losses):
      res = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                          reliability=rel, freq_mhz=3625.)
      self.assertAlmostEqual(res.db_loss, exp_loss, 2)
      self.assertEqual(res.internals['itm_err_num'], wf_itm.ItmErrorCode.WARNING)  # Double horizon

    # Reliability list input
    res = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                        reliability=reliabilities, freq_mhz=3625.)
    for loss, exp_loss in zip(res.db_loss, expected_losses):
      self.assertAlmostEqual(loss, exp_loss, 2)

  def test_average(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.754406, -122.388342, 10.0
    reliabilities = np.arange(0.01, 1.0, 0.01)
    # vector call
    results = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                            reliability=reliabilities, freq_mhz=3625.)
    # Scalar call
    for rel, exp_loss in zip(reliabilities, results.db_loss):
      res = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                          reliability=rel, freq_mhz=3625.)
      self.assertEqual(res.db_loss, exp_loss)
    # Internal average
    avg_res = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                            reliability=-1, freq_mhz=3625.)
    self.assertAlmostEqual(avg_res.db_loss, -10*np.log10(np.mean(10**(-np.array(results.db_loss)/10.))), 5)

  def test_indoor(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.754406, -122.388342, 10.0
    # scalar version
    res_outdoor = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                                cbsd_indoor=False,
                                                reliability=0.5, freq_mhz=3625.)
    res_indoor = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                               cbsd_indoor=True,
                                               reliability=0.5, freq_mhz=3625.)
    self.assertEqual(res_indoor.db_loss, res_outdoor.db_loss + 15)
    # vector version
    reliabilities = np.arange(0.01, 1.0, 0.01)
    res_outdoor = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                                cbsd_indoor=False,
                                                reliability=reliabilities, freq_mhz=3625.)
    res_indoor = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                               cbsd_indoor=True,
                                               reliability=reliabilities, freq_mhz=3625.)
    self.assertEqual(np.max(np.abs(
        np.array(res_indoor.db_loss) - np.array(res_outdoor.db_loss) - 15)), 0)

  def test_small_height(self):
    lat1, lng1 = 37.756672, -122.508512
    lat2, lng2 = 37.754406, -122.388342

    res_bad = wf_itm.CalcItmPropagationLoss(lat1, lng1, 0, lat2, lng2, -1,
                                            cbsd_indoor=False,
                                            reliability=0.5, freq_mhz=3625.)
    res_expected = wf_itm.CalcItmPropagationLoss(lat1, lng1, 1, lat2, lng2, 1,
                                                 cbsd_indoor=False,
                                                 reliability=0.5, freq_mhz=3625.)
    self.assertEqual(res_bad.db_loss, res_expected.db_loss)
    self.assertEqual(res_bad.incidence_angles, res_expected.incidence_angles)

  def test_haat(self):
    # Twin Peaks
    haat = wf_itm.ComputeHaat(
        lat_cbsd=37.751458, lon_cbsd=-122.447831, height_cbsd=10)
    self.assertAlmostEqual(haat, 259.81, 2)
    haat = wf_itm.ComputeHaat(
        lat_cbsd=37.751458, lon_cbsd=-122.447831, height_cbsd=284.69,
        height_is_agl=False)
    self.assertAlmostEqual(haat, 259.80, 2)

    # Ocean - far away from the coast
    haat  = wf_itm.ComputeHaat(
        lat_cbsd=37.50, lon_cbsd=-122.8, height_cbsd=10)
    self.assertEqual(haat, 10)


if __name__ == '__main__':
  unittest.main()
