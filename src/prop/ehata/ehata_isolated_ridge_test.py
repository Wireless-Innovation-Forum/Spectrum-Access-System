from ehata import IsolatedRidgeCorrection

import csv
import math

deltas = []
with open('testdata/isolated_ridge_test.csv') as ridge_file:
  rows = csv.reader(ridge_file)
  for row in rows:
    deltas.append(row)

with open('testdata/elevations.csv') as profiles_file:
  rows = csv.reader(profiles_file)
  target = 0
  for row in rows:
    print '\nOn row %d' % target
    profile = []
    for r in row:
       profile.append(float(r))
    profile[0] = int(profile[0])
    profile = profile[0:int(profile[0])+3]
    Kir = IsolatedRidgeCorrection(profile)

    if math.fabs(float(deltas[0][target]) - Kir) > .1:
      print('fail Kir on profile %d: %f vs %f' % (target, float(deltas[0][target]), Kir))
      exit()

    target = target + 1

print 'PASS'

