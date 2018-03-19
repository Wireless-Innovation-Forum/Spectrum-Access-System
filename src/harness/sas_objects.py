#  Copyright 2018 SAS Project Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import logging
import sys
import unittest

class Grant():
  """Holds the Grant request parameters"""

  def __init__(self, grant_id, grant_request):
    """Constructor to store the grant parameters

    Args:
       grant_id: grant id of the request
       grant_request: A dictionary containing the grant request parameters
    """
    # Store the grant parameters
    self.grant_id = grant_id
    self.grant_request = grant_request
    self.authorized_in_last_heartbeat = False
    self.is_terminated = False

  def getGrantId(self):
    return self.grant_id

  def getGrantRequest(self):
    return self.grant_request

  def getRequestOperationParam(self):
    return self.grant_request['operationParam']

  def constructHeartbeatRequest(self):
    """This function constructs heartbeat request for the grant object"""
    heartbeat_request = {
        'grantId': self.grant_id,
        'cbsdId': self.grant_request['cbsdId'],
        'operationState': 'GRANTED'
      }
    return heartbeat_request

  def isGrantAuthorizedInLastHeartbeat(self):
    return self.authorized_in_last_heartbeat

  def isActive(self):
    return not self.is_terminated


class Cbsd():
  """Holds the CBSD related parameters"""
  def __init__(self, cbsd_id, registration_request, grant_ids, grant_requests):
    """Constructor to store the registration request parameters

    Args:
      cbsd_id: cbsd id of the device extracted from the registration response
      registration_request:A registrationRequest object as defined in the SAS-CBSD TS.
      grant_ids: list of grant ids
      grant_requests:A list of dictionary containing the grant request parameters
    """
    assert (len(grant_requests) == len(grant_ids))
    self.cbsd_id = cbsd_id
    self.grant_objects = {}
    for grant_id, grant_request in zip(grant_ids, grant_requests):
      self.grant_objects[grant_id] = Grant(grant_id, grant_request)
    self.registration_request = registration_request

  def getCbsdId(self):
    return self.cbsd_id

  def getGrantObject(self, grant_id):
    return self.grant_objects[grant_id]

  def getRegistrationRequest(self):
    return self.registration_request

  def hasActiveGrant (self):
    for grant_object in self.grant_objects.itervalues():
      if grant_object.isActive():
        return True
    return False

  def constructHeartbeatRequestForAllActiveGrants(self):
    """Construct list of heartbeat requests of all active grants"""
    heartbeat_requests = []
    for grant_object in self.grant_objects.itervalues():
      if(grant_object.isActive()):
        heartbeat_request = grant_object.constructHeartbeatRequest()
        heartbeat_requests.append(heartbeat_request)
    return heartbeat_requests

  def getOperationParamsOfAllAuthorizedGrants(self):
    """Returns the list of operation params of all authorized grants"""
    operation_params = []
    for grant_object in self.grant_objects.values():
      if(grant_object.isGrantAuthorizedInLastHeartbeat()):
        operation_param = grant_object.getRequestOperationParam()
        operation_params.append(operation_param)
    return operation_params


