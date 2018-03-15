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

from reference_models.geo import vincenty
from reference_models.propagation import wf_itm

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
