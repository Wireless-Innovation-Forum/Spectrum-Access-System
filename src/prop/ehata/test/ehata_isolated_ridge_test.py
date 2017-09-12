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

deltas = []
with open('isolated_ridge_test.csv') as ridge_file:
  rows = csv.reader(ridge_file)
  for row in rows:
    deltas.append(row)

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
    Kir = ehata.IsolatedRidgeCorrection(profile)

    if math.fabs(float(deltas[0][target]) - Kir) > .1:
      print('fail Kir on profile %d: %f vs %f' % (target, float(deltas[0][target]), Kir))
      exit()

    target = target + 1

print 'PASS'

