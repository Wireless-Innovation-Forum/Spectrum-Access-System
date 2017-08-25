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

"""Simple wrapper module for ITS E-Hata module with WinnForum extensions.
"""

try:
  from reference_models.propagation.ehata import ehata_its
except:
  raise Exception('E-Hata extension module not available. Please compile it using:\n'
                '  python setup.py build_ext -i')


def SetWinnForumExtensions(on):
  """Activates/Deactivate the Winnforum extensions.
  By default they are ON.
  """
  ehata_its.SetWinnForumExtensions(on)

def ExtendedHata(its_elev, freq_mhz, height_tx, height_rx, region_code):
    """Computes the E-Hata propagation path loss.

    Inputs:
      its_elev : Terrain profile in ITS format:
                 - pfl[0] = number of elevation points - 1
                 - pfl[1] = step size, in meters
                 - pfl[2..N] = elevation above mean sea level, in meters
      freq_mhz:  frequency (MHz).
      height_tx: height of transmitter (meters).
      height_rx: height of receiver (meters).
      region_code: environment code among:
              22 = suburban
              23 or 24 = urban
              other = rural
    Returns:
      the path loss in dB.
    """
    step_meters = its_elev[1]
    if step_meters <= 25:
      raise Exception("E-HATA model does not support profile step below 25m.")
    return ehata_its.ExtendedHata(its_elev, freq_mhz, height_tx, height_rx, region_code)


def MedianBasicPropLoss(freq_mhz, height_tx, height_rx, dist_km, region_code):
    """Computes the Median Basic propagation loss.

    Differs from ExtendedHata() by not applying the various internal corrections.

    Inputs:
      freq_mhz:  frequency (MHz).
      height_tx: height of transmitter (meters).
      height_rx: height of receiver (meters).
      dist_km: distance between Tx and Rx (km)
      region_code: environment code among:
              22 = suburban
              23 or 24 = urban
              other = rural
    Returns:
      the pathloss in dB.
    """
    return ehata_its.MedianBasicPropLoss(freq_mhz, height_tx, height_rx, dist_km, region_code)
