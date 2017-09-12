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

kvars = []
with open('location_variability_test.csv') as vars_file:
  rows = csv.reader(vars_file)
  for row in rows:
    kvars.append(row)

stdev_u = ehata.EHataStdDevUrban(3500.0)
stdev_su = ehata.EHataStdDevSuburban(3500.0)

if math.fabs(stdev_u - float(kvars[0][1])) > 0.05:
  print 'FAIL urban stdev %f vs %s' % (stdev_u, kvars[0][1])
  exit()
if math.fabs(stdev_su - float(kvars[0][2])) > 0.05:
  print 'FAIL suburban stdev %f vs %s' % (stdev_su, kvars[0][2])
  exit()

print 'PASS'

