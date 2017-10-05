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
    wf_itm.climateDriver.TropoClim = lambda lat, lon: 5
    wf_itm.refractDriver.Refractivity = lambda lat, lon: 314

  @classmethod
  def tearDownClass(cls):
    testutils.RemoveFiles(TERRAIN_TEST_DIR, cls.unzip_files)

  def setUp(self):
    # Reconfigure the drivers to point to geo/testdata directories
    wf_itm.ConfigureTerrainDriver(terrain_dir=TERRAIN_TEST_DIR)
    wf_itm.ConfigureItuDrivers(itu_dir=ITU_TEST_DIR)

  def test_los_mode(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.756559, -122.507882, 10.0
    reliability = 0.5
    res = wf_itm.CalcItmPropagationLoss(lat1, lng1, height1, lat2, lng2, height2,
                                        reliability=reliability, freq_mhz=3625.)
    self.assertAlmostEqual(res.db_loss, 78.7408, 4)
    self.assertEqual(res.internals['itm_err_num'], wf_itm.ItmErrorCode.OTHER)  # LOS mode

  def test_op_mode(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.754406, -122.388342, 10.0
    reliabilities = [0.1, 0.5, 0.9]
    expected_losses = [213.72, 214.30, 214.66]

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
    self.assertAlmostEqual(avg_res.db_loss, 10*np.log10(np.mean(10**(np.array(results.db_loss)/10.))), 5)

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


  def test_hor_angles(self):
    # Using the ITM test profile Path2200
    PROFILE = [156, 77800./156.,
           96.,  84.,  65.,  46.,  46.,  46.,  61.,  41.,  33.,  27.,  23.,  19.,  15.,  15.,  15.,
           15.,  15.,  15.,  15.,  15.,  15.,  15.,  15.,  15.,  17.,  19.,  21.,  23.,  25.,  27.,
           29.,  35.,  46.,  41.,  35.,  30.,  33.,  35.,  37.,  40.,  35.,  30.,  51.,  62.,  76.,
           46.,  46.,  46.,  46.,  46.,  46.,  50.,  56.,  67., 106.,  83.,  95., 112., 137., 137.,
           76., 103., 122., 122.,  83.,  71.,  61.,  64.,  67.,  71.,  74.,  77.,  79.,  86.,  91.,
           83.,  76.,  68.,  63.,  76., 107., 107., 107., 119., 127., 133., 135., 137., 142., 148.,
           152., 152., 107., 137., 104.,  91.,  99., 120., 152., 152., 137., 168., 168., 122., 137.,
           137., 170., 183., 183., 187., 194., 201., 192., 152., 152., 166., 177., 198., 156., 127.,
           116., 107., 104., 101.,  98.,  95., 103.,  91.,  97., 102., 107., 107., 107., 103.,  98.,
           94.,  91., 105., 122., 122., 122., 122., 122., 137., 137., 137., 137., 137., 137., 137.,
           137., 140., 144., 147., 150., 152., 159.,]
    refractivity = 314.
    a0, a1, d0, d1 = wf_itm.GetHorizonAngles(PROFILE, 143.9, 8.5, refractivity)
    self.assertAlmostEqual(a0, np.arctan(-0.003900)*180./np.pi, 4)
    self.assertAlmostEqual(a1, np.arctan(0.000444)*180./np.pi, 4)
    self.assertAlmostEqual(d0, 55357.7, 1)
    self.assertAlmostEqual(d1, 19450.0, 1)

if __name__ == '__main__':
  unittest.main()
