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

# See the test_results/aggregate_interference_unit_test_calc_sheet.xlsx
# for a detail on the calculations.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json
import os
import unittest

from reference_models.common import data
from reference_models.interference import aggregate_interference
from reference_models.interference import interference as interf
from reference_models.tools import testutils


TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')


def json_load(fname):
  with open(fname) as fd:
    return json.load(fd)



class TestAggregateInterference(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    # Load the list of CBSD records with registration and grant details
    cbsd_filename = ['cbsd_uut_ut.json', 'cbsd_th1_ut.json']
    cbsd_list = []
    for cbsd_file in cbsd_filename:
      cbsd_record = json_load(os.path.join(TEST_DIR, cbsd_file))
      cbsd_list.append(cbsd_record)
    cls.cbsd_list = data.getAllGrantInfoFromCbsdDataDump(cbsd_list)
    # Load the protection entity data with overlapping frequency of CBSD grants
    cls.fss_record = json_load(os.path.join(TEST_DIR, 'fss_ut.json'))
    cls.ppa_record = json_load(os.path.join(TEST_DIR, 'ppa_ut.json'))
    cls.ppa_cbsd_list = data.getAllGrantInfoFromCbsdDataDump(cbsd_list, ppa_record=cls.ppa_record)
    cls.pal_record = json_load(os.path.join(TEST_DIR, 'pal_ut.json'))
    cls.gwpz_record = json_load(os.path.join(TEST_DIR, 'gwpz_ut.json'))
    cls.esc_record = json_load(os.path.join(TEST_DIR, 'esc_ut.json'))

  def setUp(self):
    self.original_interference = interf.computeInterference

  def tearDown(self):
    interf.computeInterference = self.original_interference


  def test_AggregateInterferenceFssCochannel(self):
    expected_interference = {34.4116: {-100.57114: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, \
        2.2316393176900284, 2.2316393176900284, 0, 0, 0, 0, 0, 0, 0, 0]}}

    interf.computeInterference = testutils.FakeInterferenceCalculator()
    allowed_interference = aggregate_interference.calculateAggregateInterferenceForFssCochannel(
                             TestAggregateInterference.fss_record, TestAggregateInterference.cbsd_list)
    self.assertSameInterference(allowed_interference, expected_interference)

  def test_AggregateInterferenceFssBlocking(self):
    expected_interference = {34.4116: {-100.57114: [4.462898399659984]}}

    interf.computeInterference = testutils.FakeInterferenceCalculator()
    allowed_interference = aggregate_interference.calculateAggregateInterferenceForFssBlocking(
                             TestAggregateInterference.fss_record, TestAggregateInterference.cbsd_list)
    self.assertSameInterference(allowed_interference, expected_interference)

  def test_AggregateInterferenceEsc(self):
    expected_interference = {34.41029: {-100.56683: [0, 0, 2.229908301599665, 2.229908301599665,\
         0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2.2323074278051225, 2.2323074278051225,\
          0, 0, 0, 0]}}

    interf.computeInterference = testutils.FakeInterferenceCalculator()

    allowed_interference = aggregate_interference.calculateAggregateInterferenceForEsc(
                             TestAggregateInterference.esc_record, TestAggregateInterference.cbsd_list)
    self.assertSameInterference(allowed_interference, expected_interference)

  def test_AggregateInterferencePpa(self):
    expected_interference = {34.40888888888889: {-100.57222222222222: [2.5022498449008137,\
        2.5022498449008137]}, 34.40944444444444: {-100.57277777777779: [2.5022498449008053,\
        2.5022498449008053], -100.57222222222222: [2.50256995666338, 2.50256995666338]}}

    interf.computeInterference = testutils.FakeInterferenceCalculator()
    allowed_interference = aggregate_interference.calculateAggregateInterferenceForPpa(
                             TestAggregateInterference.ppa_record,
                             [TestAggregateInterference.pal_record],
                             TestAggregateInterference.ppa_cbsd_list)
    self.assertSameInterference(allowed_interference, expected_interference)

  def test_AggregateInterferenceGwpz(self):
    expected_interference = {34.40888888888889: {-100.57222222222222: [2.5022498449008137,\
         2.5022498449008137, 0, 0, 0]}, 34.40944444444444: {-100.57277777777779: [2.5022498449008053,\
         2.5022498449008053, 0, 0, 0], -100.57222222222222: [2.50256995666338, 2.50256995666338,
          0, 0, 0]}}

    interf.computeInterference = testutils.FakeInterferenceCalculator()
    allowed_interference = aggregate_interference.calculateAggregateInterferenceForGwpz(
                             TestAggregateInterference.gwpz_record, TestAggregateInterference.cbsd_list)
    self.assertSameInterference(allowed_interference, expected_interference)

  def assertSameInterference(self, allowed_interference, expected_interference):
    return self.assertEqual(expected_interference, allowed_interference)


if __name__ == '__main__':
  unittest.main()
