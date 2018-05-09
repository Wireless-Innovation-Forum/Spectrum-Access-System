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

"""Example of FSS in-band protection code.

This is just an example demonstrating how to call the propagation and antenna
reference models.
"""
from collections import namedtuple
import numpy as np
import sys

from reference_models.antenna import antenna
from reference_models.geo import vincenty
from reference_models.propagation import wf_itm
from reference_models.tools import entities

import fss_pointing

# Configure here the path to terrain directory
# (if not specified in your CONFIG.py file)
## from reference_models.geo import drive
## drive.ConfigureTerrainDriver(terrain_dir='/home/winnforum/SAS-data/ned/')

# Find all the FSS protection points from a given FSS license info.
# Note that in production, one may have the exact pointing of each FSS.
def GetAllFssFromLicenseInfo(fss_license_info):
  """Get all Fss protection points from a FSS license record.

  Inputs:
    fss_license_info:  A |FssLicenseInfo| holding the license record.

  Returns:
    a list of |FssProtectionPoint| with same location and different pointings.
  """
  info = fss_license_info
  pointings = fss_pointing.GsoPossiblePointings(
      info.latitude, info.longitude,
      info.satellite_arc_west_limit, info.satellite_arc_east_limit,
      info.elevation_west_limit, info.elevation_east_limit,
      info.azimuth_west_limit, info.azimuth_east_limit)
  fss_entities = []
  for (azimuth, elevation) in pointings:
    fss = entities.FssProtection(latitude=info.latitude,
                                 longitude=info.longitude,
                                 height_agl=info.height_agl,
                                 max_gain_dbi=info.max_gain_dbi,
                                 pointing_azimuth=azimuth,
                                 pointing_elevation=elevation)
    fss_entities.append(fss)

  return fss_entities



#--------------------------------------------------------------
# Setup of the simulation: one FSS earth station and many CBSDs
np.random.seed(12345)  # For simulation repeatability

# Protect the following FSS near Kansas City defined here:
#    http://licensing.fcc.gov/myibfs/displayLicense.do?filingKey=-205179
fss_info = entities.FssLicenseInfo(latitude=38 + 48/60. + 3/3600.,
                                   longitude=-(94 + 15/60. + 28.8/3600.),
                                   height_agl=3.7,
                                   max_gain_dbi=40.9,
                                   satellite_arc_east_limit=-60,
                                   satellite_arc_west_limit=-143,
                                   elevation_east_limit=32.8,
                                   elevation_west_limit=22.9,
                                   azimuth_east_limit=132.6,
                                   azimuth_west_limit=241.2)


# Get all the FSS "protection points".
fss_entities = GetAllFssFromLicenseInfo(fss_info)
base_fss = fss_entities[0]  # All FSS entities share same location

# Distribute random CBSD of various types around the FSS.
cbsds_cat_a_indoor = entities.GenerateCbsdList(100,
                                               entities.CBSD_TEMPLATE_CAT_A_INDOOR,
                                               fss_info.latitude,
                                               fss_info.longitude,
                                               max_distance_km=200)
cbsds_cat_a_outdoor = entities.GenerateCbsdList(50,
                                                entities.CBSD_TEMPLATE_CAT_A_OUTDOOR,
                                                fss_info.latitude,
                                                fss_info.longitude,
                                                max_distance_km=200)
cbsds_cat_b = entities.GenerateCbsdList(20,
                                        entities.CBSD_TEMPLATE_CAT_B,
                                        fss_info.latitude,
                                        fss_info.longitude,
                                        max_distance_km=200)
all_cbsds = []
all_cbsds.extend(cbsds_cat_a_indoor)
all_cbsds.extend(cbsds_cat_a_outdoor)
all_cbsds.extend(cbsds_cat_b)

#---------------------------------------------------------------
# Calculate the aggregated interference calculation seen by the FSS
#  - first select all CBSD within 150km according to R2-SGN-16
cbsds = []
for cbsd in all_cbsds:
  distance_km, _, _ = vincenty.GeodesicDistanceBearing(
      base_fss.latitude, base_fss.longitude,
      cbsd.latitude, cbsd.longitude)
  if distance_km <= 150:
    cbsds.append(cbsd)

#  - then calculate all path losses and received RSSI at FSS
#    (without FSS antenna taken into account)
cbsd_rssi = np.zeros(len(cbsds))
cbsd_incidence_angles = []

for k, cbsd in enumerate(cbsds):
  if not (k%10):
    sys.stdout.write('*')
    sys.stdout.flush()
  db_loss, incidence_angles, _ = wf_itm.CalcItmPropagationLoss(
      cbsd.latitude, cbsd.longitude, cbsd.height_agl,
      base_fss.latitude, base_fss.longitude, base_fss.height_agl,
      cbsd.is_indoor, reliability=-1)

  cbsd_effective_eirp = antenna.GetStandardAntennaGains(
      incidence_angles.hor_cbsd,
      cbsd.antenna_azimuth, cbsd.antenna_beamwidth,
      cbsd.eirp_dbm_mhz)

  cbsd_rssi[k] = cbsd_effective_eirp - db_loss
  cbsd_incidence_angles.append(incidence_angles)

#  - then compute the aggregate average interference for each FSS entity
#    (ie each different possible FSS antenna pointing)
fss_total_rssi = []
for fss_entity in fss_entities:
  hor_dirs = [inc_angle.hor_rx for inc_angle in cbsd_incidence_angles]
  ver_dirs = [inc_angle.ver_rx for inc_angle in cbsd_incidence_angles]

  fss_ant_gains =  antenna.GetFssAntennaGains(
      hor_dirs, ver_dirs,
      fss_entity.pointing_azimuth,
      fss_entity.pointing_elevation,
      fss_entity.max_gain_dbi)
  # compute aggregated RSSI in linear space (and convert back to dBm)
  total_rssi = 10 * np.log10(np.sum( 10**((cbsd_rssi + fss_ant_gains) / 10.)))
  fss_total_rssi.append(total_rssi)

#---------------------------------------------------------------
# Print out results
print 'For FSS lat=%.7f lon=%.7f: %d CBSDs' % (
    base_fss.latitude, base_fss.longitude, len(cbsds))
print '   Max RSSI = %.2f dBm / MHz' % max(fss_total_rssi)
print '   RSSI per possible pointing:'
print [int(val*100)/100. for val in fss_total_rssi]
