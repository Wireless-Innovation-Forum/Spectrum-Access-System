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

"""Test utilities.

Provides a fake propagation engine that can be used to replace the actual models
for unit testing functional modules.
"""
import numpy as np
from enum import Enum
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm
from reference_models.antenna import antenna
from reference_models.interference import interference as interf
from reference_models.propagation import wf_hybrid


class FakePropagationPredictor(object):
  """Fake propagation model for testing.

  This model predicts a simplistic path loss equal to the distance
  multiplies by `factor` + `offset`. The distance can be either:
    - L1 degree distance: |dlat| + |dlng|
    - L2 degree distance: sqrt(dlat**2 + dlng**2)
    - Real distance: as given by vincenty method

  The incidence angle are the angles in the flattened lat/lon space.

  It can be used as a fake replacement for both `CalcItmPropagationLoss()`
  and `CalcHybridPropagationLoss()`, as following:
    wf_itm.CalcItmPropagationLoss = FakePropagationPredictor()
    wf_hybrid.CalcHybridPropagationLoss = FakePropagationPredictor()

  Attributes:
    factor: the multiplying factor to the distance in degrees
    offset: an offset
    dist_type: 'L1', 'L2' or 'REAL'
  """

  def __init__(self, factor=1., offset=50, dist_type='REAL'):
    """Initializes attributes - See class description."""
    self.factor = factor
    self.offset = offset
    self.dist_type = dist_type

  def __call__(self,
               lat_cbsd,
               lon_cbsd,
               height_cbsd,
               lat_rx,
               lon_rx,
               height_rx,
               cbsd_indoor=False,
               reliability=0.5,
               freq_mhz=3625.,
               its_elev=None,
               region=None):
    """See `CalcItmPropagationLoss()` for specification."""
    if self.dist_type == 'L1':
      dist = np.abs(lat_rx - lat_cbsd) + np.abs(lon_rx - lon_cbsd)
    elif self.dist_type == 'L2':
      dist = np.sqrt((lat_rx - lat_cbsd)**2 + (lon_rx - lon_cbsd)**2)
    else:
      dist, _, _ = vincenty.GeodesicDistanceBearing(lat_cbsd, lon_cbsd, lat_rx, lon_rx)

    path_loss = self.factor * dist + self.offset
    bearing_cbsd = np.arctan2(lon_rx - lon_cbsd, lat_rx - lat_cbsd) * 180. / np.pi
    bearing_rx = 180 + bearing_cbsd
    if bearing_cbsd < 0: bearing_cbsd +=360
    return wf_itm._PropagResult(
        db_loss=(path_loss if np.isscalar(reliability) else
                 np.ones(len(reliability)) * path_loss),
        incidence_angles=wf_itm._IncidenceAngles(
            hor_cbsd=bearing_cbsd, ver_cbsd=0, hor_rx=bearing_rx, ver_rx=0),
        internals={})

class FakeInterferenceCalculator(object):
  """Fake model to calculate the interference for testing.

  It can be used as a fake replacement for computeInterference() module.
  This fake model internally calls the fake models for Antenna Gain
  and Propagation Loss calculations.

  interf.computeInterference() = FakeInterferenceCalculator()

  Attributes:
    ant_gain: Effective antenna gain from CBSD towards the protected entity
              and vice versa. Default value is configured for interference
              calculation
    antenna_height: Antenna height considered for incidence angle calculation
    reference_bw: Aggregate interference is calculated in reference bandwidth
  """

  def __init__(self,
               ant_gain=10,
               antenna_height=1.5,
               reference_bw=5.e6):
    self.antenna_height = antenna_height
    self.ant_gain = ant_gain
    self.reference_bw = reference_bw

  def __call__(self, grant, eirp, constraint, fss_info=None,
                   esc_antenna_info=None, region_type=None):

    # Calculate the db loss and incidence angles using the FakePropagationPredictor
    db_loss, incidence_angles, _ = FakePropagationPredictor().__call__(grant.latitude,
        grant.longitude, grant.height_agl, constraint.latitude, constraint.longitude,
        self.antenna_height, grant.indoor_deployment, reliability=-1)

    # Calculate the interference based on the protection entity type and calculate
    # eirp and interference
    if (constraint.entity_type is interf.ProtectedEntityType.GWPZ_AREA or
      constraint.entity_type is interf.ProtectedEntityType.PPA_AREA):
      eirp = interf.getEffectiveSystemEirp(grant.max_eirp, grant.antenna_gain,
         self.ant_gain, self.reference_bw)
      interference = eirp - db_loss
      return interference
    else:
      if constraint.entity_type is interf.ProtectedEntityType.FSS_BLOCKING:
        eirp = interf.getEffectiveSystemEirp(grant.max_eirp, grant.antenna_gain,
               self.ant_gain, (grant.high_frequency - grant.low_frequency))
        # default 0.5 fss mask loss considered for FSS blocking
        interference = eirp - db_loss - 0.5
      else:
        # interference calculation for FSS Co-channel and ESC
        eirp = interf.getEffectiveSystemEirp(grant.max_eirp, grant.antenna_gain,
            self.ant_gain, self.reference_bw)
        interference = eirp - db_loss - interf.IN_BAND_INSERTION_LOSS
      return interference
