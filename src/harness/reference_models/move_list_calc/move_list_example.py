# This software was developed by employees of the National Institute
# of Standards and Technology (NIST), an agency of the Federal
# Government. Pursuant to title 17 United States Code Section 105, works
# of NIST employees are not subject to copyright protection in the United
# States and are considered to be in the public domain. Permission to freely
# use, copy, modify, and distribute this software and its documentation
# without fee is hereby granted, provided that this notice and disclaimer
# of warranty appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND,
# EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION
# WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE
# ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING,
# BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES,
# ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS
# SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR
# OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY
# OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT
# OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
#
# Distributions of NIST software should also include copyright and licensing
# statements of any third-party software that are legally bundled with
# the code in compliance with the conditions of those licenses.

#================================================================================
# Test move_list calculation for a co-channel offshore DPA.
# Expected result is 'Move list output: [True, True, True, False, True, False]'.
#================================================================================


import json
import os
import time
from pykml import parser
from collections import namedtuple

# from shapely.geometry import Polygon as SPolygon
from reference_models.geo import zones
from reference_models.common import data
from reference_models.common import mpool
from reference_models.move_list_calc import move_list
from reference_models.move_list_calc import dpa_mgr

# Define protection point, i.e., a tuple with named fields of
# 'latitude', 'longitude'
ProtectionPoint = namedtuple('ProtectionPoint', ['latitude', 'longitude'])

# Define DPA protection specifications, i.e., a tuple with named fields of
# 'lowFreq' (in Hz), 'highFreq' (in Hz), 'antHeight' (in meter),
# 'beamwidth' (in degree), 'threshold' (in dBm/10MHz)
ProtectionSpecs = namedtuple('ProtectionSpecs', ['lowFreq', 'highFreq',
    'antHeight', 'beamwidth', 'threshold'])

if __name__ == '__main__':
  # Number of Monte Carlo iterations
  num_iter = 2000

  # Congigure the global pool manager
  num_processes = 4
  mpool.Configure(num_processes) # Note: shall not be run in child process
                                 # so protect it.

  # Populate protection points
  protection_points = [ProtectionPoint(latitude=36.9400, longitude=-75.9989),
                       ProtectionPoint(latitude=37.7579, longitude=-75.4105),
                       ProtectionPoint(latitude=36.1044, longitude=-73.3147),
                       ProtectionPoint(latitude=36.1211, longitude=-75.5939)]

  # Configure operating parameters
  dpa_mgr.Dpa.Configure(num_iteration=num_iter)

  dpa = dpa_mgr.Dpa(protection_points,
                    threshold=-144,
                    beamwidth=3,
                    radar_height=50,
                    freq_ranges_mhz=[(3600, 3610)])

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

  grants = data.getGrantsFromRequests(reg_request_list, grant_request_list)

  # Set the grants
  dpa.SetGrantsFromList(grants)

  # Determine which CBSD grants are on the move list
  start_time = time.time()
  res = dpa.CalcMoveLists()
  end_time = time.time()
  print 'Move list output: ' + str(dpa.GetMoveListMask((3600, 3610)))
  print 'Computation time: ' + str(end_time - start_time)

