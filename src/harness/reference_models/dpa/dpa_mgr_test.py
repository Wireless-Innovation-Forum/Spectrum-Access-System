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
import unittest
import numpy as np

from reference_models.tools import testutils
from reference_models.tools import entities
from reference_models.propagation import wf_itm

from reference_models.dpa import dpa_mgr


class TestDpa(unittest.TestCase):

  def setUp(self):
    self.original_itm = wf_itm.CalcItmPropagationLoss

  def tearDown(self):
    wf_itm.CalcItmPropagationLoss = self.original_itm

  def test_channelization(self):
    channels = dpa_mgr.GetDpaProtectedChannels([(3550, 3650)], is_portal_dpa=False)
    self.assertListEqual(channels, [(f, f+10) for f in range(3550, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3500, 3650)], is_portal_dpa=False)
    self.assertListEqual(channels, [(f, f+10) for f in range(3540, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3500, 3650)], is_portal_dpa=True)
    self.assertListEqual(channels, [(f, f+10) for f in range(3500, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3500, 3550), (3550, 3650)],
                                               is_portal_dpa=True)
    self.assertListEqual(channels, [(f, f+10) for f in range(3500, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3500, 3600), (3550, 3650)],
                                               is_portal_dpa=True)
    self.assertListEqual(channels, [(f, f+10) for f in range(3500, 3650, 10)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3572, 3585)], is_portal_dpa=False)
    self.assertListEqual(channels, [(3570, 3580), (3580, 3590)])
    channels = dpa_mgr.GetDpaProtectedChannels([(3572, 3575)], is_portal_dpa=False)
    self.assertListEqual(channels, [(3570, 3580)])



if __name__ == '__main__':
  unittest.main()
