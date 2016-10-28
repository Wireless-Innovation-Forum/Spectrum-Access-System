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

