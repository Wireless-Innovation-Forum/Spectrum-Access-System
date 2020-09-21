#    Copyright 2020 SAS Project Authors. All Rights Reserved.
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
r"""ESC Impact Simulator.

For evaluation of the impact of ESC protection into CBSD transmit power.
It uses the IAP reference implementation to assess how much power reduction is
required on each CBSD in the network.


Inputs:
 - A JSON file defining the CBSD deployment model. For example one can use any
 NTIA model that was generated for DPA neighborhood studies, found in:
   https://github.com/Wireless-Innovation-Forum/Spectrum-Access-System/tree/master/data/research/deployment_models
 - Some JSON FADs file defining the ESC networks.

Output:
 - A figure showing the impact of ESC protection on CBSDs power.
 - A CSV file showing every CBSD with requested/obtained power.

Example Usage:
  # Run the simulation for a list of grants, on all sensors of 2 ESC FADS.
  python run_esc_impact.py data/West14_reg_grant.json.zip \
       --esc_fads esc1_fad.json,esc2_fad.json

  # Run the simulation for a list of grants, on selected sensors of 2 ESC FADS:
  #  + only the sensors whose name contains `W12` and `W13` string.
  #  + also output one CSV per sensor containing all impacted CBSD.
  python run_esc_impact.py data/West14_reg_grant.json.zip \
       --esc_fads esc1_fad.json,esc2_fad.json  \
       --sensors W12,W13 \
       --output_csv
"""
import argparse
import json
import glob

import cartopy.crs as ccrs
import csv
import matplotlib.pyplot as plt
import numpy as np
import shapely.geometry as sgeo

import iap_patch
from reference_models.iap import iap
from reference_models.geo import vincenty
from reference_models.tools import sim_utils

#----------------------------------------
# Setup the command line arguments
parser = argparse.ArgumentParser(description='ESC Impact Simulator')

# - Generic config.
parser.add_argument('cbsd_file', type=str, default='',
                    help='CBSD deployment file (JSON).')
parser.add_argument('--esc_fads', type=str, default='',
                    help='The ESC FADs file (JSON) separated by a comma.')
parser.add_argument('--per_sensor', action='store_true',
                    help='If set, no ESC aggregation.')
parser.add_argument('--output_csv', action='store_true',
                    help='If set, output CSV per sensor of all impacted CBSD.')
parser.add_argument('--sensors', type=str, default='',
                    help='Sensors to analyse (prefix).')

options = parser.parse_args()


