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

"""Implementation of multiple objects (Grant, Cbsd and DomainProxy).
   Mainly used in MCP and related test cases."""
from enum import Enum
import logging

class Grant(object):
  """Holds the Grant request parameters."""

  # Define an enumeration class named ResponseCodes with members
  # 'SUCCESS',TERMINATED_GRANT', 'SUSPENDED_GRANT',UNSYNC_OP_PARAM
  class ResponseCodes(Enum):
    SUCCESS = 0
    TERMINATED_GRANT = 500
    SUSPENDED_GRANT = 501
    UNSYNC_OP_PARAM = 502

  def __init__(self, grant_id, grant_request):
    """Store grant parameters and initialize state variables.

    Args:
      grant_id: grant id of the request.
      grant_request: A dictionary containing the grant request parameters.
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
    """Constructs heartbeat request for the grant object."""
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


class Cbsd(object):
  """Holds the CBSD related parameters."""

  def __init__(self, cbsd_id, registration_request, grant_ids, grant_requests):
    """Constructor to store the registration request parameters.

    Args:
      cbsd_id: cbsd id of the device extracted from the registration response.
      registration_request:A registrationRequest object as defined in the SAS-CBSD TS.
      grant_ids: list of grant ids.
      grant_requests:A list of dictionary containing the grant request parameters.
    """
    assert len(grant_requests) == len(grant_ids)
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

  def hasActiveGrant(self):
    for grant_object in self.grant_objects.itervalues():
      if grant_object.isActive():
        return True
    return False

  def hasAuthorizedGrant(self):
    for grant_object in self.grant_objects.itervalues():
      if grant_object.isGrantAuthorizedInLastHeartbeat():
        return True
    return False

  def constructHeartbeatRequestForAllActiveGrants(self):
    """Construct list of heartbeat requests of all active grants."""
    heartbeat_requests = []
    for grant_object in self.grant_objects.itervalues():
      if grant_object.isActive():
        heartbeat_request = grant_object.constructHeartbeatRequest()
        heartbeat_requests.append(heartbeat_request)
    return heartbeat_requests

  def getOperationParamsOfAllAuthorizedGrants(self):
    """Returns the list of operation params of all authorized grants."""
    operation_params = []
    for grant_object in self.grant_objects.values():
      if grant_object.isGrantAuthorizedInLastHeartbeat():
        operation_param = grant_object.getRequestOperationParam()
        operation_params.append(operation_param)
    return operation_params


class DomainProxy(object):
  """Performs Domain Proxy related operations.

  This class stores Domain Proxy related information like the SSL certificate, key to be used and the set of
  CBSD objects belonging to this Domain Proxy. Bulk operations like registration, grant and heartbeat
  procedures are performed on all of the CBSDs belonging to this Domain Proxy.
  """
  def __init__(self, ssl_cert, ssl_key, testcase):
    """
    Args:
      ssl_cert: Path to SSL cert file.
      ssl_key: Path to SSL key file.
      testcase: test case object from the caller.
    """
    self.ssl_cert = ssl_cert
    self.ssl_key = ssl_key
    self.cbsd_objects = {}
    self.testcase = testcase

  def addCbsdsAndGrants(self, registration_requests, grant_requests):
    """Construct CBSD object based on the the result of registration and
    grant requests.

    Args
      registration_requests: A list of dictionary elements ,where each list elements is
        individual CBSD registration requests (each of which is itself a dictionary).
      grant_requests: A list of dictionary elements,where each list elements is
        individual CBSD grant requests (each of which is itself a dictionary).
    """
    # Checking if the number of registration requests matches number of grant requests
    # There should be exactly one grant request per registration request.
    assert len(grant_requests) == len(registration_requests)
    cbsd_ids = self.testcase.assertRegistered(registration_requests)

    # Wrapped version of the grant requests
    grant_requests_wrap = {
      'grantRequest': grant_requests
    }

    #perform grant operation
    grant_responses = self.testcase._sas.Grant(grant_requests_wrap,
                                               self.ssl_cert, self.ssl_key)['grantResponse']

    # Make one CBSD object per successful grant request
    for index, grant_request in enumerate(grant_requests):
      grant_request["cbsdId"] = cbsd_ids[index]
      if grant_responses[index]['response']['responseCode'] == 0:
        cbsd_object = Cbsd(cbsd_ids[index], registration_requests[index],
                           [grant_responses[index]['grantId']], [grant_request])
        self.cbsd_objects[cbsd_ids[index]] = cbsd_object

  def getCbsdObjectById(self, cbsd_id):
      return self.cbsd_objects[cbsd_id]

  def heartbeatRequestForAllActiveGrants(self):
    """Performs heartbeat request for all grants of CBSD devices at once.

    Returns:
      heartbeat_requests : list of heart beat requests which are constructed for all the grants
      by the caller
      heartbeat_responses: list of heart beat response
    """
    # Concatenate all the heartbeat request of CBSD into single request
    heartbeat_requests = []
    for cbsd_object_item in self.cbsd_objects.values():
      heartbeat_requests.extend(cbsd_object_item.constructHeartbeatRequestForAllActiveGrants())

    if len(heartbeat_requests):
      heartbeat_requests_wrapped = {
        'heartbeatRequest': heartbeat_requests
      }
      print heartbeat_requests_wrapped
      # Perform heartbeat requests
      heartbeat_responses = self.testcase._sas.Heartbeat(
        heartbeat_requests_wrapped, self.ssl_cert, self.ssl_key)['heartbeatResponse']

      for heartbeat_response in heartbeat_responses:
        cbsd_object = self.cbsd_objects[heartbeat_response['cbsdId']]
        grant_object = cbsd_object.grant_objects[heartbeat_response['grantId']]

        # Update grant state based on the heartbeat response
        self._mapResponseCodeToGrantState(heartbeat_response['response']['responseCode'],
                                         grant_object)

      return heartbeat_requests, heartbeat_responses

  def _mapResponseCodeToGrantState(self, heartbeat_response_code, grant_object):
    """Maps the heartbeat response and update the grant state."""
    if heartbeat_response_code == Grant.ResponseCodes.SUCCESS.value:
      grant_object.authorized_in_last_heartbeat = True
    elif heartbeat_response_code == Grant.ResponseCodes.TERMINATED_GRANT.value:
      grant_object.is_terminated = True
    elif heartbeat_response_code == Grant.ResponseCodes.SUSPENDED_GRANT.value:
      grant_object.authorized_in_last_heartbeat = False
    elif heartbeat_response_code == Grant.ResponseCodes.UNSYNC_OP_PARAM.value:
      grant_object.is_terminated = True
      grant_object.authorized_in_last_heartbeat = False
      logging.error('Received UNSYNC_OP_PARAM code in Heartbeat Response')
    else:
      logging.error('Unknown code=%s received in Heartbeat Response',heartbeat_response_code)

  def _constructGrantRequests(self,heartbeat_request):
    """Constrcut unwrapped version of grant request."""
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
    return grant_request

  def performHeartbeatAndUpdateGrants(self):
    """Does heartbeat request for all active grants and updates the grants.

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
    heartbeat_requests, heartbeat_responses = self.heartbeatRequestForAllActiveGrants()
    relinquishment_requests = []
    grant_requests = []

    # Construct relinquishment and grant for the heart beat response which have operation param
    for heartbeat_response, heartbeat_request in zip(heartbeat_responses, heartbeat_requests):
        if heartbeat_response['response']['responseCode'] == Grant.ResponseCodes.TERMINATED_GRANT.value:
           if 'operationParam' in heartbeat_response:
             # Construct grant request for Terminated grants
             grant_requests.append(self._constructGrantRequests(heartbeat_request))
           else:
             logging.error('Invalid Response since operation param not present in case of Terminated Grant')

        elif heartbeat_response['response']['responseCode'] != 0:
          # If any heartbeat contain suggested operation params,construct relinquishment requests
          if 'operationParam' in heartbeat_response:
            relinquishment_request = {
                'cbsdId': heartbeat_response['cbsdId'],
                'grantId': heartbeat_response['grantId']
            }
            relinquishment_requests.append(relinquishment_request)

            # Construct grant request for relinquished grants
            grant_requests.append(self._constructGrantRequests(heartbeat_request))

            # Delete the grant object
            del self.cbsd_objects[heartbeat_response['cbsdId']].grant_objects[heartbeat_response['grantId']]

    # Perform relinquishment since operation param present in heartbeat response
    if len(relinquishment_requests):
      relinquishment_requests_wrap = {
        'relinquishmentRequest': relinquishment_requests
      }
      relinquishment_responses = self.testcase._sas.Relinquishment(relinquishment_requests_wrap,
                                        self.ssl_cert, self.ssl_key)['relinquishmentResponse']

      # Validate the response of the relinquishment request
      for relinquishment_request, relinquishment_response in \
              zip(relinquishment_requests, relinquishment_responses):
        self.testcase.assertEqual(relinquishment_response['response']['responseCode'], 0)
        self.testcase.assertEqual(relinquishment_response['cbsdId'], relinquishment_request['cbsdId'])
        self.testcase.assertEqual(relinquishment_response['grantId'], relinquishment_request['grantId'])

    # Check if any grant request need to be sent
    if len(grant_requests):
      grant_requests_wrap = {
        'grantRequest': grant_requests
      }
      # Perform Grant for relinquished grants
      grant_responses = self.testcase._sas.Grant(grant_requests_wrap,
                                                 self.ssl_cert, self.ssl_key)['grantResponse']

      for grant_response, grant_request in zip(grant_responses, grant_requests):
        cbsd_object = self.cbsd_objects[grant_request['cbsdId']]
        cbsd_object.grant_objects[grant_response['grantId']] = Grant(grant_response['grantId'], grant_request)

    # Perform Heartbeat request for all grants
    self.heartbeatRequestForAllActiveGrants()

  def getCbsdsWithAtLeastOneAuthorizedGrant(self):
    """This function returns a list of CBSD with authorized grants.

    returns: list of CBSD objects.
    """
    cbsd_objects = []
    for cbsd_object in self.cbsd_objects.values():
      if cbsd_object.hasAuthorizedGrant():
        cbsd_objects.append(cbsd_object)
    return cbsd_objects
