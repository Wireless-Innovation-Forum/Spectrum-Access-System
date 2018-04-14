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
import unittest

from reference_models.antenna import antenna


class TestAntenna(unittest.TestCase):

  def test_pattern_gain(self):
    pattern = np.arange(360)
    gain = antenna.GetAntennaPatternGains(40, 0, pattern)
    self.assertAlmostEqual(gain, 40)
    gain = antenna.GetAntennaPatternGains(40.5, 0, pattern)
    self.assertAlmostEqual(gain, 40.5)
    gain = antenna.GetAntennaPatternGains(40.2, 20, pattern)
    self.assertAlmostEqual(gain, 20.2)
    hor_dirs = [10.5, 42.2, 25]
    gains = antenna.GetAntennaPatternGains(hor_dirs, 0, pattern)
    self.assertAlmostEqual(np.max(np.abs(
        gains - np.array([10.5, 42.2, 25]))), 0)
    gains = antenna.GetAntennaPatternGains(hor_dirs, 20, pattern)
    self.assertAlmostEqual(np.max(np.abs(
        gains - np.array([350.5, 22.2, 5]))), 0)
    gains = antenna.GetAntennaPatternGains(hor_dirs, 20, pattern, 10)
    self.assertAlmostEqual(np.max(np.abs(
        gains - np.array([360.5, 32.2, 15]))), 0)
    # Vectorized vs scalar
    hor_dirs = [3.5, 47.3, 342]
    gains = antenna.GetAntennaPatternGains(hor_dirs, 123.3, pattern, 12.4)
    for k, hor in enumerate(hor_dirs):
      gain = antenna.GetAntennaPatternGains(hor, 123.3, pattern, 12.4)
      self.assertEqual(gain, gains[k])

  def test_standard_gain(self):
    # Isotropic antenna
    gains = antenna.GetStandardAntennaGains([0, 90, 180, 270],
                                            0, None, 5)
    self.assertEqual(np.max(np.abs(
        gains - 5 * np.ones(4))), 0)
    gains = antenna.GetStandardAntennaGains([0, 90, 180, 270],
                                            None, 90, 5)
    self.assertEqual(np.max(np.abs(
        gains - 5 * np.ones(4))), 0)
    gains = antenna.GetStandardAntennaGains([0, 90, 180, 270],
                                            0, 0, 5)
    self.assertEqual(np.max(np.abs(
        gains - 5 * np.ones(4))), 0)
    gains = antenna.GetStandardAntennaGains([0, 90, 180, 270],
                                            0, 360, 5)
    self.assertEqual(np.max(np.abs(
        gains - 5 * np.ones(4))), 0)

    # Back lobe: maximum attenuation
    gain = antenna.GetStandardAntennaGains(180, 0, 120, 10)
    self.assertEqual(gain, -10)
    # At beamwidth, cutoff by 3dB (by definition)
    gain = antenna.GetStandardAntennaGains(60, 0, 120, 10)
    self.assertEqual(gain, 10-3)
    gain = antenna.GetStandardAntennaGains(5.5, 50.5, 90, 10)
    self.assertEqual(gain, 10-3)
    # Bore sight: full gain
    gain = antenna.GetStandardAntennaGains(50.5, 50.5, 90, 10)
    self.assertEqual(gain, 10)
    # At half beamwidth, -0.75dB + integer values well managed
    gain = antenna.GetStandardAntennaGains(25, 50, 100, 10)
    self.assertEqual(gain, 10-0.75)
    # At twice beamwidth, -12dB
    gain = antenna.GetStandardAntennaGains(310, 50, 100, 10)
    self.assertEqual(gain, 10-12)

    # Vectorized vs scalar
    hor_dirs = [3.5, 47.3, 342]
    gains = antenna.GetStandardAntennaGains(hor_dirs, 123.3, 90, 12.4)
    for k, hor in enumerate(hor_dirs):
      gain = antenna.GetStandardAntennaGains(hor, 123.3, 90, 12.4)
      self.assertEqual(gain, gains[k])

  def test_dpa_gain(self):
    hor_dirs = [0, 1.49, 360-1.49, 1.51, 360-1.51, 90, 320]
    gains = antenna.GetRadarNormalizedAntennaGains(hor_dirs, 0)
    self.assertEqual(np.max(np.abs(
        gains - np.array([0, 0, 0, -25, -25, -25, -25]))), 0)
    for k, hor in enumerate(hor_dirs):
      gain = antenna.GetRadarNormalizedAntennaGains(hor, 0)
      self.assertEqual(gain, gains[k])

    gains = antenna.GetRadarNormalizedAntennaGains([5, 8.6, 11.4, 20], 10)
    self.assertEqual(np.max(np.abs(
        gains - np.array([-25, 0, 0, -25]))), 0)

  def test_fss_gain(self):
    # Test the internal GSO gains
    # - diff in hor plane only
    hor_dirs = [20, 21, 21.4, 21.6, 22.9, 23.1, 26.9, 27.1, 29.1, 29.3, 67, 69]
    ver_dirs = np.zeros(len(hor_dirs))
    #   * perpendicular
    gains = antenna.GetFssAntennaGains(hor_dirs, ver_dirs,
                                       20, 0, 30, 0, 1)
    self.assertAlmostEqual(np.max(np.abs(
        gains - np.array([30, 30, 30, 30, 30,
                          32-25*np.log10(3.1),
                          32-25*np.log10(6.9),
                          32-25*np.log10(7.1),
                          32-25*np.log10(9.1),
                          32-25*np.log10(9.3),
                          32-25*np.log10(47),
                          -10]))), 0)
    #   * tangential
    gains = antenna.GetFssAntennaGains(hor_dirs, ver_dirs,
                                       20, 0, 30, 1, 0)
    self.assertAlmostEqual(np.max(np.abs(
        gains - np.array([30, 30, 30,
                          29-25*np.log10(1.6),
                          29-25*np.log10(2.9),
                          29-25*np.log10(3.1),
                          29-25*np.log10(6.9),
                          8,
                          8,
                          32-25*np.log10(9.3),
                          32-25*np.log10(47),
                          -10]))), 0)
    # - diff in ver plane only
    gains = antenna.GetFssAntennaGains(ver_dirs, hor_dirs,
                                       0, 20, 30, 0, 1)
    self.assertAlmostEqual(np.max(np.abs(
        gains - np.array([30, 30, 30, 30, 30,
                          32-25*np.log10(3.1),
                          32-25*np.log10(6.9),
                          32-25*np.log10(7.1),
                          32-25*np.log10(9.1),
                          32-25*np.log10(9.3),
                          32-25*np.log10(47),
                          -10]))), 0)


if __name__ == '__main__':
  unittest.main()