#--------------------------------------------------
# The simulation
def esc_impact_sim(cbsd_reg_grant, esc_fads,
                   sensor_filters=None,
                   per_sensor_mode=False,
                   do_csv_output=False):
  """ESC impact simulation.

  Performs simulation on given input (CBSD and ESC), creates resulting plots
  and output CSV file.

  Args:
    cbsd_reg_grant: The CBSD file (JSON) in 'reg_grant' format.
    esc_fads: A list of ESC FAD data (JSON).
    sensor_filters: List of string for filtering sensor (ex: W13, google, ..).
    per_sensor_mode: If set, computes impact stats per sensor. No plots or CSV
      output is done.
    do_csv_output: If set, output
  """
  # Read the grants from 'reg_grant' file
  grants, _ = sim_utils.ReadTestHarnessConfigFile(cbsd_reg_grant)

  # Reads the ESC sensors from all FADs.
  sensors = []
  for fad in esc_fads:
    sensors.extend(json.load(open(fad))['recordData'])

  # Filter the ESCs to simulate.
  if sensor_filters:
    filt_sensors = []
    for sensor in sensors:
      for token in sensor_filters:
        if token in sensor['id']:
          filt_sensors.append(sensor)
          break
    sensors = filt_sensors

  if not sensors:
    print('Simulation cancelled - No sensor name containing one of %s'
          % sensor_filters)
    return

  print('ESCs included in the simulation:')
  print([sensor['id'] for sensor in sensors])

  # Run IAP simulation.
  if not per_sensor_mode:
    for sensor in sensors:
      esc_allowed_interference = iap.performIapForEsc(sensor, grants, [])
    impacted_grants = [grant for grant in grants
                       if max(grant.iap_eirp) - min(grant.iap_eirp) > 0]
    print('Number of impacted CBSDs: %d' % len(impacted_grants))
  else:
    # Special mode for getting # impacted grants per sensor independently.
    for sensor in sensors:
      # Clear iap_eirp before simulation of each ESC
      for grant in grants:
        grant.iap_eirp.clear()
        grant.iap_eirp.add(grant.max_eirp)
      esc_allowed_interference = iap.performIapForEsc(sensor, grants, [])
      impacted_grants = [grant for grant in grants
                         if max(grant.iap_eirp) - min(grant.iap_eirp) > 0]
      print('Number of CBSDs impacted by %s: %d'
            % (sensor['id'], len(impacted_grants)))
      return

  # Output the CSV.
  if do_csv_output:
    for sensor in sensors:
      sensor_loc = (sensor['installationParam']['latitude'],
                    sensor['installationParam']['longitude'])
      neighbor_grants = []
      sensor_name = sensor['id'].split('/')
      for idx, grant in enumerate(grants):
        dist_km, _, _ = vincenty.GeodesicDistanceBearing(
            grant.latitude, grant.longitude, sensor_loc[0], sensor_loc[1])
        if ((grant.cbsd_category == 'A' and dist_km <= 40) or
            (grant.cbsd_category == 'B' and dist_km <= 80)):
          neighbor_grants.append(
              [sensor_name[1], sensor_name[2], idx,
               grant.cbsd_category, grant.indoor_deployment, grant.height_agl,
               dist_km, grant.antenna_gain,
               grant.max_eirp + 10,
               min(grant.iap_eirp) + 10])

      file_name = sensor_name[2] + '_neighbors.csv'
      with open(file_name, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(
            ['ESC Network', 'ESC Sensor','CBSD ID','CBSD Category','Indoor CBSD',
             'CBSD AGL','Distance to ESC (km)','CBSD Antenna Gain (dBi)',
             'Max EIRP (dBm/10MHz)','Actual EIRP (dBm/10MHz)'])
        writer.writerows(neighbor_grants)

  # Retrieve the delta EIRP for plots and stats.
  delta_eirp = []
  for grant in grants:
    delta_eirp.append(max(grant.iap_eirp) - min(grant.iap_eirp))

  # Create figure with simple projection.
  fig = plt.figure(figsize=(10,10))
  subplot = 111
  ax = fig.add_subplot(subplot, projection=ccrs.PlateCarree())

  # Finds the bounding box of all geometries (DPA and CBSDs).
  box_margin = 0.1 # about 10km
  box = sgeo.box(*sgeo.MultiPoint(
    [(grant.longitude, grant.latitude) for grant in grants]).bounds)
  box = box.buffer(box_margin)

  # Plot geometries.
  ax.axis([box.bounds[0], box.bounds[2], box.bounds[1], box.bounds[3]])
  ax.coastlines()
  ax.stock_img()

  # class1: no power reduction
  class1_grants = [grant for grant in grants
                   if max(grant.iap_eirp) == min(grant.iap_eirp)]
  class1_locations = ([grant.longitude for grant in class1_grants],
                      [grant.latitude for grant in class1_grants])
  ax.scatter(*class1_locations, c='g', marker='1', s=50,
             label='0 dB power reduction: %d' % len(class1_grants) )

  # class2: less than 10 dB power reduction
  class2_grants = [grant for grant in grants
                   if (max(grant.iap_eirp) > min(grant.iap_eirp)
                       and max(grant.iap_eirp)-min(grant.iap_eirp) < 10)]
  class2_locations = ([grant.longitude for grant in class2_grants],
                      [grant.latitude for grant in class2_grants])
  ax.scatter(*class2_locations, c='b', marker='1', s=50,
             label='<10 dB power reduction: %d' % len(class2_grants) )

  # class3: 10 dB or more power reduction
  class3_grants = [grant for grant in grants
                   if max(grant.iap_eirp) - min(grant.iap_eirp) >= 10]
  class3_locations = ([grant.longitude for grant in class3_grants],
                      [grant.latitude for grant in class3_grants])
  ax.scatter(*class3_locations, c='r', marker='1', s=50,
             label='>=10 dB power reduction: %d' % len(class3_grants) )

  ax.legend(loc=0)
  ax.set_title('ESC Protection')

  # Print histogram of power reduction
  power_reduction = [max(grant.iap_eirp) - min(grant.iap_eirp)
                     for grant in grants]
  plt.figure()
  plt.hist(power_reduction, bins=np.arange(0.1, 50, 1))
  plt.xlabel('CBSD power reduction')
  plt.ylabel('# of CBSDs')
  plt.grid()


#----------------------------------------------------------------
# Script main runner
if __name__ == '__main__':
  esc_fads = options.esc_fads.split(',')
  sensor_filters = options.sensors.split(',')
  esc_impact_sim(options.cbsd_file, esc_fads, sensor_filters,
                 options.per_sensor, options.output_csv)
  plt.show(block=True)
