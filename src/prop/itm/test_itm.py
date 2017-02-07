# Copyright 2016 SAS Project Authors. All Rights Reserved.
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

# This file contains a sample test run for the ITM point-to-point code
# as implemented in itm.cpp and exported for python in itm_py.cpp. See
# those files for more build/install instructions.
#
# The test vector is taken directly from the C++ version of the Fortran
# test.
#
# Usage documentation:
#   itm.point_to_point(
#       elevations,
#            The first item in the list is the number of elevation points
#            minus one. The second is the distance in meters between elevation
#            points in the profile. Thus the total distance is (first)*(second)
#            and there should be (first+1) profile elevations supplied in the
#            vector following those initial values.
#       transmitter_height_meters,  (above ground level)
#       receiver_height_meters,     (above ground level)
#       dielectric_constant,
#            Typical value is 15 for ground, 81 for water.
#       soil_conductivity,
#            Typical value is 0.005 for ground, 0.01 for fresh water, 5.0 for
#            sea water.
#       refractivity,
#            From 250 to 400. Typical value is 314. There are maps of usual
#            values based on geography available from ITU.
#       frequency_mhz,              (frequency of the emission)
#       radio_climate,
#            Values are Equatorial=1, Continental Subtropical=2, Maritime
#            Tropical=3, Desert=4, Continental Temperate (typical)=5,
#            Maritime Temperate (over land)=6, Maritime Temperate (over sea)=7
#       polarization,
#            0=horizontal, 1=vertical
#       confidence,                  (value between 0.001 and 0.999)
#            This value indicates a fraction of situations in which the actual
#            loss will not exceed the modeled loss in similar situations.
#       reliability)
#            This value indicates a fraction of the time in which the actual
#            loss will not exceed the modeled loss for a particular radio
#            station.

import itm

path = [ 156, 499,
         96,   84,   65,   46,   46,   46,   61,   41,   33,   27,   23,   19,   15,   15,   15,
         15,   15,   15,   15,   15,   15,   15,   15,   15,   17,   19,   21,   23,   25,   27,
         29,   35,   46,   41,   35,   30,   33,   35,   37,   40,   35,   30,   51,   62,   76,
         46,   46,   46,   46,   46,   46,   50,   56,   67,  106,   83,   95,  112,  137,  137,
         76,  103,  122,  122,   83,   71,   61,   64,   67,   71,   74,   77,   79,   86,   91,
         83,   76,   68,   63,   76,  107,  107,  107,  119,  127,  133,  135,  137,  142,  148,
         152, 152,  107,  137,  104,   91,   99,  120,  152,  152,  137,  168,  168,  122,  137,
         137, 170,  183,  183,  187,  194,  201,  192,  152,  152,  166,  177,  198,  156,  127,
         116, 107,  104,  101,   98,   95,  103,   91,   97,  102,  107,  107,  107,  103,   98,
         94,   91,  105,  122,  122,  122,  122,  122,  137,  137,  137,  137,  137,  137,  137,
         137, 140,  144,  147,  150,  152,  159 ]

loss, err, mode = itm.point_to_point(path, 143.9, 8.5, 15, .005, 314, 41.5, 5, 0, .5, .5)

if err != 0:
  print "FAIL: expected err=0"

if abs(loss-135.8) > 0.2:
  print "FAIL: expected 135.8, got ", loss
else:
  print "SUCCESS: expected 135.8, got ", loss

sloss, err, mode = itm.point_to_point_stat(path, 143.9, 8.5, 15, .005, 314, 41.5, 5, 0, .5,
                                           [.1, .2, .5, .8, .9], 5)
if abs(sloss[3] - loss) < 0.0001:
  print "FAIL: expected ", loss
if sloss[0] > sloss[4]:
  print "FAIL: greater loss for lower reliability parameter", sloss

