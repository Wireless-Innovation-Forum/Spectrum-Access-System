"""Tests for usgs_pop_driver."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import unittest

import numpy as np

import usgs_pop_driver

TESTDATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'testdata')


class UsgsPopDriverTest(unittest.TestCase):

  def setUp(self):
    self.longMessage = True

  def testLoadWrongDirRaiseException(self):
    with self.assertRaises(ValueError):
      driver = usgs_pop_driver.UsgsPopDriver(
          os.path.join(TESTDATA_DIR, 'UNKNOWN_DIR'))

  def testReadDataOk(self):
    driver = usgs_pop_driver.UsgsPopDriver(TESTDATA_DIR)
    driver.LoadRaster()
    latitudes = [37.702042, 37.721747, 37.722372]
    longitudes = [-122.414730, -122.391210, -122.395741]
    exp_values = [12686, 2500, 11359]
    densities = driver.GetPopulationDensity(
        latitudes, longitudes)
    self.assertTrue(np.all(densities == exp_values),
                    'Different densities read')

if __name__ == '__main__':
  unittest.main()
