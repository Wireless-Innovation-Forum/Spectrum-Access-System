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

import numpy
import math
import sys

from pykml.factory import KML_ElementMaker as KML
from lxml import etree

import vincenty

# This function computes the waypoint distances along a total
# distance given in meters.
# It uses the algorithm of attempting to find evenly-spaced
# distances as close to 30m separations as possible, up to
# a total distance of 45000m.
# Above that distance, it uses points defining 1500 equal
# separations.
# The waypoints returned will be N+1, with the first value
# of 0 and the last of 'total_distance'
# If total_distance <= 30, only two waypoints will be
# returned: 0 and total_distance.
def waypoint_distances(total_distance):
  if total_distance <= 30.0:
    return [0, total_distance]

  if total_distance >= 45000.0:
    return [t for t in numpy.linspace(0, total_distance, 1500 + 1)]

  N = math.ceil(total_distance/30.0)
  return [t for t in numpy.linspace(0, total_distance, N+1)]

# This function returns the waypoint latitudes and longitudes
# to be used for the path between the given latlng coordinates.
# Uses vincenty waypointing.
def waypoints(lat1, lng1, lat2, lng2):
  d, az, raz = vincenty.dist_bear_vincenty(lat1, lng1, lat2, lng2)
  dist = waypoint_distances(d*1000.0)

  way = [ [lat1, lng1] ]
  for i in range(1, len(dist)):
    d = dist[i]/1000.0
    b = az
    lt, ln, az_nn = vincenty.to_dist_bear_vincenty(lat1, lng1, d, b)
    way.append([lt, ln])

  return way

# When run as a command, emit a KML file with the waypoints in it.
# command line arguments are lat/lng of first point and lat/lng of second point.
if __name__ == '__main__':
  lat = 32
  lng = -111
  latt = 32.124
  lngt = -110.81

  way = waypoints(float(sys.argv[1]), float(sys.argv[2]),
                  float(sys.argv[3]), float(sys.argv[4]))
  #print way

  coords = []
  for w in way:
      coords.append('%f,%f' % (w[1], w[0]))
  coordinates = KML.coordinates(' '.join(coords))
  doc = KML.kml(KML.Document(
    KML.Placemark(KML.name('waypoints'),
                  KML.LineString(coordinates))))
  print etree.tostring(etree.ElementTree(doc))

