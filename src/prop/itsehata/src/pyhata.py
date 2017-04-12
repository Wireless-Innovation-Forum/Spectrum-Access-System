# Copyright 2017 SAS Project Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This module wraps the ITM implementation, checking validity of
# input parameters and returning error messages if there are any
# out-of-bounds values.

import ehata

# eHata point-to-point loss model.
# elevation is the ITM-like elevation profile data. The first element is the number of
# elevations minus one. The second is the distance in meters between points. The rest
# (first+1) of the points are profile elevations in meters.
# transmitter_height_meters is the structure height
# receiver_height_meters is the structure height
# land_category is the NLCD land category -- 23/24 is urban, 22 is suburban, else is rural
def point_to_point(elevation, transmitter_height_meters, receiver_height_meters,
                   frequency_mhz, land_category):

  (loss, breakpoint, att_1km, att_100km, h_b_eff, h_m_eff, pfl10, pfl50, pfl90, deltah, dist,
   hzn0, hzn1, avg0, avg1,
   theta_m, beta, iend_over_sea, hedge, single_horizon,
   slope_max, slope_min, trace) = ehata.point_to_point(elevation, frequency_mhz,
                                                transmitter_height_meters, receiver_height_meters,
                                                land_category)

  dbg = {}
  dbg['breakpoint'] = breakpoint
  dbg['att_1km'] = att_1km
  dbg['att_100km'] = att_100km
  dbg['h_b_eff'] = h_b_eff
  dbg['h_m_eff'] = h_m_eff
  dbg['pfl10'] = pfl10
  dbg['pfl50'] = pfl50
  dbg['pfl90'] = pfl90
  dbg['delta_h'] = deltah
  dbg['distance'] = dist
  dbg['horizon'] = [hzn0, hzn1]
  dbg['avg'] = [avg0, avg1]
  dbg['theta_m'] = theta_m
  dbg['beta'] = beta
  dbg['iend_over_sea'] = iend_over_sea
  dbg['hedge'] = hedge
  dbg['single_horizon'] = single_horizon
  dbg['slope_max'] = slope_max
  dbg['slope_min'] = slope_min
  dbg['trace_code'] = trace

  return loss, dbg



