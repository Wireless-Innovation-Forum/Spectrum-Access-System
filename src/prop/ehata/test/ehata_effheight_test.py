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

import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import ehata

import csv
import math

heights = []
with open('effective_height_test.csv') as heights_file:
  rows = csv.reader(heights_file)
  for row in rows:
    heights.append(row)

with open('elevations.csv') as profiles_file:
  rows = csv.reader(profiles_file)
  target = 0
  for row in rows:
    profile = []
    for r in row:
       profile.append(float(r))
    profile[0] = int(profile[0])
    profile = profile[0:int(profile[0])+3]
    eff_tx_m, eff_rx_m = ehata.EffectiveHeights(50, 3, profile)
    if math.fabs(float(heights[0][target]) - eff_tx_m) > .05:
      print('fail Tx effective height on profile %d: %f vs %f' % (target, float(heights[0][target]), eff_tx_m))
      exit()
    if math.fabs(float(heights[1][target]) - eff_rx_m) > .05:
      print('fail Rx effective height on profile %d: %f vs %f' % (target, float(heights[1][target]), eff_rx_m))
      exit()
    target = target + 1

interp_profile = [10, 1000, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
eff_tx_m, eff_rx_m = ehata.EffectiveHeights(50, 3, interp_profile)
if math.fabs(47 - eff_tx_m) > .05:
  print('fail interp Tx effective height: %f vs %f' % (47, eff_tx_m))
  exit()
if math.fabs(10 - eff_rx_m) > .05:
  print('fail interp Rx effective height: %f vs %f' % (10, eff_rx_m))
  exit()

print 'PASS'

