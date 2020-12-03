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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import logging
import numpy as np
import unittest

from reference_models.tools import testutils
from reference_models.geo import drive
from reference_models.propagation import wf_hybrid
from reference_models.propagation import wf_itm

TERRAIN_TEST_DIR = os.path.join(os.path.dirname(__file__),
                                '..', 'geo', 'testdata', 'ned')
ITU_TEST_DIR = os.path.join(os.path.dirname(__file__),
                            '..', 'geo', 'testdata', 'itu')

logging.disable(30)
class TestWfHybrid(unittest.TestCase):

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

  def test_100m_mode(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 10.0
    lat2, lng2, height2 = 37.756559, -122.507882, 10.0 # about 50m away
    reliability = 0.5
    res = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=reliability, freq_mhz=3625.,
        region='SUBURBAN', return_internals=True)
    self.assertAlmostEqual(res.db_loss, 79.167, 3)
    self.assertEqual(res.internals['hybrid_opcode'], wf_hybrid.HybridMode.FSL)

  def test_high_height_mode(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 201.0
    lat2, lng2, height2 = 37.756559, -122.507882, 10.0 # about 50m away
    reliability = 0.5
    res = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=reliability, freq_mhz=3625.,
        region='SUBURBAN', return_internals=True)
    self.assertEqual(res.db_loss, res.internals['itm_db_loss'])
    self.assertEqual(res.internals['hybrid_opcode'],
                     wf_hybrid.HybridMode.ITM_HIGH_HEIGHT)

  def test_rural_mode(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 50.0
    lat2, lng2, height2 = 37.756559, -122.507882, 10.0 # about 50m away
    reliability = 0.5
    res = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=reliability, freq_mhz=3625.,
        region='RURAL', return_internals=True)
    self.assertEqual(res.db_loss, res.internals['itm_db_loss'])
    self.assertEqual(res.internals['hybrid_opcode'],
                     wf_hybrid.HybridMode.ITM_RURAL)

  def test_1km_mode(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.762314, -122.500973, 10.0  # 912 meters away
    reliability = 0.5
    res = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=reliability, freq_mhz=3625.,
        region='URBAN', return_internals=True)
    self.assertAlmostEqual(res.db_loss, 144.836, 3)
    self.assertEqual(res.internals['hybrid_opcode'],
                     wf_hybrid.HybridMode.EHATA_FSL_INTERP)

  def test_itm_dominant(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.754406, -122.388342, 10.0
    reliability = 0.5
    expected_itm_loss = 211.47
    res = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=reliability, freq_mhz=3625.,
        region='SUBURBAN', return_internals=True)
    self.assertAlmostEqual(res.db_loss, expected_itm_loss, 2)
    self.assertEqual(res.db_loss, res.internals['itm_db_loss'])
    self.assertEqual(res.internals['hybrid_opcode'],
                     wf_hybrid.HybridMode.ITM_DOMINANT)
    self.assertEqual(res.internals['itm_err_num'],
                     wf_hybrid.wf_itm.ItmErrorCode.WARNING)

  def test_ehata_dominant(self):
    lat1, lng1, height1 = 37.751985, -122.443890, 20.0
    lat2, lng2, height2 = 37.771594, -122.253895, 10.0
    reliability = 0.5
    expected_loss = 150.680
    res = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=reliability, freq_mhz=3625.,
        region='SUBURBAN', return_internals=True)
    self.assertAlmostEqual(res.db_loss, expected_loss, 2)
    self.assertEqual(res.internals['hybrid_opcode'],
                     wf_hybrid.HybridMode.EHATA_DOMINANT)

  def test_ehata_mean(self):
    lat1, lng1, height1 = 37.751985, -122.443890, 20.0
    lat2, lng2, height2 = 37.771594, -122.253895, 10.0
    expected_med_loss = 161.93
    expected_offset = -12.45
    self.assertAlmostEqual(wf_hybrid._GetMedianToMeanOffsetDb(3625., False),
                           expected_offset, 2)

    res_med = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=0.5, freq_mhz=3625.,
        region='SUBURBAN')
    res_mean = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=-1, freq_mhz=3625.,
        region='SUBURBAN')
    self.assertAlmostEqual(res_mean[0], res_med[0] + expected_offset, 2)

  def test_over_80km(self):
    lat1, lng1, height1 = 37.751985, -122.443890, 20.0
    lat2, lng2, height2 = 37.094745, -122.040671, 10.0  # 81km away
    expected_loss = 286.903
    expected_itm_loss = 269.067

    res = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=0.5, freq_mhz=3625.,
        region='SUBURBAN', return_internals=True)
    self.assertAlmostEqual(res.db_loss, expected_loss, 3)
    self.assertAlmostEqual(expected_itm_loss, res.internals['itm_db_loss'], 0)
    self.assertEqual(res.internals['hybrid_opcode'],
                     wf_hybrid.HybridMode.ITM_CORRECTED)

  def test_average_itm(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.754406, -122.388342, 1.5
    reliabilities = np.arange(0.01, 1.0, 0.01)
    losses = []
    for rel in reliabilities:
      res = wf_itm.CalcItmPropagationLoss(
          lat1, lng1, height1, lat2, lng2, height2,
          reliability=rel, freq_mhz=3625.)
      losses.append(res.db_loss)

    avg_res = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        reliability=-1, freq_mhz=3625.,
        region='SUBURBAN', return_internals=True)
    self.assertEqual(avg_res.internals['hybrid_opcode'],
                     wf_hybrid.HybridMode.ITM_DOMINANT)
    self.assertAlmostEqual(avg_res.db_loss,
                           -10*np.log10(np.mean(10**(-np.array(losses)/10.))),
                           5)

  def test_indoor(self):
    lat1, lng1, height1 = 37.756672, -122.508512, 20.0
    lat2, lng2, height2 = 37.754406, -122.388342, 10.0
    res_outdoor = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        cbsd_indoor=False,
        reliability=0.5, freq_mhz=3625.,
        region='SUBURBAN')
    res_indoor = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, height1, lat2, lng2, height2,
        cbsd_indoor=True,
        reliability=0.5, freq_mhz=3625.,
        region='SUBURBAN')
    self.assertEqual(res_indoor.db_loss, res_outdoor.db_loss + 15)

  def test_median_to_mean_offset(self):
    # Test median to mean offset formula on lognormal sample
    np.random.seed(1234)
    median = 80
    std = wf_hybrid.GetEHataStandardDeviation(3625, True)
    signal = -median + np.random.randn(1000000) * std
    signal_mean = 10*np.log10(np.mean(10**(signal / 10.)))
    offset = wf_hybrid._GetMedianToMeanOffsetDb(3625, True)
    self.assertAlmostEqual(median + offset, -signal_mean, 2)

  def test_small_height(self):
    lat1, lng1 = 37.756672, -122.508512
    lat2, lng2 = 37.754406, -122.388342
    res_bad = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, 0, lat2, lng2, -1,
        cbsd_indoor=False,
        reliability=0.5, freq_mhz=3625., region='SUBURBAN')
    res_expected = wf_hybrid.CalcHybridPropagationLoss(
        lat1, lng1, 1, lat2, lng2, 1,
        cbsd_indoor=False,
        reliability=0.5, freq_mhz=3625., region='SUBURBAN')
    self.assertEqual(res_bad.db_loss, res_expected.db_loss)
    self.assertEqual(res_bad.incidence_angles, res_expected.incidence_angles)

  def test_same_location(self):
    result = wf_hybrid.CalcHybridPropagationLoss(45, -80, 10, 45, -80, 10)
    self.assertEqual(result.db_loss, 0)
    self.assertTupleEqual(result.incidence_angles, (0, 0, 0, 0))


if __name__ == '__main__':
  unittest.main()
