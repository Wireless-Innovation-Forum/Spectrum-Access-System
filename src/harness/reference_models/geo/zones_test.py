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


import numpy as np
import os
import unittest
import geojson
import shapely.geometry as sgeo
from shapely import ops

from reference_models.geo import zones

#TEST_DIR = os.path.join(os.path.dirname(__file__),'testdata', 'zones')


class TestZones(unittest.TestCase):
  # Simplistic tests which only check the proper reading of the files.

  def test_read_protection(self):
    z = zones.GetCoastalProtectionZone()
    self.assertTrue(z.is_valid)
    self.assertTrue(z.area > 80)

  def test_read_exclusion(self):
    z = zones.GetExclusionZones()
    self.assertTrue(z.is_valid)
    self.assertTrue(z.area > 3 and z.area < 4)

  def test_read_dpa(self):
    z = zones.GetDpaZones()
    for name, zone in z.items():
      self.assertTrue(zone.is_valid)
    self.assertAlmostEqual(z['east_dpa_5'].area, 6, 1)

  def test_read_usborder(self):
    z = zones.GetUsBorder()
    self.assertTrue(z.is_valid)
    us_area = 9.8e6
    approx_area = z.area * 110**2 * np.cos(44*np.pi/180)
    self.assertTrue(approx_area > us_area * 0.9 and
                    approx_area < us_area * 1.1)

  def test_read_urban_areas(self):
    z = zones.GetUrbanAreas()
    exp_area = 150000  # Should be instead 275000 ??
    approx_area = z.area * 110**2 * np.cos(44*np.pi/180)
    self.assertTrue(z.is_valid)
    self.assertTrue(approx_area > exp_area * 0.9 and
                    approx_area < exp_area * 1.1)


if __name__ == '__main__':
  unittest.main()
