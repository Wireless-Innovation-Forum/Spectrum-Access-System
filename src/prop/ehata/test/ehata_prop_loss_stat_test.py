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

import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import ehata

import csv
import math

region = ['Urban', 'Suburban', 'DenseUrban']

for reg in region:

  loss = []
  with open('prop_loss_%s.csv' % reg) as loss_file:
    rows = csv.reader(loss_file)
    for row in rows:
      loss.append(row)

  with open('elevations.csv') as profiles_file:
    rows = csv.reader(profiles_file)
    target = 0
    for row in rows:
      print '\nOn row %d of %s' % (target, reg)
      profile = []
      for r in row:
         profile.append(float(r))
      profile[0] = int(profile[0])
      profile = profile[0:int(profile[0])+3]

      loss_db = ehata.ExtendedHata_PropagationLossStat(3500, 50, 3, reg, profile, [.01, .5, .99])

      delta = 0.15
      if target in [39, 44, 60, 65, 67, 70]:
        delta = 0.5
        # account for variances in rolling hill correction

      if math.fabs(float(loss[0][target]) - loss_db[1]) > delta:
        print('FAIL prop loss stat test on profile %d: %f vs %f' % (target, float(loss[0][target]), loss_db[1]))
        exit()
      if loss_db[0] > loss_db[2]:
        print('FAIL prop loss stat test on profile %d: %f vs %f' % (target, loss_db[0], loss_db[2]))
        exit()
      target = target + 1

print 'PASS'

