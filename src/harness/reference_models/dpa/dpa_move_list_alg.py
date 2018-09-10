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

# This software was developed in part by employees of the National Institute
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

"""An example of the DPA move list and interference check."""
# Usage:
#   python dpa_move_list_alg.py <name of dpa (e.g., 'East1', 'Pensacola')>
#                               <dpa channel start frequency (MHz)>
#                               <dpa channel end frequency (MHz)>
#                               <cbsd channel start frequency (MHz)>
#                               <cbsd channel end frequency (MHz)>
#                               <cat A neighboorhood distance (km)>
#                               <cat B neighboorhood distance (km)>
#                               <cat A neighboorhood OOB distance (km)>
#                               <cat B neighboorhood OOB distance (km)>
#                               <move list algorithm selection (integer)>
#                               <path loss reliability for sort (0<r<1)>

import json
import os
import time
from collections import namedtuple
import numpy as np
from copy import deepcopy
import sys

from reference_models.common import data
from reference_models.common import mpool
from reference_models.dpa import dpa_mgr

# Define protection point, i.e., a tuple with named fields of
# 'latitude', 'longitude'
ProtectionPoint = namedtuple('ProtectionPoint', ['latitude', 'longitude'])


def csvToRegGrants(data_dir, dpa_name, cbsd_channel):
  """Return lists of registration and grant requests from deployment csv files.

  Args:
    data_dir: path to template registration and grant request json files and to csv files
    dpa_name: name of DPA
    cbsd_channel: channel start and end frequencies (MHz) of grants (binary tuple)
  """
  reg_request_list = []
  grant_request_list = []

  # Template registration and grant requests
  reg_request_filename = 'RegistrationRequest_Omni.json'
  reg_requestN = json.load(open(os.path.join(data_dir, reg_request_filename)))
  grant_request_filename = 'GrantRequest_N.json'
  grant_requestN = json.load(open(os.path.join(data_dir, grant_request_filename)))  
  
  # Populate Category A CBSD registration and grant requests
  csv_fname = os.path.join(data_dir, dpa_name + '_cata.csv')
  latA, lonA, htA, EIRPdBm10MHzA = np.loadtxt(csv_fname,delimiter=',',skiprows=1,usecols=(0,1,2,4),unpack=True)
  for i in range(latA.size):
    reg_request = deepcopy(reg_requestN)
    reg_request['fccId'] = '321cba_' + str(i+1)
    reg_request['cbsdCategory'] = 'A'
    reg_request['installationParam']['latitude'] = latA[i]
    reg_request['installationParam']['longitude'] = lonA[i]
    reg_request['installationParam']['height'] = htA[i]
    reg_request['installationParam']['indoorDeployment'] = True
    reg_request_list.append(reg_request)
    grant_request = deepcopy(grant_requestN)
    grant_request['cbsdId'] = 'sas1/cbsd' + str(i+1)
    grant_request['operationParam']['maxEirp'] = EIRPdBm10MHzA[i] - 10.0   # convert to dBm/MHz
    grant_request['operationParam']['operationFrequencyRange']['lowFrequency'] = cbsd_channel[0] * int(1e6)
    grant_request['operationParam']['operationFrequencyRange']['highFrequency'] = cbsd_channel[1] * int(1e6)
    grant_request_list.append(grant_request)

  # Populate Category B CBSD registration and grant requests
  csv_fname = os.path.join(data_dir, dpa_name + '_catb.csv')
  latB, lonB, htB, EIRPdBm10MHzB = np.loadtxt(csv_fname,delimiter=',',skiprows=1,usecols=(0,1,2,4),unpack=True)
  for i in range(latB.size):
    reg_request = deepcopy(reg_requestN)
    reg_request['fccId'] = '321cba_' + str(i+1+latA.size)
    reg_request['cbsdCategory'] = 'B'
    reg_request['installationParam']['latitude'] = latB[i]
    reg_request['installationParam']['longitude'] = lonB[i]
    reg_request['installationParam']['height'] = htB[i]
    reg_request['installationParam']['indoorDeployment'] = False
    reg_request_list.append(reg_request)
    grant_request = deepcopy(grant_requestN)
    grant_request['cbsdId'] = 'sas1/cbsd' + str(i+1+latA.size)
    grant_request['operationParam']['maxEirp'] = EIRPdBm10MHzB[i] - 10.0   # convert to dBm/MHz
    grant_request['operationParam']['operationFrequencyRange']['lowFrequency'] = cbsd_channel[0] * int(1e6)
    grant_request['operationParam']['operationFrequencyRange']['highFrequency'] = cbsd_channel[1] * int(1e6)
    grant_request_list.append(grant_request)

  print 'Size of registration/grant list:', len(grant_request_list)

  return reg_request_list, grant_request_list


