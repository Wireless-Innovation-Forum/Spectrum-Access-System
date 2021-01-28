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

import unittest

import fss_pointing as fp

# Tests based on https://www.ngs.noaa.gov/CORS/Articles/SolerEisemannJSE.pdf
# which uses a slightly different SPHERICAL_GSO_CST than FCC 05-56
fp._GSO_SPHERICAL_CST = 0.1508  # instead of 0.1512


class TestAntenna(unittest.TestCase):

  def test_gso_elevation(self):
    # From https://www.ngs.noaa.gov/CORS/Articles/SolerEisemannJSE.pdf
    # Table 1
    self.assertAlmostEqual(fp.GsoElevation(0, 50, 50), 90)
    self.assertAlmostEqual(fp.GsoElevation(5, 50, 50), 84.1139, 3)
    self.assertAlmostEqual(fp.GsoElevation(25, 50, 50), 60.7782, 3)
    self.assertAlmostEqual(fp.GsoElevation(55, 50, 50), 27.2990, 3)
    self.assertAlmostEqual(fp.GsoElevation(80, 50, 50), 1.3291, 3)

    # Table 2
    self.assertAlmostEqual(fp.GsoElevation(45, 0, 30), 30.2785, 3)
    self.assertAlmostEqual(fp.GsoElevation(45, 0, 75), 1.8768, 3)
    self.assertAlmostEqual(fp.GsoElevation(45, 0, 77.6865), 0, 3)
    self.assertAlmostEqual(fp.GsoElevation(45, 0, -60), 12.2299, 3)

  def test_gso_azimuth(self):
    # From: https://www.ngs.noaa.gov/CORS/Articles/SolerEisemannJSE.pdf
    # Table 2
    self.assertAlmostEqual(fp.GsoAzimuth(45, 0, 0), 180)
    self.assertAlmostEqual(fp.GsoAzimuth(45, 0, 10), 165.9981, 4)
    self.assertAlmostEqual(fp.GsoAzimuth(45, 0, 30), 140.7685, 4)
    self.assertAlmostEqual(fp.GsoAzimuth(45, 0, 75), 100.7286, 4)
    self.assertAlmostEqual(fp.GsoAzimuth(45, 0, 77.6865), 98.7743, 4)
    self.assertAlmostEqual(fp.GsoAzimuth(45, 0, -60), 247.7923, 4)

  def test_gso_pointings(self):
    # From above, shall be +-30degree visibility
    pointings = fp.GsoPossiblePointings(45, 0,
                                        west_elevation_limit=30.2785,
                                        east_elevation_limit=30.2785)
    sat_lon_slots = range(-29, 30, 2)
    self.assertEqual(len(pointings), len(sat_lon_slots))
    for lon in sat_lon_slots:
      elev = fp.GsoElevation(45, 0, lon)
      azi = fp.GsoAzimuth(45, 0, lon)
      self.assertIn((azi, elev), pointings)

    # Same with further limitation in sat_orbit
    pointings = fp.GsoPossiblePointings(45, 0,
                                        west_elevation_limit=30.2785,
                                        east_elevation_limit=30.2785,
                                        west_sat_lon=-21,
                                        east_sat_lon=40)
    sat_lon_slots = range(-21, 30, 2)
    self.assertEqual(len(pointings), len(sat_lon_slots))
    for lon in sat_lon_slots:
      elev = fp.GsoElevation(45, 0, lon)
      azi = fp.GsoAzimuth(45, 0, lon)
      self.assertIn((azi, elev), pointings)

    # Same with further limitation in sat_orbit and azimuth
    pointings = fp.GsoPossiblePointings(45, 0,
                                        east_elevation_limit=30.2785,
                                        west_sat_lon=-21,
                                        east_sat_lon=40,
                                        west_azimuth_limit=166,
                                        east_azimuth_limit=140.7685)

    sat_lon_slots = range(11, 30, 2)
    self.assertEqual(len(pointings), len(sat_lon_slots))
    for lon in sat_lon_slots:
      elev = fp.GsoElevation(45, 0, lon)
      azi = fp.GsoAzimuth(45, 0, lon)
      self.assertIn((azi, elev), pointings)

    # Check the 180 degree crossover
    pointings = fp.GsoPossiblePointings(45, 180,
                                        west_sat_lon=150,
                                        east_sat_lon=-150)
    sat_lon_slots = range(180-29, 180+30, 2)
    self.assertEqual(len(pointings), len(sat_lon_slots))
    for lon in sat_lon_slots:
      elev = fp.GsoElevation(45, 180, lon)
      azi = fp.GsoAzimuth(45, 180, lon)
      self.assertIn((azi, elev), pointings)

if __name__ == '__main__':
  unittest.main()
