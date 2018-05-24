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

import os
import json
import mock
import numpy as np
import unittest

from reference_models.common import data
from reference_models.tools import entities
from reference_models.tools import testutils
from reference_models.geo import vincenty
from reference_models.antenna import antenna
from reference_models.propagation import wf_hybrid
from reference_models.propagation import wf_itm
from reference_models.interference import interference as interf


TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

class FreqRange(object):
  """Used for duck typing objects with freq range requirmeent."""
  def __init__(self, low, high):
    self.low_frequency = low*1.e6
    self.high_frequency = high*1.e6


class TestAggInterf(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.fss_record = json.load(open(os.path.join(TEST_DIR, 'fss_ut.json')))

  def setUp(self):
    self.original_itm = wf_itm.CalcItmPropagationLoss
    self.original_hybrid = wf_hybrid.CalcHybridPropagationLoss
    self.fss_antenna = antenna.GetFssAntennaGains

  def tearDown(self):
    wf_hybrid.CalcHybridPropagationLoss = self.original_hybrid
    wf_itm.CalcItmPropagationLoss = self.original_itm
    antenna.GetFssAntennaGains = self.fss_antenna

  def test_getFssMaskLoss(self):
    constraint = FreqRange(3550, 3650)
    # Grant must overlap with the constraint
    with self.assertRaises(ValueError):
      grant = FreqRange(3680, 3690)
      interf.getFssMaskLoss(grant, constraint)
    # Integrated power of grant in constraint band correct
    # - simple 1MHz grant within 50MHz
    grant = FreqRange(3630, 3631)
    exp_loss = 0.5 + 19.5 * 0.6
    self.assertAlmostEqual(interf.getFssMaskLoss(grant, constraint), exp_loss)
    # - simple 1MHz grant outside 50MHz
    grant = FreqRange(3530, 3531)
    exp_loss = 0.5 + 50 * 0.6 + 69.5 * 0.25
    self.assertAlmostEqual(interf.getFssMaskLoss(grant, constraint), exp_loss)
    # - 20MHz in between the 50MHz edge - inequal split
    grant = FreqRange(3595, 3615)
    exp_losses1 = 0.5 + (35.5 + np.arange(15)) * 0.6
    exp_losses2 = 0.5 + 50 * 0.6 + (0.5+np.arange(5)) * 0.25
    exp_loss = (sum(10**(-loss/10.) for loss in exp_losses1) +
                sum(10**(-loss/10.) for loss in exp_losses2)) / 20
    exp_loss = -10*np.log10(exp_loss)
    self.assertAlmostEqual(interf.getFssMaskLoss(grant, constraint), exp_loss)
    # - grant overlapping the constraint
    grant = FreqRange(3645, 3655)
    exp_losses = 0.5 + (0.5 + np.arange(5)) * 0.6
    exp_loss = sum(10**(-loss/10.) for loss in exp_losses) / 5
    exp_loss = -10*np.log10(exp_loss)
    self.assertAlmostEqual(interf.getFssMaskLoss(grant, constraint), exp_loss)
    # - high constraint not aligned to 5MHz multiple
    constraint = FreqRange(3550, 3652.25)
    grant = FreqRange(3630, 3631)
    exp_loss = 0.5 + (19.5+2.25) * 0.6
    self.assertAlmostEqual(interf.getFssMaskLoss(grant, constraint), exp_loss)

  def test_computeFssBlocking(self):
    # Mock things propag and FSS antenna. -70dBm at 30km
    wf_itm.CalcItmPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=70 - 30.0)
    antenna.GetFssAntennaGains = mock.create_autospec(antenna.GetFssAntennaGains,
                                                      return_value=2.8)
    import ipdb; ipdb.set_trace()
    # Create FSS and a CBSD at 30km
    fss_point, fss_info, _ = data.getFssInfo(TestAggInterf.fss_record)
    fss_freq_range = (3650e6, 3750e6)
    cbsd_lat, cbsd_lon, _ = vincenty.GeodesicPoint(fss_point[1], fss_point[0], 30, 0)
    cbsd = entities.CBSD_TEMPLATE_CAT_A_OUTDOOR._replace(
      latitude=cbsd_lat, longitude=cbsd_lon)
    grant = entities.ConvertToCbsdGrantInfo([cbsd], 3640, 3680)[0]
    constraint = data.ProtectionConstraint(fss_point[1], fss_point[0],
                                           3550e6, fss_freq_range[0],
                                           data.ProtectedEntityType.FSS_BLOCKING)

    itf = interf.computeInterferenceFssBlocking(grant, constraint, fss_info,
                                                grant.max_eirp)
    self.assertAlmostEqual(itf,
                           20 + # EIRP/MHZ
                           10 + # 10MHz effective bandwidth
                           -70 # pathloss
                           + 2.8 # FSS antenna gain
                           - 3.1634, # FSS mask loss for adjacent 10MHz
                           4)

  def test_computeFssCoChannel(self):
    # Mock things propag and FSS antenna. -70dBm at 30km
    wf_itm.CalcItmPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=70 - 30.0)
    antenna.GetFssAntennaGains = mock.create_autospec(antenna.GetFssAntennaGains,
                                                      return_value=2.8)

    # Create FSS and a CBSD at 30km
    fss_point, fss_info, _ = data.getFssInfo(TestAggInterf.fss_record)
    fss_freq_range = (3652e6, 3750e6)
    cbsd_lat, cbsd_lon, _ = vincenty.GeodesicPoint(fss_point[1], fss_point[0], 30, 0)
    cbsd = entities.CBSD_TEMPLATE_CAT_A_OUTDOOR._replace(
      latitude=cbsd_lat, longitude=cbsd_lon)
    grant = entities.ConvertToCbsdGrantInfo([cbsd], 3645, 3660)[0]
    constraint = data.ProtectionConstraint(fss_point[1], fss_point[0],
                                           fss_freq_range[0], fss_freq_range[1],
                                           data.ProtectedEntityType.FSS_CO_CHANNEL)

    itf = interf.computeInterferenceFssCochannel(grant, constraint, fss_info,
                                                 grant.max_eirp)
    self.assertAlmostEqual(itf,
                           20 + # EIRP/MHZ
                           9.0309 + # 8MHz effective bandwidth
                           -70 # pathloss
                           + 2.8 # FSS antenna gain
                           - 0.5, # inband filter
                           4)


if __name__ == '__main__':
  unittest.main()
