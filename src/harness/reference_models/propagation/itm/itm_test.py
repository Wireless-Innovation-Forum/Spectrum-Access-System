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

import numpy as np
import random
import unittest

from reference_models.propagation.itm import itm

# This test data comes directly from the example cases given on the NTIA/ITS
# information page at:
#   https://www.its.bldrdoc.gov/resources/radio-propagation-software/itm/itm.aspx
#   (see Fortran souce code and sample results section)
# The input data can be found in the file called qkpfldat.txt
# The expected output can be found in the file called qkpflanx.txt
# Profile path corresponds to: CRYSTAL PALACE TO MURSLEY, ENGLAND
##
##  QKPFL TEST 1, PATH 2200 (MEASURED MEDIAN LB=133.2 DB)
##  CRYSTAL PALACE TO MURSLEY, ENGLAND
##
##            DISTANCE        77.8 KM
##           FREQUENCY        41.5 MHZ
##     ANTENNA HEIGHTS   143.9     8.5 M
##   EFFECTIVE HEIGHTS   240.5    18.4 M
##    TERRAIN, DELTA H         89. M
##
##  POL=0, EPS=15., SGM=  .005 S/M
##  CLIM=5, NS=314., K= 1.368
##  PROFILE- NP= 156, XI=  .499 KM
##
##     A DOUBLE-HORIZON PATH
##     DIFFRACTION IS THE DOMINANT MODE
##
##  ESTIMATED QUANTILES OF BASIC TRANSMISSION LOSS (DB)
##     FREE SPACE VALUE-  102.6 DB
##
##        RELIA-    WITH CONFIDENCE
##        BILITY     50.0    90.0    10.0
##
##          1.0     128.6   137.6   119.6
##         10.0     132.2   140.8   123.5
##         50.0     135.8   144.3   127.2
##         90.0     138.0   146.5   129.4
##         99.0     139.7   148.4   131.0
##  QKPFL TEST 2, PATH 1979 (MEASURED MEDIAN LB=149.5 DB)
##  CRYSTAL PALACE TO MURSLEY, ENGLAND
##
##            DISTANCE        77.8 KM
##           FREQUENCY       573.3 MHZ
##     ANTENNA HEIGHTS   194.0     9.1 M
##   EFFECTIVE HEIGHTS   292.5    19.0 M
##    TERRAIN, DELTA H         91. M
##
##  POL=0, EPS=15., SGM=  .005 S/M
##  CLIM=5, NS=314., K= 1.368
##  PROFILE- NP= 156, XI=  .499 KM
##
##     A DOUBLE-HORIZON PATH
##     DIFFRACTION IS THE DOMINANT MODE
##
##  ESTIMATED QUANTILES OF BASIC TRANSMISSION LOSS (DB)
##     FREE SPACE VALUE-  125.4 DB
##
##        RELIA-    WITH CONFIDENCE
##        BILITY     50.0    90.0    10.0
##
##          1.0     144.3   154.1   134.4
##         10.0     150.9   159.5   142.3
##         50.0     157.6   165.7   149.4
##         90.0     161.6   169.9   153.3
##         99.0     164.9   173.6   156.2

PROFILE = [156, 77800./156.,
           96.,  84.,  65.,  46.,  46.,  46.,  61.,  41.,  33.,  27.,  23.,  19.,  15.,  15.,  15.,
           15.,  15.,  15.,  15.,  15.,  15.,  15.,  15.,  15.,  17.,  19.,  21.,  23.,  25.,  27.,
           29.,  35.,  46.,  41.,  35.,  30.,  33.,  35.,  37.,  40.,  35.,  30.,  51.,  62.,  76.,
           46.,  46.,  46.,  46.,  46.,  46.,  50.,  56.,  67., 106.,  83.,  95., 112., 137., 137.,
           76., 103., 122., 122.,  83.,  71.,  61.,  64.,  67.,  71.,  74.,  77.,  79.,  86.,  91.,
           83.,  76.,  68.,  63.,  76., 107., 107., 107., 119., 127., 133., 135., 137., 142., 148.,
           152., 152., 107., 137., 104.,  91.,  99., 120., 152., 152., 137., 168., 168., 122., 137.,
           137., 170., 183., 183., 187., 194., 201., 192., 152., 152., 166., 177., 198., 156., 127.,
           116., 107., 104., 101.,  98.,  95., 103.,  91.,  97., 102., 107., 107., 107., 103.,  98.,
           94.,  91., 105., 122., 122., 122., 122., 122., 137., 137., 137., 137., 137., 137., 137.,
           137., 140., 144., 147., 150., 152., 159.,
]


