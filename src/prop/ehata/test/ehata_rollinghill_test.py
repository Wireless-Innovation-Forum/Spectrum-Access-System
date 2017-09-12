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

kvals = []
with open('rolling_hill_test.csv') as hills_file:
  rows = csv.reader(hills_file)
  for row in rows:
    kvals.append(row)

with open('elevations.csv') as profiles_file:
  rows = csv.reader(profiles_file)
  target = 0
  for row in rows:
    print '\nOn row %d' % target
    profile = []
    for r in row:
       profile.append(float(r))
    profile[0] = int(profile[0])
    profile = profile[0:int(profile[0])+3]
    Krh, Kh, Khf = ehata.RollingHillyCorrection(profile)

    delta = .15

    if target in [29, 39, 44, 60, 62, 65, 66, 67, 70]:
      delta = .5
                     # note: for these values, the matlab test code has a
                     # problem with the CDF. There are a bunch of values
                     # at 121, and the interpolation function is ignoring
                     # that the delta is all in the first bit, and so under-estimates
                     # the median height by a bit (less than 1m). This is enough to throw
                     # the loss estimate by half a db or so.
                     # (After discussions, fixed up this issue, but the CDF treatment is
                     # still offset a bit.)

    if math.fabs(float(kvals[0][target]) - Krh) > delta:
      print('fail Krh on profile %d: %f vs %f' % (target, float(kvals[0][target]), Krh))
      exit()
    if math.fabs(float(kvals[1][target]) - Kh) > delta:
      print('fail Kh on profile %d: %f vs %f' % (target, float(kvals[1][target]), Kh))
      exit()
    if math.fabs(float(kvals[2][target]) - Khf) > delta:
      print('fail Khf on profile %d: %f vs %f' % (target, float(kvals[2][target]), Khf))
      exit()
    target = target + 1

print 'PASS'

