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

import logging
import os
import unittest

import numpy as np

from reference_models.geo import refractivity


TEST_DIR = os.path.join(os.path.dirname(__file__),'testdata', 'itu')
logging.disable(30)


class TestRefractivity(unittest.TestCase):

  def setUp(self):
    self.refDriver = refractivity.RefractivityIndexer()
    self.refDriver.ConfigureDataFile(TEST_DIR, do_load=False)

  def test_internals(self):
    # Test lazy loading
    self.assertTrue(self.refDriver._data is None)
    r0 = self.refDriver.Refractivity(0., 0.)
    self.assertTrue(self.refDriver._data is not None)
    self.assertEqual(self.refDriver._data.shape,
                     (self.refDriver._num_lat_rows, self.refDriver._num_lon_cols))

  def test_data(self):
    # Read data at the pole.
    r0 = self.refDriver.Refractivity(90., 0.)
    r1 = self.refDriver.Refractivity(90., 91.)
    r2 = self.refDriver.Refractivity(90., 155.4)
    self.assertEqual(r0, 317.248)
    self.assertEqual(r1, 317.248)
    self.assertEqual(r2, 317.248)

  def test_interpolation(self):
    # Change the internal data
    self.refDriver._data = np.zeros((120, 240))
    self.refDriver._data[60, 0] = 10.
    self.refDriver._data[60, 1] = 50.
    self.refDriver._data[59, 0] = 100.
    self.refDriver._data[59, 1] = 300.
    self.assertEqual(self.refDriver.Refractivity(0, 0), 10)
    self.assertEqual(self.refDriver.Refractivity(0, 0.375), 20)
    self.assertEqual(self.refDriver.Refractivity(0.375, 0), 32.5)
    self.assertEqual(self.refDriver.Refractivity(1.5, 0.375), 150)
    self.assertEqual(self.refDriver.Refractivity(0.375, 0.375), 150*0.25 + 20*0.75)

if __name__ == '__main__':
  unittest.main()