class DomainProxy():
  """Holds the domain proxy related parameters"""

  def __init__(self, ssl_cert, ssl_key, testcase):
    """
    Args:
      ssl_cert: Path to SSL cert file
      ssl_key: Path to SSL key file
      testcase: test case object from the caller
    """
    self.ssl_cert = ssl_cert
    self.ssl_key = ssl_key
    self.cbsd_objects = {}
    self.testcase = testcase
    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
      logging.Formatter(
        '[%(levelname)s] %(asctime)s %(filename)s:%(lineno)d %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

  def initialize(self, registration_requests, grant_requests):
    """
    Args
      registration_requests: A list of dictionary elements ,where each list elements is
        individual CBSD registration requests (each of which is itself a dictionary).
      grant_requests: A list of dictionary elements,where each list elements is
        individual CBSD grant requests (each of which is itself a dictionary).
    """
    # Checking if the number of registration requests matches number of grant requests
    # There should be exactly one grant request per registration request.
    assert (len(grant_requests) == len(registration_requests))
    cbsd_ids = self.testcase.assertRegistered(registration_requests)

    # Make one CBSD object per successful grant request
    grant_requests_wrap = {
      'grantRequest': grant_requests
    }
    grant_responses = self.testcase._sas.Grant(grant_requests_wrap, self.ssl_cert, self.ssl_key)[
                                               'grantResponse']
    for index, grant_request in enumerate(grant_requests):
      grant_request["cbsdId"] = cbsd_ids[index]
      if grant_responses[index]['response']['responseCode'] == 0:
        cbsd_object = Cbsd(cbsd_ids[index], registration_requests[index],
                           [grant_responses[index]['grantId']], [grant_request])
        self.cbsd_objects[cbsd_ids[index]] = cbsd_object

  def getCbsdObjectById(self, cbsd_id):
    return self.cbsd_objects[cbsd_id]

  def heartbeatRequestForAllGrants(self, heartbeat_requests = None):
    """This function performs heartbeat request for all grants of CBSD devices at once

    Argument:
    heartbeat_requests : heart beat requests ,which  are constructed
    """
    # Concatenate all the heartbeat request of CBSD into single request
    heartbeat_requests = []
    for cbsd_object_item in self.cbsd_objects.values():
      heartbeat_requests = cbsd_object_item.constructHeartbeatRequestForAllActiveGrants()
    heartbeat_requests_wrapped = {
      'heartbeatRequest': heartbeat_requests
    }
    # Perform heartbeat requests
    heartbeat_responses = self.testcase._sas.Heartbeat(
      heartbeat_requests_wrapped, self.ssl_cert, self.ssl_key)['heartbeatResponse']

    for heartbeat_response in heartbeat_responses:
      try:
        cbsd_object = self.cbsd_objects[heartbeat_response['cbsdId']]
        grant_object = cbsd_object.grant_objects[heartbeat_response['grantId']]
      except KeyError:
        logging.debug("key not found")
      if heartbeat_response['response']['responseCode'] == 0:
        grant_object.authorized_in_last_heartbeat = True
      else:
        self.mapResponseCodeToGrantState(heartbeat_response['response']['responseCode'],
                                         grant_object)
    return heartbeat_responses

  def mapResponseCodeToGrantState(self, heartbeat_response_code, grant_object):
    """This function maps the heartbeat response and update the grant state"""
    if (heartbeat_response_code == 502):
      grant_object.is_terminated = True
    elif (heartbeat_response_code == 500):
      grant_object.is_terminated = True
      grant_object.authorized_in_last_heartbeat = False
    elif (heartbeat_response_code == 501):
      grant_object.authorized_in_last_heartbeat = False

  def performHeartbeatAndUpdateGrants(self):
    """ Does heartbeat request for all active grants and updates the grants

    The following steps are performed by this function
      1. Send heartbeat request on all grant of CBSD at once
      2. If the heartbeat response contains operationParam then those grants
         are relinquished.
      3. New grant requests with the suggested operationParam values in the
         heartbeat response is sent. Failures are ignored.
      4. Heartbeat is performed again for all grants. Failures are ignored.
    """
    # Heartbeat on all active grants
    heartbeat_requests = []
    heartbeat_responses = self.heartbeatRequestForAllGrants(heartbeat_requests)
    relinquish_requests = []
    grant_requests = []

    # Construct relinquishment request  for the heart beat response which have operation param
    for heartbeat_response, heartbeat_request in zip(heartbeat_responses,heartbeat_requests):
        if heartbeat_response['response']['responseCode'] != 0:
          # If any heartbeats contain suggested operating params,
          # relinquish the corresponding grant
          if 'operationParam' in heartbeat_response:
            relinquish_request = {
                'cbsdId': heartbeat_response['cbsdId'],
                'grantId': heartbeat_response['grantId']
            }
            relinquish_requests.append(relinquish_request)

            # Construct grant request for relinquished grants
            grant_request = {
              'cbsdId': heartbeat_request['cbsdId'],
              'operationParam': {
                'maxEirp': heartbeat_request['operationParam']['maxEirp'],
                'operationFrequencyRange': {
                  'lowFrequency': heartbeat_request['operationParam']['operationFrequencyRange']['lowFrequency'],
                  'highFrequency': heartbeat_request['operationParam']['operationFrequencyRange']['highFrequency']
                }
              }
            }
            grant_requests.append(grant_request)

          del self.cbsd_objects[heartbeat_response['cbsdId']]
    relinquish_requests_wrap = {
      'relinquishmentRequest': relinquish_requests
    }

    # Perform relinquishment if operation param present in heartbeat response
    self.testcase._sas.Relinquishment(relinquish_requests_wrap,
                                      self.ssl_cert, self.ssl_key)

    grant_requests_wrap = {
      'grantRequest': grant_requests
    }

    # Perform Grant for relinquished grants
    grant_responses = self.testcase._sas.Grant(grant_requests_wrap, self.ssl_cert, self.ssl_key)[
                                        'grantResponse']
    try:
      for grant_response,grant_request in zip(grant_responses,grant_requests):
        cbsd_object = self.cbsd_objects[grant_request['cbsdId']]
        cbsd_object.grant_objects[grant_request['grantId']] = Grant(grant_request['grantId'], grant_request)
    except KeyError:
      logging.debug("key not found")

    # Perform Heartbeat request for all grants
    self.heartbeatRequestForAllGrants()

  def getCbsdsWithAtLeastOneAuthorizedGrant(self):
    """This function returns a list of CBSD with authorized grants

    returns: list of CBSD objects
    """
    cbsd_objects = []
    for cbsd_object in self.cbsd_objects.values():
      if cbsd_object.hasActiveGrant():
        cbsd_objects.append(cbsd_object)
    return cbsd_objects
