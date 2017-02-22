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

distance = range(1,100)

hb = 50
hmVals = [1.5, 3, 4.5, 6]

region = ['Urban', 'Suburban']

for reg in region:

  loss = []
  abmloss = []
  with open('median_loss_%s.csv' % reg) as loss_file:
    rows = csv.reader(loss_file)
    for row in rows:
      loss.append(row)
  with open('median_abm_%s.csv' % reg) as loss_file:
    rows = csv.reader(loss_file)
    for row in rows:
      abmloss.append(row)

  for hmi in range(len(hmVals)):
    hm = hmVals[hmi]

    for disti in range(len(distance)):
      dist = distance[disti]

      median_loss, above_median_loss = ehata.ExtendedHata_MedianBasicPropLoss(3500, dist, hb, hm, reg)


      if math.fabs(float(loss[hmi][disti]) - median_loss) > .05:
        print('fail median loss on profile %d: %f vs %f' % (target, float(loss[hmi][disti]), median_loss))
        exit()
      if math.fabs(float(abmloss[hmi][disti]) - above_median_loss) > .05:
        print('fail above-median loss on profile %d: %f vs %f' % (target, float(abmloss[hmi][disti]), above_median_loss))
        exit()

print 'PASS'

