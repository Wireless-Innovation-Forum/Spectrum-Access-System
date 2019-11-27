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

"""Compute and save the move list necessary to meet the DPA protection
   level,  with the option to use a hybrid propagation model and/or
   a clutter model."""

import os
import time
from collections import namedtuple
import numpy as np
import sys
import argparse

from reference_models.common import data
from reference_models.common import mpool
from reference_models.dpa import dpa_mgr

from dpa_utils import regGrantsFromJson

# Define protection point, i.e., a tuple with named fields of
# 'latitude', 'longitude'
ProtectionPoint = namedtuple('ProtectionPoint', ['latitude', 'longitude'])

# Define command-line arguments
parser = argparse.ArgumentParser(description='DPA Point Move Lists')
parser.add_argument('dpa_name', type=str,
                    help='name of DPA (e.g., \'East1\', \'Pensacola\')')
parser.add_argument('--dpa_name_suffix', type=str, default='',
                    help='suffix to append to DPA name')
parser.add_argument('--cata_dist', type=int,
                    help='category A neighborhod distance')
parser.add_argument('--catb_dist', type=int,
                    help='category B neighborhod distance')
parser.add_argument('--protection_points_method', type=str,
                    default='default(25,10,10,5)',
                    help='protection points method')
parser.add_argument('--portal_dpa_fname', type=str,
                    help='portal DPA file name (optional)')
parser.add_argument('--protection_level_margin', type=float, default=0.0,
                    help='margin to add to DPA protection level (dB)')
parser.add_argument('--hybrid_prop', type=bool, default=False,
                    help='use hybrid ITM/eHata propagation model')
parser.add_argument('--add_clutter', type=bool, default=False,
                    help='use the ITU-R P.2108 statistical terrestrial clutter model')


def setNeighborhoodDistance(dpa, dist_selection, neigh_dist):
  """Set the selected neighborhood distance of the DPA.

  Args:
    dpa: Dpa object
    dist_selection: index of neighborhood distance to set
    neigh_dist: the neighborhood distance (km)
  """
  neighbor_distances = list(dpa.neighbor_distances)
  neighbor_distances[dist_selection] = float(neigh_dist)
  dpa.neighbor_distances = tuple(neighbor_distances)


if __name__ == '__main__':

  # Obtain command line arguments
  args = parser.parse_args()
  
  # Number of Monte Carlo iterations
  num_iter = 2000

  # Read registration and grant requests
  current_dir = os.getcwd()
  config_fname = os.path.join(current_dir, 'test_data/' + args.dpa_name + args.dpa_name_suffix
                              + '_reg_grant.json')
  reg_request_list, grant_request_list = regGrantsFromJson(config_fname)
  grants = data.getGrantsFromRequests(reg_request_list, grant_request_list)
  print 'Number of grants:', len(grants)

  # Set DPA channel to be co-channel with grants
  grant_channel_lo = grants[0].low_frequency/1000000
  grant_channel_hi = grants[0].high_frequency/1000000  
  dpa_channel = (grant_channel_lo, grant_channel_hi)

  # Configure operating parameters
  dpa_mgr.Dpa.Configure(num_iteration=num_iter)
  dpa_ref = dpa_mgr.BuildDpa(args.dpa_name, protection_points_method=args.protection_points_method,
                             portal_dpa_filename=args.portal_dpa_fname)
  dpa_ref.ResetFreqRange([dpa_channel])

  # Set the grants
  dpa_ref.SetGrantsFromList(grants)

  # Configure the global pool manager
  print 'Number of protection points:', len(dpa_ref.protected_points)
  num_processes = min(50, len(dpa_ref.protected_points))
  mpool.Configure(num_processes) # Note: shall not be run in child process
                                 # so protect it.

  # Set the Cat A and inner and outer Cat B neighborhood distances, if
  # provided
  if args.cata_dist:
    setNeighborhoodDistance(dpa_ref, 0, args.cata_dist)
  if args.catb_dist:
    setNeighborhoodDistance(dpa_ref, 1, args.catb_dist)
    setNeighborhoodDistance(dpa_ref, 2, args.catb_dist)

  # Add the optional protection level margin
  dpa_ref.threshold = dpa_ref.threshold + args.protection_level_margin

  # Compute the move list
  start_time = time.time()
  dpa_ref.ComputeMoveLists(hybrid_prop=args.hybrid_prop,
                           add_clutter=args.add_clutter)
  end_time = time.time()
  dpa_channel = dpa_ref._channels[0]
  moveList = dpa_ref.GetMoveList(dpa_channel)
  print 'Move list size: {:d} ({:.1f} s)'.format(
    len(moveList), end_time - start_time)

  # Save the move list and metadata
  fname = 'data/'+dpa_ref.name+args.dpa_name_suffix+'_ml_'
  fname += 'hyb' if args.hybrid_prop else 'itm'
  fname += 'c' if args.add_clutter else ''
  fname += '_m0p{:.0f}'.format(10*args.protection_level_margin)
  fname += '.npy'
  np.save(fname, (moveList, dpa_ref.protected_points, dpa_ref.neighbor_distances,
                  dpa_ref.threshold))
