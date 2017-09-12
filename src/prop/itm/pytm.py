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

import itm

# Calculate the point-to-point predicted loss for a path.
# Arguments:
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
def point_to_point(elevation, transmitter_height_meters, receiver_height_meters,
                   dielectric_constant, soil_conductivity, refractivity,
                   frequency_mhz, radio_climate, polarization,
                   confidence, reliability):
  if transmitter_height_meters < 1.0:
    print 'Transmitter height less than 1m'
    return -1

  if transmitter_height_meters > 1000.0:
    raise Exception('Transmitter height greater than 1000m')

  if receiver_height_meters < 1.0:
    raise Exception('Receiver height less than 1m')

  if receiver_height_meters > 1000.0:
    raise Exception('Receiver height greater than 1000m')

  if frequency_mhz < 40.0:
    raise Exception('Frequency less than 40MHz')

  if frequency_mhz > 10000.0:
    raise Exception('Frequency greater than 10,000 MHz')

  if refractivity < 250.0:
    raise Exception('Refractivity less than 250')

  if refractivity > 400.0:
    raise Exception('Refractivity more than 400')

  if polarization != 0 and polarization != 1:
    raise Exception('Bad polarization value (not 0 or 1)')

  if (radio_climate != 1 and radio_climate != 2 and
      radio_climate != 3 and radio_climate != 4 and
      radio_climate != 5 and radio_climate != 6 and radio_climate != 7):
    raise Exception('Bad radio climate value (not 1, 2, 3, 4, 5, 6, 7)')

  if confidence < 0.0:
    raise Exception('Confidence less than 0')

  if confidence > 1.0:
    raise Exception('Confidence greater than 1')

  if reliability < 0.0:
    raise Exception('Reliability less than 0')

  if reliability > 1.0:
    raise Exception('Reliability greater than 1')

  loss, err, mode = itm.point_to_point(elevation, transmitter_height_meters, receiver_height_meters,
                                       dielectric_constant, soil_conductivity, refractivity,
                                       frequency_mhz, radio_climate, polarization,
                                       confidence, reliability)

  if err != 0:
    print 'Warning: got an applicability warning [%d] in ITM for mode %s' % (err, mode)

  return loss

def point_to_point_stat(elevation, transmitter_height_meters, receiver_height_meters,
                   dielectric_constant, soil_conductivity, refractivity,
                   frequency_mhz, radio_climate, polarization,
                   confidence, reliability):
  if transmitter_height_meters < 1.0:
    print 'Transmitter height less than 1m'
    return -1

  if transmitter_height_meters > 1000.0:
    raise Exception('Transmitter height greater than 1000m')

  if receiver_height_meters < 1.0:
    raise Exception('Receiver height less than 1m')

  if receiver_height_meters > 1000.0:
    raise Exception('Receiver height greater than 1000m')

  if frequency_mhz < 40.0:
    raise Exception('Frequency less than 40MHz')

  if frequency_mhz > 10000.0:
    raise Exception('Frequency greater than 10,000 MHz')

  if refractivity < 250.0:
    raise Exception('Refractivity less than 250')

  if refractivity > 400.0:
    raise Exception('Refractivity more than 400')

  if polarization != 0 and polarization != 1:
    raise Exception('Bad polarization value (not 0 or 1)')

  if (radio_climate != 1 and radio_climate != 2 and
      radio_climate != 3 and radio_climate != 4 and
      radio_climate != 5 and radio_climate != 6 and radio_climate != 7):
    raise Exception('Bad radio climate value (not 1, 2, 3, 4, 5, 6, 7)')

  if confidence < 0.0:
    raise Exception('Confidence less than 0')

  if confidence > 1.0:
    raise Exception('Confidence greater than 1')

  loss, err, mode = itm.point_to_point_stat(elevation, transmitter_height_meters, receiver_height_meters,
                                       dielectric_constant, soil_conductivity, refractivity,
                                       frequency_mhz, radio_climate, polarization,
                                       confidence, reliability, len(reliability))

  if err != 0:
    print 'Warning: got an applicability warning [%d] in ITM for mode %s' % (err, mode)

  return loss


# TODO: main method that takes freq/location and prints loss
