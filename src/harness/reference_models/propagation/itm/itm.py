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

"""Simple wrapper module for ITS ITM module.
"""
import numpy as np

try:
  from reference_models.propagation.itm import itm_its
except:
  raise Exception('ITM extension module not available. Please compile it using:\n'
                  '  python setup.py build_ext -i')

def point_to_point(its_elev, height_tx, height_rx,
                   dielectric, conductivity,
                   refractivity, freq_mhz,
                   climate, polarization,
                   confidence, reliabilities,
                   mdvar=12, refract_is_final=False):
  """Computes the ITM propagation path loss.

  Inputs:
    its_elev:   Terrain profile in ITS format from transmitter to receiver::
                 - pfl[0] = number of elevation points - 1
                 - pfl[1] = step size, in meters
                 - pfl[2..N] = elevation above mean sea level, in meters
    height_tx:  Height of transmitter (meters).
    height_rx:  Height of receiver (meters).
    dielectric: Dielectric constant (relative permittivity) of the ground.
                  Typical values are 15 for ground, 81 for water.
    conductivity: Conductivity of the ground (S/m).
                  Typical values are 0.005 for ground, 0.01 for fresh water, 5 for sea water
    refractivity: Refractivity of the atmosphere.
                  Should be between 250 and 400 (Reasonable default is 314).
    freq_mhz:   Frequency (MHz).
    climate:    Climate code among:
                  1: 'Equatorial'
                  2: 'Continental Subtropical'
                  3: 'Maritime Tropical'
                  4: 'Desert'
                  5: 'Continental Temperate'
                  6: 'Maritime Temperate, Over Land'
                  7: 'Maritime Temperate, Over Sea'
    polarization: Signal polarization:
                    0: horizontal
                    1: vertical
    confidence: Confidence factor [0.01..0.99].
    reliabilities: Reliability factor [0.01..0.99].
                   Two type of input supported:
                     - scalar value: will return a scalar path_loss output
                     - sequence of values: will return a list of corresponding
                       path_loss output
    mdvar:      Mode of variability.
    refract_is_final: boolean - If True, do not correct the refractivity
                      with average altitude.

  Returns:
     a tuple of:
       path_loss : the path loss in dB,
                   either a scalar (if reliability is scalar) or a list
       str_mode: A string information on the operating conditions among:
           "Line-Od-Sight Mode"
           "Single Horizon, Diffraction Dominant"
           "Double Horizon, Diffraction Dominant"
           "Single Horizon, Troposcatter Dominant"
           "Double Horizon, Troposcatter Dominant"
       err_num:  An 'error' code:
           1- Warning: Some parameters are nearly out of range.
                       Results should be used with caution.
           2- Note: Default parameters have been substituted for impossible ones.
           3- Warning: A combination of parameters is out of range.
                       Results are probably invalid.
           Other-  Warning: Some parameters are out of range.
                   Results are probably invalid.
  """
  if np.isscalar(reliabilities):
    return itm_its.point_to_point(its_elev, height_tx, height_rx,
                                  dielectric, conductivity, refractivity,
                                  freq_mhz, climate, polarization,
                                  confidence, reliabilities,
                                  mdvar, refract_is_final)
  else:
    reliabilities = list(reliabilities)
    return itm_its.point_to_point_rels(its_elev, height_tx, height_rx,
                                       dielectric, conductivity, refractivity,
                                       freq_mhz, climate, polarization,
                                       confidence, reliabilities,
                                       mdvar, refract_is_final)