if __name__ == '__main__':

  # Command line arguments
  dpa_name = sys.argv[1]
  dpa_ch_start = int(sys.argv[2])
  dpa_ch_end = int(sys.argv[3])
  cbsd_ch_start = int(sys.argv[4])
  cbsd_ch_end = int(sys.argv[5])
  cata_nd = int(sys.argv[6])
  catb_nd = int(sys.argv[7])
  cata_oob_nd = int(sys.argv[8])
  catb_oob_nd = int(sys.argv[9])
  move_list_alg = int(sys.argv[10])
  sort_reliability = float(sys.argv[11])
  
  # Number of Monte Carlo iterations
  num_iter = 2000

  # Margin check
  margin_db = 0.01  # Possible only because cache manager is used

##  # Populate protection points
##  protection_points_from_file = np.load('data/protection_points_'+dpa_name+'.npy')
##  protection_points = []
##  for p in protection_points_from_file:
##      protection_points.append(ProtectionPoint(latitude=p[0], longitude=p[1]))
##  print 'Number of protection points:', len(protection_points)

  dpa_channel = (dpa_ch_start, dpa_ch_end)
  cbsd_channel = (cbsd_ch_start, cbsd_ch_end)

  # Configure operating parameters
  dpa_mgr.Dpa.Configure(num_iteration=num_iter)
  dpa_ref = dpa_mgr.BuildDpa(dpa_name, protection_points_method='default (18, 0, 0, 0, 20)')
  dpa_ref.neighbor_distances = (cata_nd, catb_nd, cata_oob_nd, catb_oob_nd)
  dpa_ref.channels = [dpa_channel]
##  dpa_ref.protected_points = protection_points

  # Configure the global pool manager
  print 'Number of protection points:', len(dpa_ref.protected_points)
  num_processes = min(18, len(dpa_ref.protected_points))
  mpool.Configure(num_processes) # Note: shall not be run in child process
                                 # so protect it.

  # Read all grants
  current_dir = os.getcwd()
  _BASE_DATA_DIR = os.path.join(current_dir, 'test_data')

  # Populate a list of CBSD registration requests and grant requests
  reg_request_list, grant_request_list = csvToRegGrants(_BASE_DATA_DIR, dpa_name, cbsd_channel)

  # Set the grants
  grants_uut = data.getGrantsFromRequests(reg_request_list, grant_request_list)
  dpa_ref.SetGrantsFromList(grants_uut)

  # Determine which CBSD grants are on the move list
  start_time = time.time()
  dpa_ref.ComputeMoveLists(move_list_alg, sort_reliability)
  end_time = time.time()
  moveList = dpa_ref.GetMoveListMask(dpa_channel)
  print 'Move list size:', np.count_nonzero(moveList)
  print 'Computation time: ' + str(end_time - start_time)

  # Compute the resulting interference
  start_time = time.time()
  interf = dpa_ref.CalcGlobalKeepListInterference(dpa_channel, do_max=False)
  end_time = time.time()
  print 'Global Keep List Interf: %.3f' % np.amax(interf)
  print 'Computation time: ' + str(end_time - start_time)

  # Save move list mask and aggregate interference to file
  fname = 'data/'+dpa_name+'_alg.npy'
  try:
    (moveLists, aggInterfs, catANeighDists, catBNeighDists, catAOOBNeighDists, catBOOBNeighDists, dpa_channels, cbsd_channels, ml_alg, sort_rel) = np.load(fname)
    moveLists = np.column_stack((moveLists, moveList))
    aggInterfs = np.dstack((aggInterfs, np.column_stack(interf)))
    catANeighDists.append(cata_nd)
    catBNeighDists.append(catb_nd)
    catAOOBNeighDists.append(cata_oob_nd)
    catBOOBNeighDists.append(catb_oob_nd)
    dpa_channels.append(dpa_channel)
    cbsd_channels.append(cbsd_channel)
    ml_alg.append(move_list_alg)
    sort_rel.append(sort_reliability)
  except:
    moveLists = np.expand_dims(moveList, axis=1)
    aggInterfs = np.column_stack(interf)
    catANeighDists = [cata_nd]
    catBNeighDists = [catb_nd]
    catAOOBNeighDists = [cata_oob_nd]
    catBOOBNeighDists = [catb_oob_nd]
    dpa_channels = [dpa_channel]
    cbsd_channels = [cbsd_channel]
    ml_alg = [move_list_alg]
    sort_rel = [sort_reliability]
  np.save(fname, (moveLists, aggInterfs, catANeighDists, catBNeighDists, catAOOBNeighDists, catBOOBNeighDists, dpa_channels, cbsd_channels, ml_alg, sort_rel))
