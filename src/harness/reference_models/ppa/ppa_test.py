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
import json

import shapely.geometry as sgeo

import util
from reference_models.geo import drive
from reference_models.geo import vincenty
from reference_models.geo import utils
from reference_models.propagation import wf_hybrid
from reference_models.tools import testutils

from reference_models.ppa import ppa

TEST_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

class TestPpa(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    # Change the Default county directory to test_data
    drive.ConfigureCountyDriver(TEST_DIR)
    # Load the common setup to all tests
    user_id = 'pal_user_id_0'
    pal_record_filenames = ['pal_record_1.json', 'pal_record_2.json']
    device_filenames = ['device_b.json', 'device_c.json']
    pal_low_frequency = 3550000000
    pal_high_frequency = 3650000000
    cls.devices = [json.load(open(os.path.join(TEST_DIR, device_filename)))
                   for device_filename in device_filenames]
    cls.pal_records = [json.load(open(os.path.join(TEST_DIR, pal_record_filename)))
                   for pal_record_filename in pal_record_filenames]
    cls.pal_records = util.makePalRecordsConsistent(
        cls.pal_records, pal_low_frequency, pal_high_frequency, user_id)

  def setUp(self):
    self.original_hybrid = wf_hybrid.CalcHybridPropagationLoss

  def tearDown(self):
    wf_hybrid.CalcHybridPropagationLoss = self.original_hybrid

  def assertAlmostSamePolygon(self, poly1, poly2, tol_km2=0.001):
    self.assertTrue(utils.GeometryArea(poly1.difference(poly2)) < tol_km2)
    self.assertTrue(utils.GeometryArea(poly2.difference(poly1)) < tol_km2)

  def test_SimplePpaCircle(self):
    # Configuring for -96dBm circle at 16km includes
    wf_hybrid.CalcHybridPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=(96+30-0.1) - 16.0)
    expected_ppa = sgeo.Polygon(
        [vincenty.GeodesicPoint(
            TestPpa.devices[0]['installationParam']['latitude'],
            TestPpa.devices[0]['installationParam']['longitude'],
            dist_km=16.0, bearing=angle)[1::-1]  # reverse to lng,lat
         for angle in xrange(360)])

    ppa_zone = ppa.PpaCreationModel(TestPpa.devices[0:1], TestPpa.pal_records[0:1])
    ppa_zone = json.loads(ppa_zone)

    self.assertAlmostSamePolygon(
        utils.ToShapely(ppa_zone), expected_ppa, 0.001)

  def test_ClippedPpaByCounty(self):
    # Configuring for -96dBm circle above 40km
    wf_hybrid.CalcHybridPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=(96+30-0.1) - 45.0)
    expected_ppa = sgeo.Polygon([(-80.3, 30.3), (-80.7, 30.3),
                                 (-80.7, 30.7), (-80.3, 30.7)])

    ppa_zone = ppa.PpaCreationModel(TestPpa.devices[0:1], TestPpa.pal_records[0:1])
    ppa_zone = json.loads(ppa_zone)

    self.assertAlmostSamePolygon(
        utils.ToShapely(ppa_zone), expected_ppa, 0.001)

  def test_ClippedPpaByCountyWithSmallHoles(self):
    # Configuring for -96dBm circle above 40km
    wf_hybrid.CalcHybridPropagationLoss = testutils.FakePropagationPredictor(
        dist_type='REAL', factor=1.0, offset=(96+30-0.1) - 45.0)

    ppa_zone = ppa.PpaCreationModel(TestPpa.devices[1:], TestPpa.pal_records[1:])
    ppa_zone = json.loads(ppa_zone)

    county_zone = utils.ToShapely(
        drive.county_driver.GetCounty('06027000100')
        ['features'][0]['geometry'])
    self.assertTrue(utils.ToShapely(ppa_zone).buffer(-1e-6).within(county_zone))


if __name__ == '__main__':
  unittest.main()
