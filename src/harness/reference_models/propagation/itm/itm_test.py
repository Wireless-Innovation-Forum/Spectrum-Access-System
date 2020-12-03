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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

import numpy as np

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

# Utility function to compute the vertical incidence angles at CBSD and Rx
# This code is derived from the qlrps() routine in itm.py, as specified
# in R2-SGN-21.
# NOTE:
#   This routine was initially used in the Winnforum ITM model, before replacement by
#   the angles directly calculated by the hzns() routine it used to replicate.
#   Keeping it as part of a unit test just for non regression test purposes.
def _GetHorizonAnglesLegacy(its_elev, height_cbsd, height_rx, refractivity):
  """Gets the horizon angles given a terrain profile.

  Derived from ITM hzns() routine as specified in R2-SGN-21.

  Inputs:
    its_elev:   Terrain profile in ITM format
                  - pfl[0] = number of terrain points + 1
                  - pfl[1] = step size, in meters
                  - pfl[i] = elevation above mean sea level, in meters
    height_cbsd:Height of the CBSD
    height_rx:  Height of the reception point

  Returns:
    a tuple of:
      ver_cbsd:      Vertical incidence angle. Positive value means upwards.
      ver_rx:        Vertical incidence angle. Positive value means upwards.
      hor_dist_cbsd: Horizon distance from CBSD (ie diffraction edge)
      hor_dist_rx:   Horizon distance from Rx (ie diffraction edge).
  """
  num_points = int(its_elev[0])
  step = its_elev[1]
  dist = num_points * step

  # Find the refractivity at the average terrain height
  start_avg = int(3.0 + 0.1 * num_points)
  end_avg = num_points - start_avg + 6
  zsys = np.mean(its_elev[start_avg-1:end_avg])
  refractivity *= np.exp(-zsys/9460.0)

  # Find the ray down-curvature per meter
  gma = 157e-9
  gme = gma*(1.0 - 0.04665 * np.exp(refractivity/179.3))

  alt_cbsd = its_elev[2] + height_cbsd
  alt_rx = its_elev[num_points+2] + height_rx
  qc = 0.5 * gme
  q = qc * dist
  # theta0 and theta1 the slopes, dl0 and dl1 the horizon distances
  theta1 = (alt_rx - alt_cbsd) / dist
  theta0 = theta1 - q
  theta1 = -theta1 - q
  dl0 = dist
  dl1 = dist

  if num_points >= 2:
    sa = 0.0
    sb = dist
    wq = True
    for i in range(1, num_points):
      sa += step
      sb -= step
      q = its_elev[i+2] - (qc*sa + theta0) * sa - alt_cbsd
      if q > 0.0:
        theta0 += q/sa
        dl0 = sa
        wq = False
      if not wq:
        q = its_elev[i+2] - (qc*sb + theta1) * sb - alt_rx
        if q > 0.0:
          theta1 += q/sb
          dl1 = sb

  return (np.arctan(theta0) * 180/np.pi,
          np.arctan(theta1) * 180/np.pi,
          dl0,
          dl1)


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
        loss, ver0, ver1, err, mode = itm.point_to_point(PROFILE, height1, height2,
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
        loss, ver0, ver1, err, mode = itm.point_to_point(PROFILE, height1, height2,
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

    loss1, _, _, _, _ = itm.point_to_point(PROFILE, height1, height2,
                                     dielectric, .005, refractivity,
                                     frequency, climate, polarization,
                                     confidence, reliability,
                                     mdvar, refractivity_final)
    loss2, _, _, _, _ = itm.point_to_point(PROFILE, height1, height2,
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
    losses, _, _, _, _ = itm.point_to_point(PROFILE, height1, height2,
                                      dielectric, .005, refractivity,
                                      frequency, climate, polarization,
                                      confidence, reliabilities)
    self.assertEqual(len(losses), len(reliabilities))

    for rel, exp_loss in zip(reliabilities, losses):
      loss, _, _, _, _ = itm.point_to_point(PROFILE, height1, height2,
                                      dielectric, .005, refractivity,
                                      frequency, climate, polarization,
                                      confidence, rel)
      self.assertEqual(loss, exp_loss)

  def test_horizon_angles(self):
    refractivity = 314.
    a0, a1, d0, d1 = _GetHorizonAnglesLegacy(PROFILE, 143.9, 8.5, refractivity)
    _, v0, v1, _, _ = itm.point_to_point(PROFILE, 143.9, 8.5,
                                         dielectric=15, conductivity=.005,
                                         refractivity=refractivity,
                                         freq_mhz=41.5, climate=5,
                                         polarization=0, confidence=0.5, reliabilities=0.5)
    self.assertAlmostEqual(a0, np.arctan(-0.003900)*180./np.pi, 4)
    self.assertAlmostEqual(a1, np.arctan(0.000444)*180./np.pi, 4)
    self.assertAlmostEqual(d0, 55357.7, 1)
    self.assertAlmostEqual(d1, 19450.0, 1)
    # test exactness of new method vs old method
    self.assertEqual(a0, v0)
    self.assertEqual(a1, v1)

  def test_horizon_angles_los(self):
    refractivity = 314.
    PROFILE = [5, 28.5, 10, 10, 8, 9, 11, 12]
    a0, a1, _, _ = _GetHorizonAnglesLegacy(PROFILE, 100, 50, refractivity)
    _, v0, v1, _, _ = itm.point_to_point(PROFILE, 100, 50,
                                         dielectric=15, conductivity=.005,
                                         refractivity=refractivity,
                                         freq_mhz=41.5, climate=5,
                                         polarization=0, confidence=0.5, reliabilities=0.5)
    self.assertEqual(a0, v0)
    self.assertEqual(a1, v1)


if __name__ == '__main__':
  unittest.main()
