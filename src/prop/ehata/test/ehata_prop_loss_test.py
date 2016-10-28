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

      loss_db = ehata.ExtendedHata_PropagationLoss(3500, 50, 3, reg, profile)

      delta = 0.15
      if target in [39, 44, 60, 65, 67, 70]:
        delta = 0.5
        # account for variances in rolling hill correction

      if math.fabs(float(loss[0][target]) - loss_db) > delta:
        print('FAIL prop loss on profile %d: %f vs %f' % (target, float(loss[0][target]), loss_db))
        exit()
      target = target + 1

print 'PASS'

