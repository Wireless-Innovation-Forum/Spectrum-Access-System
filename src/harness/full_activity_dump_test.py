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
"""Tests for the Full Activity Dump object."""

import unittest
from full_activity_dump import FullActivityDump


class FullActivityDumpTest(unittest.TestCase):
  """Full Activity Dump Object unit tests."""

  def test_get_data(self):
    """Tests that the data can be requested by record type."""
    fad = FullActivityDump({
        'cbsd': [1, 2, 3, 10, 11, 12],
        'esc_sensor': [4, 5, 6],
        'zone': [7, 8, 9]
    })
    self.assertDictEqual(fad.getData(), {
        'cbsd': [1, 2, 3, 10, 11, 12],
        'esc_sensor': [4, 5, 6],
        'zone': [7, 8, 9]
    })

  def test_cbsd_get(self):
    """Tests that the cbsd data can be requested through GetCbsdRecords."""
    fad = FullActivityDump({
        'cbsd': [1, 2, 3, 10, 11, 12],
        'esc_sensor': [4, 5, 6],
        'zone': [7, 8, 9]
    })
    self.assertEqual(fad.getCbsdRecords(), [1, 2, 3, 10, 11, 12])

  def test_filter_by_content(self):
    """Tests that the data can be filtered."""
    fad = FullActivityDump({
        'cbsd': [1, 2, 3, 10, 11, 12],
        'esc_sensor': [4, 5, 6],
        'zone': [7, 8, 9]
    })
    odd_numbers_only = lambda x: x % 2
    self.assertEqual(fad.getCbsdRecords(filters=[odd_numbers_only]), [1, 3, 11])

  def test_filter_does_not_modify_underlying_data(self):
    """Tests that data filtering does not affect the underlying data."""
    fad = FullActivityDump({
        'cbsd': [1, 2, 3, 10, 11, 12],
        'esc_sensor': [4, 5, 6],
        'zone': [7, 8, 9]
    })
    odd_numbers_only = lambda x: x % 2
    fad.getCbsdRecords(filters=[odd_numbers_only]), [1, 3, 11]
    self.assertEqual(fad.getCbsdRecords(), [1, 2, 3, 10, 11, 12])

  def test_set_cbsd_record(self):
    """Tests that the cbsd data setter and getter works."""
    fad = FullActivityDump({})
    fad.setCbsdRecords([13, 14, 15])
    self.assertEqual(fad.getCbsdRecords(), [13, 14, 15])
    self.assertDictEqual(fad.getData(), {
        'cbsd': [13, 14, 15],
        'esc_sensor': [],
        'zone': []
    })

  def test_esc_sensor_records_set_get(self):
    """Tests that the esc sensor data setter and getter works."""
    fad = FullActivityDump({})
    fad.setEscSensorRecords([13, 14, 15])
    self.assertEqual(fad.getEscSensorRecords(), [13, 14, 15])
    self.assertDictEqual(fad.getData(), {
        'cbsd': [],
        'esc_sensor': [13, 14, 15],
        'zone': []
    })

  def test_zone_records_set_get(self):
    """Tests that the zone data setter and getter works."""
    fad = FullActivityDump({})
    fad.setZoneRecords([13, 14, 15])
    self.assertEqual(fad.getZoneRecords(), [13, 14, 15])
    self.assertDictEqual(fad.getData(), {
        'cbsd': [],
        'esc_sensor': [],
        'zone': [13, 14, 15]
    })

  def test_get_cbsd_record_returns_copy(self):
    """The cbsd data returned is a copy."""
    fad = FullActivityDump({
        'cbsd': [1, 2, 3, 10, 11, 12],
        'esc_sensor': [4, 5, 6],
        'zone': [7, 8, 9]
    })
    fad.getCbsdRecords()[1] = 1000
    self.assertEqual(fad.getCbsdRecords(), [1, 2, 3, 10, 11, 12])

  def test_get_cbsd_record_returns_copy_with_filter(self):
    """The cbsd data returned when a filter is applied is a copy."""
    fad = FullActivityDump({
        'cbsd': [1, 2, 3, 10, 11, 12],
        'esc_sensor': [4, 5, 6],
        'zone': [7, 8, 9]
    })
    fad.getCbsdRecords([lambda x: True])[1] = 1000
    self.assertEqual(fad.getCbsdRecords(), [1, 2, 3, 10, 11, 12])

  def test_unfilled_fields_exist_in_output(self):
    """An empty list will be added for missing fields in the input."""
    fad = FullActivityDump({})
    self.assertDictEqual(fad.getData(), {
        'cbsd': [],
        'esc_sensor': [],
        'zone': []
    })
