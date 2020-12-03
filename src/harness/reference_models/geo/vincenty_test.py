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

import numpy as np
import pygc
import random
import unittest

from reference_models.geo import vincenty


def geodesic_iterative(lat1, lon1, lat2, lon2, num_points):
  """Original function using a dual iterative approach.
  """
  geodesic = [(lat1, lon1)]
  lat, lon = lat1, lon1
  dist, bearing, _ = vincenty.GeodesicDistanceBearing(lat, lon, lat2, lon2)
  step_km = dist / (float(num_points-1))
  for _ in range(1, num_points-1):
    lat, lon, _ = vincenty.GeodesicPoint(lat, lon, step_km, bearing)
    geodesic.append((lat, lon))
    _, bearing, _ = vincenty.GeodesicDistanceBearing(lat, lon, lat2, lon2)

  geodesic.append((lat2, lon2))
  return geodesic


class TestVincenty(unittest.TestCase):

  def test_distbear_whensamepoints(self):
    self.assertEqual(vincenty.GeodesicDistanceBearing(38, -80, 38, -80),
                     (0, 0, 0))

  def test_distbear(self):
    random.seed(69)
    for _ in range(1000):
      lat1 = random.uniform(-70, 70)
      lng1 = random.uniform(-170, 170)
      lat2 = lat1 + random.uniform(-10, 10)  # up to about 1000km
      lng2 = lng1 + random.uniform(-10, 10)

      d, az, rev_az = vincenty.GeodesicDistanceBearing(lat1, lng1, lat2, lng2)
      self.assertTrue(az >= 0.0 and az < 360 and rev_az >= 0 and rev_az < 360)
      p = pygc.great_distance(start_latitude=lat1, start_longitude=lng1,
                              end_latitude=lat2, end_longitude=lng2)

      self.assertAlmostEqual(d*1000.0, p['distance'], 2)  # cm precision
      self.assertAlmostEqual(az, p['azimuth'], 9)
      self.assertAlmostEqual(rev_az, p['reverse_azimuth'], 9)

  def test_point(self):
    random.seed(69)
    for _ in range(1000):
      lat = random.uniform(-80, 80)
      lng = random.uniform(-180, 180)
      dist = random.uniform(10, 1000000)
      bearing = random.uniform(-180, 180)

      latd, lngd, rev_az = vincenty.GeodesicPoint(lat, lng, dist/1000.0, bearing)
      self.assertTrue(rev_az >= 0 and rev_az < 360)
      p = pygc.great_circle(latitude=lat, longitude=lng, distance=dist, azimuth=bearing)
      self.assertAlmostEqual(latd, p['latitude'])
      self.assertAlmostEqual(lngd, p['longitude'])
      self.assertAlmostEqual(rev_az, p['reverse_azimuth'])

  def test_points(self):
    distances = [5,10,50, 100, 500, 1000, 5000]
    lat0 = 45
    lng0 = -122
    bearing = 33
    lats, lngs, rev_azis = vincenty.GeodesicPoints(lat0, lng0, distances, bearing)
    self.assertTrue(isinstance(lats, list))
    # Test with ndarray
    lats2, lngs2, rev_azis2 = vincenty.GeodesicPoints(lat0, lng0, np.array(distances), bearing)
    self.assertTrue(isinstance(lats2, np.ndarray))
    self.assertEqual(np.max(np.abs(np.array(lats) - lats2)), 0)
    self.assertEqual(np.max(np.abs(np.array(lngs) - lngs2)), 0)
    self.assertEqual(np.max(np.abs(np.array(rev_azis) - rev_azis2)), 0)
    # Test work with scalar
    lat, lng, rev_azi = vincenty.GeodesicPoints(lat0, lng0, distances[-1], bearing)
    self.assertTrue(np.isscalar(lat))
    self.assertEqual(lat, lats[-1])
    self.assertEqual(lng, lngs[-1])
    self.assertEqual(rev_azi, rev_azis[-1])
    # Test against scalar version
    for k, dist in enumerate(distances):
      lat, lng, rev_azi = vincenty.GeodesicPoint(lat0, lng0, dist, bearing)
      self.assertEqual(lat, lats[k])
      self.assertEqual(lng, lngs[k])
      self.assertEqual(rev_azi, rev_azis[k])

  def test_sampling(self):
    lat0, lng0 = 44.0, -122.0
    lat10, lng10 = 43.0, -122.0
    lat11, lng11 = 44.0, -121.0

    # Compare with dual iterative implementation (well used initially)
    lats11, lons11 = vincenty.GeodesicSampling(lat0, lng0, lat11, lng11, 1500)
    pts11 = list(zip(lats11, lons11))
    pts11it = geodesic_iterative(lat0, lng0, lat11, lng11, 1500)
    diff = np.array(pts11) - np.array(pts11it)
    self.assertLess(np.max(np.abs(diff)), 1e-10)

    # Special case North south, longitude constant. lat delta constant
    lats10, lons10 = vincenty.GeodesicSampling(lat0, lng0, lat10, lng10, 51)
    lon_offs = lons10 - lng0
    self.assertEqual(np.max(np.abs(lon_offs)), 0)

    lat_diffs = lats10[1:] - lats10[:-1]
    self.assertAlmostEqual(np.max(lat_diffs), -0.02, 5)
    self.assertAlmostEqual(np.min(lat_diffs), -0.02, 5)

if __name__ == '__main__':
  unittest.main()
