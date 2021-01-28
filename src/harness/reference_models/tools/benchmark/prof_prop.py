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

"""Script for profiling the propagation model timing.

Usage:
  To profile per function:
     python -m cProfile -s cumulative prof_prop.py > fn_profile.txt

  To profile per line:
    - put @profile decorator on functions to be profiled
    - run:
      kernprof -l -v prof_prop.py > line_profile.txt
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from reference_models.propagation import wf_itm
from reference_models.propagation import wf_hybrid
from reference_models.geo import drive
from reference_models.geo import vincenty

# Tx location
cbsd_lat = 40.5
cbsd_lon = -90.5

# Rx location
max_distance = 300
distance = 60
bearing = 90
freq_mhz = 3625
rx_lat, rx_lng, _ = vincenty.GeodesicPoints(cbsd_lat,cbsd_lon,
                                            distance, bearing)

def CalcHybrid(rel, rx_lat, rx_lng):
  res = wf_hybrid.CalcHybridPropagationLoss(
      cbsd_lat, cbsd_lon, 10,
      rx_lat, rx_lng, 1.5,
      False, rel, freq_mhz, 'SUBURBAN')
  return res

def CalcItm(rel, rx_lat, rx_lng):
  res = wf_itm.CalcItmPropagationLoss(
      cbsd_lat, cbsd_lon, 10,
      rx_lat, rx_lng, 1.5,
      False, rel, freq_mhz)
  return res

if __name__ == '__main__':
  # First calc to load the terrain data in cache
  print('# Pre-Loading the terrain')
  res = CalcItm(0.5, rx_lat, rx_lng)
  print('## Initial driver report')
  drive.terrain_driver.stats.Report()
  print('')
  print('# Propagation calculation')
  for k in range(1000):
    CalcItm(-1, rx_lat, rx_lng)
  print('## Final driver report')
  drive.terrain_driver.stats.Report()
