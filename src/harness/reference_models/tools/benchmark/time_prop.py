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

"""Benchmark the propagation model timing.
"""
import timeit
import numpy as np
import matplotlib.pyplot as plt

from reference_models.propagation import wf_itm
from reference_models.propagation import wf_hybrid
from reference_models.geo import drive
from reference_models.geo import vincenty

# Tx location
cbsd_lat = 40.5
cbsd_lon = -90.5

# Rx location
max_distance = 300
distances = np.array([2, 5] + range(10, 100, 10) + range(100, max_distance+20, 40))
bearing = 90
freq_mhz = 3625
rx_lats, rx_lngs, _ = vincenty.GeodesicPoints(cbsd_lat,cbsd_lon,
                                              distances, bearing)

t_itm_avg = []
t_hybrid_avg = []

def PlotProp():
  plt.figure()
  plt.plot(distances, t_itm_avg, 'b', label='ITM mean')
  plt.plot(distances, t_hybrid_avg, 'r', label='Hybrid mean')
  plt.legend()
  plt.xlabel('Distance (km)')
  plt.ylabel('Calculation time (ms)')
  plt.title('One pathloss calculation time')
  plt.grid('on')

def CalcHybrid(rel, rx_lat, rx_lng):
  res = wf_hybrid.CalcHybridPropagationLoss(
      cbsd_lat, cbsd_lon, 10,
      rx_lat, rx_lng, 1.5,
      False, rel, freq_mhz, 'SUBURBAN')
  return res

def CalcItm(rel, rx_lat, rx_lng):
  res = wf_itm.CalcItmPropagationLoss(
      cbsd_lat, cbsd_lon, 10,
      rx_lat, rx_lng, 1.5,
      False, rel, freq_mhz)
  return res

# Now do the time estimation
repeat = 3
num = 1000

if __name__ == '__main__':


  # First calc to load the terrain data in cache
  print '# Pre-Loading the terrain'
  res_last = CalcHybrid(0.5, rx_lats[-1], rx_lngs[-1])
  res_first = CalcHybrid(0.5, rx_lats[-1], rx_lngs[-1])
  print '## Initial driver report'
  drive.terrain_driver.stats.Report()

  print ''
  print '# Propagation calculation time at various distances'
  for k, dist in enumerate(distances):
    # ITM
    times = timeit.repeat(setup = 'import time_prop',
                          stmt='time_prop.CalcItm(-1,{0},{1})'.format(
                              rx_lats[k], rx_lngs[k]),
                          repeat=repeat, number=num)
    t_itm_avg.append(min(times))

    # Hybrid
    times = timeit.repeat(setup = 'import time_prop',
                          stmt='time_prop.CalcHybrid(-1,{0},{1})'.format(
                              rx_lats[k], rx_lngs[k]),
                          repeat=repeat, number=num)
    t_hybrid_avg.append(min(times))
    print '{0}km: {1:5f}ms (itm)  {2:5f}ms (hybrid)'.format(
        int(dist),
        t_itm_avg[-1] / num * 1000,
        t_hybrid_avg[-1] / num * 1000)

  print '# Final driver report'
  wf_itm.terrainDriver.stats.Report()

  PlotProp()
  plt.show()
