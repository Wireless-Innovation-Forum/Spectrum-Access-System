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

mpaths = []
with open('mixed_path_test.csv') as mpaths_file:
  rows = csv.reader(mpaths_file)
  for row in rows:
    mpaths.append(row)

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
    Kmp = ehata.MixedPathCorrection(profile, [float(i) == 0.0 for i in profile])

    if math.fabs(float(mpaths[0][target]) - Kmp) > .1:
      print('fail Kmp on profile %d: %f vs %f' % (target, float(mpaths[0][target]), Kmp))
      exit()

    target = target + 1

print 'PASS'

