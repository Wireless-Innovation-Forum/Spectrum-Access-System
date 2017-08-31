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

import csv
import os
import numpy as np
import random
import unittest

from reference_models.propagation.ehata import ehata

# Read a profile in test/pfls directory
# Note: reverse it to be from Tx to Rx
def ReadProfileFile(filename):
  profiles = []
  with open(filename) as fd:
    rows = csv.reader(fd)
    for row in rows:
      profile = [float(val) for val in row]
      profile[0] = int(profile[0])
      profile = profile[0:int(profile[0])+3]
      # Reverse profiles from Tx to Rx
      rev_profile = profile[0:2]
      rev_profile.extend(profile[-1:1:-1])
      profiles.append(rev_profile)

  return profiles


# Read the ITS test-inputs file defining a number of tests
def ReadTestInputs(filename):
  with open(filename) as fd:
    rows = csv.reader(fd)
    columns = rows.next()
    tests = [row for row in rows]
    return (columns, tests)
  return None


class TestEHata(unittest.TestCase):

  def setUp(self):
    self.test_dir = os.path.join(os.path.dirname(__file__), 'its', 'test')
    self.test_profile_dir = os.path.join(self.test_dir, 'pfls')
    self.columns, self.tests = ReadTestInputs(
        os.path.join(self.test_dir, 'test-inputs-wfmod.csv'))

  # Test the ITS eHata version with original testbed code from ITS
  def test_its_testbed(self):
    ehata.SetWinnForumExtensions(False)
    for test in self.tests:
      # read all data for the profile test
      scenario = test[self.columns.index('Scenario Title')]
      profile_filename = test[self.columns.index('pfl file name')]
      profile = ReadProfileFile(os.path.join(self.test_profile_dir,
                                             profile_filename))[0]
      freq_mhz = float(test[self.columns.index('f')])
      hb = float(test[self.columns.index('hb')])
      hm = float(test[self.columns.index('hm')])
      env_code = int(test[self.columns.index('env')])
      exp_ploss = float(test[self.columns.index('Path Loss(dB)')])

      ploss = ehata.ExtendedHata(profile, freq_mhz, hb, hm, env_code)
      #print "%s: %f vs %f" % (scenario, ploss, exp_ploss)
      self.assertAlmostEqual(ploss, exp_ploss, 4)

  def test_eff_height_within3km(self):
    profile = [4, 500, 1, 2, 3, 4, 5]
    eff_tx_m = ehata.CbsdEffectiveHeights(50, profile)
    self.assertEqual(50, eff_tx_m)

    eff_tx_m = ehata.CbsdEffectiveHeights(19, profile)
    self.assertEqual(20, eff_tx_m)

  def test_eff_height_within15km(self):
    profile = [9, 1000, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    eff_tx_m = ehata.CbsdEffectiveHeights(50, profile)
    self.assertEqual(47, eff_tx_m)

    eff_tx_m = ehata.CbsdEffectiveHeights(21, profile)
    self.assertEqual(20, eff_tx_m)

    eff_tx_m = ehata.CbsdEffectiveHeights(19, profile)
    self.assertEqual(20, eff_tx_m)

    profile = [5, 800, 12, 2, 3, 4, 5, 9]
    eff_tx_m = ehata.CbsdEffectiveHeights(50, profile)
    self.assertEqual(50.5, eff_tx_m)

  def test_eff_height_over15km(self):
    profile = [9, 2000, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    eff_tx_m = ehata.CbsdEffectiveHeights(50, profile)
    self.assertEqual(46.0, eff_tx_m)

    profile = [12, 2000, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40]
    eff_tx_m = ehata.CbsdEffectiveHeights(50, profile)
    self.assertEqual(46.0, eff_tx_m)


if __name__ == '__main__':
  unittest.main()
