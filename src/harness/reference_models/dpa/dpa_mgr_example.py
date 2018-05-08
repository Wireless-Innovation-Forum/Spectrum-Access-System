#    Copyright 2018 SAS Project Authors. All Rights Reserved.
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

"""An example of the DPA move list and interference check."""
import json
import os
import time
from collections import namedtuple

from reference_models.common import data
from reference_models.common import mpool
from reference_models.dpa import dpa_mgr

# Define protection point, i.e., a tuple with named fields of
# 'latitude', 'longitude'
ProtectionPoint = namedtuple('ProtectionPoint', ['latitude', 'longitude'])


if __name__ == '__main__':
  # Number of Monte Carlo iterations
  num_iter = 2000

  # Margin check
  margin_db = 0.01  # Possible only because cache manager is used

  # Configure the global pool manager
  num_processes = 4
  mpool.Configure(num_processes) # Note: shall not be run in child process
                                 # so protect it.

  # Populate protection points
  protection_points = [ProtectionPoint(latitude=36.9400, longitude=-75.9989),
                       ProtectionPoint(latitude=37.7579, longitude=-75.4105),
                       ProtectionPoint(latitude=36.1044, longitude=-73.3147),
                       ProtectionPoint(latitude=36.1211, longitude=-75.5939)]

  channel = (3600, 3610)

  # Configure operating parameters
  dpa_mgr.Dpa.Configure(num_iteration=num_iter)
  dpa_ref = dpa_mgr.Dpa(protection_points,
                        threshold=-144,
                        beamwidth=3,
                        radar_height=50,
                        catb_neighbor_dist=190, # so as to exercise the HAAT
                        freq_ranges_mhz=[channel])

  # Read all grants
  current_dir = os.getcwd()
  _BASE_DATA_DIR = os.path.join(current_dir, 'test_data')

  # Populate a list of CBSD registration requests
  reg_request_filename = ['RegistrationRequest_1.json',
                          'RegistrationRequest_2.json',
                          'RegistrationRequest_3.json',
                          'RegistrationRequest_4.json',
                          'RegistrationRequest_5.json',
                          'RegistrationRequest_6.json']
  reg_request_list = []
  for reg_file in reg_request_filename:
    reg_request = json.load(open(os.path.join(_BASE_DATA_DIR, reg_file)))
    reg_request_list.append(reg_request)

  # Populate a list of grant requests
  grant_request_filename = ['GrantRequest_1.json',
                            'GrantRequest_2.json',
                            'GrantRequest_3.json',
                            'GrantRequest_4.json',
                            'GrantRequest_5.json',
                            'GrantRequest_6.json']
  grant_request_list = []
  for grant_file in grant_request_filename:
    grant_request = json.load(open(os.path.join(_BASE_DATA_DIR, grant_file)))
    grant_request_list.append(grant_request)

  grants_uut = data.getGrantsFromRequests(reg_request_list[:4], grant_request_list[:4])
  grants_th = data.getGrantsFromRequests(reg_request_list[4:], grant_request_list[4:],
                                         is_managing_sas=False)
  # Set the grants
  dpa_ref.SetGrantsFromList(grants_uut + grants_th)

  # Determine which CBSD grants are on the move list
  start_time = time.time()
  dpa_ref.ComputeMoveLists()
  end_time = time.time()
  print '-- Reference model --'
  print 'Move list output: ' + str(dpa_ref.GetMoveListMask(channel))
  print 'Computation time: ' + str(end_time - start_time)

  # Compute the resulting interference
  interf = dpa_ref.CalcKeepListInterference(channel)
  print 'Keep List Interf: %s' % (' '.join([('%.3f' % i) for i in interf]))

  # Simulate the SAS UUT
  # same algo but with a slightly different set of points
  print '-- UUT model --'
  protection_points = [ProtectionPoint(latitude=36.945, longitude=-76.),
                       ProtectionPoint(latitude=37.76, longitude=-75.405),
                       ProtectionPoint(latitude=36.102, longitude=-73.312),
                       ProtectionPoint(latitude=36.12, longitude=-75.58)]
  dpa_uut = dpa_mgr.Dpa(protection_points,
                        threshold=-144,
                        beamwidth=3,
                        radar_height=50,
                        freq_ranges_mhz=[channel])
  dpa_uut.SetGrantsFromList(grants_uut + grants_th)
  dpa_uut.ComputeMoveLists()
  keep_list = dpa_uut.GetKeepList(channel)
  active_uut_grants = [grant for grant in grants_uut
                       if grant in keep_list]
  check = dpa_ref.CheckInterference(active_uut_grants,
                                    margin_db=margin_db)
  print 'Move list output: ' + str(dpa_uut.GetMoveListMask(channel))
  print 'Check Interference @%.2fdB margin: %s' % (margin_db, 'OK' if check else 'FAIL')

  # Simulate a single SAS UUT (no peer SAS)
  print '-- Single UUT model --'
  dpa_uut.SetGrantsFromList(grants_uut)
  dpa_uut.ComputeMoveLists()
  keep_list = dpa_uut.GetKeepList(channel)
  active_uut_grants = [grant for grant in grants_uut
                       if grant in keep_list]
  check = dpa_uut.CheckInterference(active_uut_grants,
                                    margin_db=margin_db,
                                    do_abs_check_single_uut=True)
  print 'Move list output: ' + str(dpa_uut.GetMoveListMask(channel))
  print 'Check Interference @%.2fdB margin: %s' % (margin_db, 'OK' if check else 'FAIL')