class TestItm(unittest.TestCase):

  def test_qkpfl_path2200_its(self):
    confidence_vals = [0.5, 0.9, 0.1]
    reliability_vals = [0.01, 0.1, 0.5, 0.9, 0.99]
    expected_losses = [128.6, 137.6, 119.6,
                       132.2, 140.8, 123.5,
                       135.8, 144.3, 127.2,
                       138.0, 146.5, 129.4,
                       139.7, 148.4, 131.0]
    frequency = 41.5
    height1 = 143.9
    height2 = 8.5
    refractivity = 314.0  # Typical
    refractivity_final=True
    dielectric = 15  # Typical for ground
    conductivity = 0.005  # Typical for ground
    climate = 5  # Continental temperate
    polarization = 0  # Vertical
    mdvar = 12
    k = 0
    for reliability in reliability_vals:
      for confidence in confidence_vals:
        loss, err, mode = itm.point_to_point(PROFILE, height1, height2,
                                             dielectric, .005, refractivity,
                                             frequency, climate, polarization,
                                             confidence, reliability,
                                             mdvar, refractivity_final)
        self.assertAlmostEqual(loss, expected_losses[k], 1)
        k+=1

  def test_qkpfl_path1979_its(self):
    confidence_vals = [0.5, 0.9, 0.1]
    reliability_vals = [0.01, 0.1, 0.5, 0.9, 0.99]
    expected_losses = [144.3, 154.1, 134.4,
                       150.9, 159.5, 142.3,
                       157.6, 165.7, 149.4,
                       161.6, 169.9, 153.3,
                       164.9, 173.6, 156.2]

    frequency = 573.3
    height1 = 194.0
    height2 = 9.1
    refractivity = 314.0  # Typical
    refractivity_final=True
    dielectric = 15  # Typical for ground
    conductivity = 0.005  # Typical for ground
    climate = 5  # Continental temperate
    polarization = 0  # Vertical
    mdvar = 12
    k = 0
    for reliability in reliability_vals:
      for confidence in confidence_vals:
        loss, err, mode = itm.point_to_point(PROFILE, height1, height2,
                                             dielectric, .005, refractivity,
                                             frequency, climate, polarization,
                                             confidence, reliability,  mdvar,
                                             refractivity_final)
        self.assertAlmostEqual(loss, expected_losses[k], 1)
        k+=1

  def test_default_arg(self):
    frequency = 573.3
    height1 = 194.0
    height2 = 9.1
    refractivity = 314.0  # Typical
    dielectric = 15  # Typical for ground
    conductivity = 0.005  # Typical for ground
    climate = 5  # Continental temperate
    polarization = 0  # Vertical
    confidence = 0.5
    reliability = 0.5
    # Expected default arguments
    mdvar = 12
    refractivity_final = False

    loss1, _, _ = itm.point_to_point(PROFILE, height1, height2,
                                     dielectric, .005, refractivity,
                                     frequency, climate, polarization,
                                     confidence, reliability,
                                     mdvar, refractivity_final)
    loss2, _, _ = itm.point_to_point(PROFILE, height1, height2,
                                     dielectric, .005, refractivity,
                                     frequency, climate, polarization,
                                     confidence, reliability)
    self.assertEqual(loss1, loss2)

  def test_reliabilities(self):
    # test scalar vs vector version
    frequency = 573.3
    height1 = 194.0
    height2 = 9.1
    refractivity = 314.0  # Typical
    dielectric = 15  # Typical for ground
    conductivity = 0.005  # Typical for ground
    climate = 5  # Continental temperate
    polarization = 0  # Vertical
    confidence = 0.5
    mdvar = 12
    refractivity_final = False

    reliabilities = np.arange(0.1, 1.0, 0.1)
    losses, _, _ = itm.point_to_point(PROFILE, height1, height2,
                                      dielectric, .005, refractivity,
                                      frequency, climate, polarization,
                                      confidence, reliabilities)
    self.assertEqual(len(losses), len(reliabilities))

    for rel, exp_loss in zip(reliabilities, losses):
      loss, _, _ = itm.point_to_point(PROFILE, height1, height2,
                                      dielectric, .005, refractivity,
                                      frequency, climate, polarization,
                                      confidence, rel)
      self.assertEqual(loss, exp_loss)


if __name__ == '__main__':
  unittest.main()
