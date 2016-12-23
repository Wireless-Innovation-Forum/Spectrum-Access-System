#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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

import waypoints
import unittest
import random

class TestDistance(unittest.TestCase):
  def test_short_distance(self):
    d = waypoints.waypoint_distances(4.0)
    self.assertEquals(2, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(4.0, d[1])

    d = waypoints.waypoint_distances(30.0)
    self.assertEquals(2, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(30.0, d[1])

  def test_medium_distance(self):
    d = waypoints.waypoint_distances(50.0)
    self.assertEquals(3, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(25.0, d[1])
    self.assertEquals(50.0, d[2])

    d = waypoints.waypoint_distances(300.0)
    self.assertEquals(11, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(30.0, d[1])
    self.assertEquals(270.0, d[9])
    self.assertEquals(300.0, d[10])

    d = waypoints.waypoint_distances(3000.0)
    self.assertEquals(101, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(300.0, d[10])
    self.assertEquals(2970.0, d[99])
    self.assertEquals(3000.0, d[100])

    d = waypoints.waypoint_distances(30000.0)
    self.assertEquals(1001, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(3000.0, d[100])
    self.assertEquals(29970.0, d[999])
    self.assertEquals(30000.0, d[1000])

    d = waypoints.waypoint_distances(45000.0)
    self.assertEquals(1501, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(3000.0, d[100])
    self.assertEquals(44970.0, d[1499])
    self.assertEquals(45000.0, d[1500])

  def test_long(self):
    d = waypoints.waypoint_distances(60000.0)
    self.assertEquals(1501, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(40.0, d[1])
    self.assertEquals(80.0, d[2])
    self.assertEquals(59960.0, d[1499])
    self.assertEquals(60000.0, d[1500])

    d = waypoints.waypoint_distances(450000.0)
    self.assertEquals(1501, len(d))
    self.assertEquals(0.0, d[0])
    self.assertEquals(300.0, d[1])
    self.assertEquals(450000.0, d[1500])

  def test_random(self):
    for i in range(0, 100):
      x = random.uniform(100, 45000)
      d = waypoints.waypoint_distances(x)
      self.assertAlmostEqual(d[1], d[3]-d[2])
      self.assertEquals(0, d[0])
      self.assertGreater(30.0, d[1])
      self.assertEquals(int(x/30.0), int(len(d)-2))

if __name__ == '__main__':
  unittest.main()

