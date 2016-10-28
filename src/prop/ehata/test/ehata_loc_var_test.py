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

