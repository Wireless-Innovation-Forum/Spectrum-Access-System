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

import math
import vincenty
import pygc
import random

for i in range(1000):
  lat1 = random.uniform(-80, 80)
  lng1 = random.uniform(-180, 180)
  lat2 = random.uniform(-80, 80)
  lng2 = random.uniform(-80, 80)

  d, a_initial, a_final = vincenty.dist_bear_vincenty(lat1, lng1, lat2, lng2)
  a_final = a_final - 180
  if a_final < 0:
      a_final = a_final + 360
  print d, a_initial, a_final

  p = pygc.great_distance(start_latitude=lat1, start_longitude=lng1, end_latitude=lat2, end_longitude=lng2)
  print p

  assert math.fabs(d - p['distance']) < .1
  assert math.fabs(a_initial - p['azimuth']) < 1e-6
  assert math.fabs(a_final - p['reverse_azimuth']) < 1e-6

print 'direct'

for i in range(1000):
  lat = random.uniform(-80, 80)
  lng = random.uniform(-180, 180)
  dist = random.uniform(10, 1000000)
  bearing = random.uniform(-180, 180)

  latd, lngd, az = vincenty.to_dist_bear_vincenty(lat, lng, dist/1000.0, bearing)
  az = az - 180
  if az < 0:
      az = az + 360
  print latd, lngd, az

  p = pygc.great_circle(latitude=lat, longitude=lng, distance=dist, azimuth=bearing)
  print p

  assert math.fabs(latd - p['latitude']) < 1e-7
  assert math.fabs(lngd - p['longitude']) < 1e-7
  assert math.fabs(az - p['reverse_azimuth']) < 1e-7

  
