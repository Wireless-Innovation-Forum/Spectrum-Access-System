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

import logging
import numpy as np
import os
import unittest

from reference_models.geo import tropoclim


TEST_DIR = os.path.join(os.path.dirname(__file__),'testdata', 'itu')
logging.disable(30)


class TestTropoclim(unittest.TestCase):

  def setUp(self):
    self.climDriver = tropoclim.ClimateIndexer()
    self.climDriver.ConfigureDataFile(TEST_DIR, do_load=False)

  def test_internals(self):
    # Test lazy loading
    self.assertTrue(self.climDriver._data is None)
    r0 = self.climDriver.TropoClim(0., 0.)
    self.assertTrue(self.climDriver._data is not None)
    self.assertEqual(self.climDriver._data.shape,
                     (self.climDriver._num_lat_rows, self.climDriver._num_lon_cols))

  def test_data(self):
    r0 = self.climDriver.TropoClim(90, 0)
    self.assertEqual(r0, 7)
    r0 = self.climDriver.TropoClim(50, -90)
    self.assertEqual(r0, 5)
    r0 = self.climDriver.TropoClim(40, -120)
    self.assertEqual(r0, 4)
    r0 = self.climDriver.TropoClim(0, 20)
    self.assertEqual(r0, 1)
    r0 = self.climDriver.TropoClim(-30, -20)
    self.assertEqual(r0, 7)

if __name__ == '__main__':
  unittest.main()
