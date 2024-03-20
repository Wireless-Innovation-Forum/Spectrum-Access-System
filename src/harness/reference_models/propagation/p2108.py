#    Copyright 2024 SAS Project Authors. All Rights Reserved.
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

from reference_models.geo import drive
from reference_models.geo import vincenty

# P.2108 section 3.2.2 variables as defined by WINNF-TS-1020, REL1Ext-R2-SGN-02
F_2108 = 3.6  # Desired frequency (GHz)
P_2108 = 50  # Desired percentage
# P.2108 variables (4b),(5b), unused by WINNF-TS-1020, REL1Ext-R2-SGN-02
# sigma_l = 4
# sigma_s = 6

# P.2108 (6) in dB, maximum clutter loss pre-calculated at d = 2km
P2108_LOSS_2KM = 30.50030179

# 8 dB reduction for DPA points: TDD activity factor of 80% and 20% Network loading factor, 10log10(0.16)
ACTIVITY_LOSS_FACTOR = 8


def calc_P2108(lat_cbsd, lon_cbsd, height_cbsd,
               lat_rx, lon_rx, is_height_cbsd_amsl=False):
  """Implements clutter loss as defined by ITU-R P.2108-1 and WINNF-TS-1020, REL1Ext-R2-SGN-02

  Inputs:
    lat_cbsd, lon_cbsd, height_cbsd: Lat/lon (deg) and height AGL (m) of CBSD
    lat_rx, lon_rx:                  Lat/lon (deg) of Rx point
    is_height_cbsd_amsl: If True, the CBSD height shall be considered as AMSL (Average
                         mean sea level).

  Returns:
    the clutter loss in db
  """
  # convert cbsd height to AGL
  if is_height_cbsd_amsl:
    altitude_cbsd = drive.terrain_driver.GetTerrainElevation(lat_cbsd, lon_cbsd)
    height_cbsd = height_cbsd - altitude_cbsd

  # return 0 if cbsd height greater than 6 or distance < 0.25
  # else return P2108 result at 2 km if distance > 2
  # else perform calculation to determine L_ctt
  if height_cbsd <= 6:
    distance, _, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd, lat_rx, lon_rx)
    if distance < 0.25:
      return 0
    elif distance >= 2:
      return P2108_LOSS_2KM
    else:
      L_l = -2 * np.log10(10 ** (-5 * np.log10(F_2108) - 12.5) + 10 ** (-16.5))  # P.2108 (4a)
      L_s = 32.98 + 23.9 * np.log10(distance) + 3 * np.log10(F_2108)  # P.2108 (5a)

      # WINNF-TS-1020, REL1Ext-R2-SGN-02 clutter loss derived from ITU-R P.2108-1 Section 3.2.2 equations
      # P.2108 (3a), remove (sigma_cb * Q_inv) term which is always 0 due to Q_inv
      # sigma_cb = np.sqrt((sigma_l ** 2 * 10 ** (-0.2 * L_l) + sigma_s ** 2 * 10 ** (-0.2 * L_s)) / (
      #           10 ** (-0.2 * L_l) + 10 ** (-0.2 * L_s)))  # P.2108 (3b)
      # Q_inv = 0  # Note: Q(x) = 0.5 when x = 0
      return -5 * np.log10(10 ** (-0.2 * L_l) + 10 ** (-0.2 * L_s))
  else:
    return 0
