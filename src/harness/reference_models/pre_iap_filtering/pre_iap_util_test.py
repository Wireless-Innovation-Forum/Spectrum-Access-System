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

import unittest

from reference_models.pre_iap_filtering import pre_iap_util


class preIapFilteringUtilTest(unittest.TestCase):
  """The pre-IAP filtering util unit tests."""

  def create_frequency_range(self, low_freq, high_freq):
    return {'lowFrequency': low_freq, 'highFrequency': high_freq}

  def create_ppa_record(self, ppa_id, pal_ids):
    return {'id': ppa_id, 'ppaInfo': {'palId': pal_ids}}

  def create_pal_record(self, pal_id, frequency_range):
    return {
        'palId': pal_id,
        'channelAssignment': {
            'primaryAssignment': frequency_range,
        }
    }

  def test_ppa_frequency_range(self):
    self.assertDictEqual(
        self.create_frequency_range(3550, 3700),
        pre_iap_util.getPpaFrequencyRange(
            self.create_ppa_record('PPA1', ['PAL1']), [
                self.create_pal_record('PAL1',
                                       self.create_frequency_range(3550, 3700)),
                self.create_pal_record('PAL2',
                                       self.create_frequency_range(3550, 3600))
            ]))

    self.assertDictEqual(
        self.create_frequency_range(3550, 3600),
        pre_iap_util.getPpaFrequencyRange(
            self.create_ppa_record('PPA1', ['PAL2']), [
                self.create_pal_record('PAL1',
                                       self.create_frequency_range(3550, 3700)),
                self.create_pal_record('PAL2',
                                       self.create_frequency_range(3550, 3600))
            ]))

    self.assertDictEqual(
        self.create_frequency_range(3550, 3700),
        pre_iap_util.getPpaFrequencyRange(
            self.create_ppa_record('PPA1', ['PAL2', 'PAL1']), [
                self.create_pal_record('PAL1',
                                       self.create_frequency_range(3550, 3700)),
                self.create_pal_record('PAL2',
                                       self.create_frequency_range(3550, 3700))
            ]))

    # No matching PAL ID is found
    with self.assertRaises(ValueError) as context:
      pre_iap_util.getPpaFrequencyRange(
          self.create_ppa_record('PPA1', ['PAL3', 'PAL4']), [
              self.create_pal_record(
                  'PAL1', self.create_frequency_range(3550, 3700)),
              self.create_pal_record(
                  'PAL2', self.create_frequency_range(3550, 3700))
          ])

    # No matching PAL ID is found (palId is empty).
    with self.assertRaises(ValueError) as context:
      pre_iap_util.getPpaFrequencyRange(
          self.create_ppa_record('PPA1', []), [
              self.create_pal_record(
                  'PAL1', self.create_frequency_range(3550, 3700)),
              self.create_pal_record(
                  'PAL2', self.create_frequency_range(3550, 3700))
          ])

    # The frequency of the PAL records are not matching.
    with self.assertRaises(ValueError) as context:
      pre_iap_util.getPpaFrequencyRange(
          self.create_ppa_record('PPA1', ['PAL1', 'PAL2']), [
              self.create_pal_record('PAL1',
                                     self.create_frequency_range(3550, 3700)),
              self.create_pal_record('PAL2',
                                     self.create_frequency_range(3550, 3600))
          ])


if __name__ == '__main__':
  unittest.main()
