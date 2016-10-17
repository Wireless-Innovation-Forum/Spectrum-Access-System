from ehata import GeneralSlopeCorrection

import csv
import math

slopes = []
with open('testdata/general_slope_test.csv') as slopes_file:
  rows = csv.reader(slopes_file)
  for row in rows:
    slopes.append(row)

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
    Kgs = GeneralSlopeCorrection(profile)

    delta = .15

    if math.fabs(float(slopes[0][target]) - Kgs) > delta:
      print('fail Kgs on profile %d: %f vs %f' % (target, float(slopes[0][target]), Kgs))
      exit()
    target = target + 1

print 'PASS'

