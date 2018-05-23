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
import numpy as np
import unittest
from reference_models.common import data
from reference_models.interference import interference as interf


TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

class FreqRange(object):
  """Use for ducj\k typing objects with freq tange requirmeent."""
  def __init__(self, low, high):
    self.low_frequency = low*1.e6
    self.high_frequency = high*1.e6


class TestAggregateInterference(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    pass

  def setUp(self):
    pass

  def tearDown(self):
    pass

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


if __name__ == '__main__':
  unittest.main()
