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
import logging
from common_types import ResponseCodes

class Grant(object):
  """Holds the Grant request parameters."""

  def __init__(self, grant_id, grant_request):
    """Store grant parameters and initialize state variables.

    Args:
      grant_id: grant id of the request.
      grant_request: A dictionary containing the grant request parameters.
    """
    # Store the grant parameters.
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

  def getAuthorizedGrants(self):
    grants = []
    for grant_object in self.grant_objects.itervalues():
      if grant_object.isGrantAuthorizedInLastHeartbeat():
        grants.append(grant_object)
    return grants

  def constructHeartbeatRequestForAllActiveGrants(self):
    """Construct list of heartbeat requests of all active grants."""
    heartbeat_requests = []
    for grant_object in self.grant_objects.itervalues():
      if grant_object.isActive():
        heartbeat_requests.append(grant_object.constructHeartbeatRequest())
    return heartbeat_requests

  def getOperationParamsOfAllAuthorizedGrants(self):
    """Returns the list of operation params of all authorized grants."""
    operation_params = []
    for grant_object in self.grant_objects.itervalues():
      if grant_object.isGrantAuthorizedInLastHeartbeat():
        operation_params.append(grant_object.getRequestOperationParam())
    return operation_params


class DomainProxy(object):
  """Performs Domain Proxy related operations.

  This class stores Domain Proxy related information like the SSL certificate, key to be used and the set of
  CBSD objects belonging to this Domain Proxy. Bulk operations like registration, grant and heartbeat
  procedures are performed on all of the CBSDs belonging to this Domain Proxy.
  """
  def __init__(self, testcase, ssl_cert=None, ssl_key=None):
    """
    Args:
      ssl_cert: Path to SSL cert file.
      ssl_key: Path to SSL key file.
      testcase: test case object from the caller.
    """
    self.ssl_cert = ssl_cert if ssl_cert else self.GetDefaultDomainProxySSLCertPath()
    self.ssl_key = ssl_key if ssl_key else self.GetDefaultDomainProxySSLKeyPath()
    self.cbsd_objects = {}
    self.testcase = testcase

  def registerCbsdsAndRequestGrants(self,
                                    registration_requests,
                                    grant_requests,
                                    conditional_registration_data=None):
    """Construct CBSD object based on the result of registration and
    grant requests.

    Args
      registration_requests: A list of dictionary elements, where each list
        element is an individual CBSD registration request (which is itself a
        dictionary).
      grant_requests: A list of dictionary elements, where each list element is
        an individual CBSD grant request (which is itself a dictionary).
      conditional_registration_data: A list of individual CBSD registration
        data that need to be preloaded into SAS (each of which is a dictionary).
        The dictionary is a RegistrationRequest object, the fccId and
        cbsdSerialNumber fields are required, other fields are optional.
    """
    # Checking if the number of registration requests matches number of grant requests.
    # There should be exactly one grant request per registration request.
    self.testcase.assertEqual(len(grant_requests), len(registration_requests))
    cbsd_ids = self.testcase.assertRegistered(
        registration_requests,
        conditional_registration_data=conditional_registration_data,
        cert=self.ssl_cert,
        key=self.ssl_key)

    # Copy the cbsdId from Registration response to grant requests.
    for cbsd_id, grant_request in zip(cbsd_ids, grant_requests):
      grant_request['cbsdId'] = cbsd_id

    # Wrapped version of the grant requests.
    grant_requests_wrap = {
      'grantRequest': grant_requests
    }

    #perform grant operation.
    grant_responses = self.testcase._sas.Grant(grant_requests_wrap,
                                               self.ssl_cert, self.ssl_key)['grantResponse']

    # Check the length of grant responses is the same as grant requests.
    self.testcase.assertEqual(len(grant_responses), len(grant_requests))

    # Make one CBSD object per successful grant request.
    for grant_request, grant_response, \
        registration_request, cbsd_id in zip(grant_requests,
                                             grant_responses, registration_requests, cbsd_ids):
      if grant_response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
        cbsd_object = Cbsd(cbsd_id, registration_request,
                           [grant_response['grantId']], [grant_request])
        self.cbsd_objects[cbsd_id] = cbsd_object

  def getCbsdObjectById(self, cbsd_id):
      return self.cbsd_objects[cbsd_id]

  def heartbeatForAllActiveGrants(self):
    """Performs heartbeat request for all grants of CBSD devices at once.

    Returns:
      heartbeat_requests : list of heartbeat requests which are constructed for all the grants
      by the caller.
      heartbeat_responses: list of heartbeat response.
    """
    # Concatenate all the heartbeat request of CBSD into single request.
    heartbeat_requests = []
    for cbsd_object_item in self.cbsd_objects.itervalues():
      heartbeat_requests.extend(cbsd_object_item.constructHeartbeatRequestForAllActiveGrants())

    if len(heartbeat_requests):
      heartbeat_requests_wrapped = {
        'heartbeatRequest': heartbeat_requests
      }
      # Perform heartbeat requests.
      heartbeat_responses = self.testcase._sas.Heartbeat(
        heartbeat_requests_wrapped, self.ssl_cert, self.ssl_key)['heartbeatResponse']

      # Check the length of heartbeat responses is the same as heartbeat requests.
      self.testcase.assertEqual(len(heartbeat_responses), len(heartbeat_requests))

      for heartbeat_request, heartbeat_response in zip(heartbeat_requests, heartbeat_responses):
        cbsd_object = self.cbsd_objects[heartbeat_request['cbsdId']]
        grant_object = cbsd_object.grant_objects[heartbeat_request['grantId']]

        # Update grant state based on the heartbeat response.
        self._mapResponseCodeToGrantState(heartbeat_response['response']['responseCode'],
                                         grant_object)

      return heartbeat_requests, heartbeat_responses

  def _mapResponseCodeToGrantState(self, heartbeat_response_code, grant_object):
    """Maps the heartbeat response and update the grant state."""
    if heartbeat_response_code == ResponseCodes.SUCCESS.value:
      grant_object.authorized_in_last_heartbeat = True
    elif heartbeat_response_code == ResponseCodes.TERMINATED_GRANT.value:
      grant_object.is_terminated = True
    elif heartbeat_response_code == ResponseCodes.SUSPENDED_GRANT.value:
      grant_object.authorized_in_last_heartbeat = False
    else:
      logging.error('Unknown code=%s received in Heartbeat Response',heartbeat_response_code)
      raise Exception('Unknown code received in Heartbeat Response')

  def _constructGrantRequest(self,heartbeat_response):
    """Construct unwrapped version of grant request."""
    grant_request = {
      'cbsdId': heartbeat_response['cbsdId'],
      'operationParam': {
        'maxEirp': heartbeat_response['operationParam']['maxEirp'],
        'operationFrequencyRange': {
          'lowFrequency': heartbeat_response['operationParam']['operationFrequencyRange']['lowFrequency'],
          'highFrequency': heartbeat_response['operationParam']['operationFrequencyRange']['highFrequency']
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
    heartbeat_requests, heartbeat_responses = self.heartbeatForAllActiveGrants()
    relinquishment_requests = []
    grant_requests = []

    # Construct relinquishment and grant for the heartbeat response which have operation param.
    for heartbeat_response, heartbeat_request in zip(heartbeat_responses, heartbeat_requests):
        if heartbeat_response['response']['responseCode'] == ResponseCodes.TERMINATED_GRANT.value:
           if 'operationParam' in heartbeat_response:
             # Construct grant request for Terminated grants
             grant_requests.append(self._constructGrantRequest(heartbeat_response))
           else:
             logging.error('Invalid Response received for grantId=%s and cbsdId=%s',
                           heartbeat_response['grantId'], heartbeat_response['cbsdId'])
           # Delete the grant object
           del self.cbsd_objects[heartbeat_response['cbsdId']].grant_objects[heartbeat_response['grantId']]

        elif heartbeat_response['response']['responseCode'] == ResponseCodes.SUSPENDED_GRANT.value:
          # If any heartbeat contain suggested operation params,construct relinquishment requests.
          if 'operationParam' in heartbeat_response:
            relinquishment_request = {
                'cbsdId': heartbeat_response['cbsdId'],
                'grantId': heartbeat_response['grantId']
            }
            relinquishment_requests.append(relinquishment_request)

            # Construct grant request for relinquished grants
            grant_requests.append(self._constructGrantRequest(heartbeat_request))

            # Delete the grant object
            del self.cbsd_objects[heartbeat_response['cbsdId']].grant_objects[heartbeat_response['grantId']]

    # Perform relinquishment since operation param present in heartbeat response.
    if len(relinquishment_requests):
      relinquishment_requests_wrap = {
        'relinquishmentRequest': relinquishment_requests
      }
      relinquishment_responses = self.testcase._sas.Relinquishment(relinquishment_requests_wrap,
                                        self.ssl_cert, self.ssl_key)['relinquishmentResponse']

      # Check the length of relinquishment responses is the same as relinquishment request.
      self.testcase.assertEqual(len(relinquishment_responses), len(relinquishment_requests))

      # Validate the response of the relinquishment request.
      for relinquishment_request, relinquishment_response in \
              zip(relinquishment_requests, relinquishment_responses):
        self.testcase.assertEqual(relinquishment_response['response']['responseCode'],
                                  ResponseCodes.SUCCESS.value)
        self.testcase.assertEqual(relinquishment_response['cbsdId'], relinquishment_request['cbsdId'])
        self.testcase.assertEqual(relinquishment_response['grantId'], relinquishment_request['grantId'])

    # Check if any grant request need to be sent.
    if len(grant_requests):
      grant_requests_wrap = {
        'grantRequest': grant_requests
      }
      # Perform Grant for relinquished grants.
      grant_responses = self.testcase._sas.Grant(grant_requests_wrap,
                                                 self.ssl_cert, self.ssl_key)['grantResponse']

      # Check the length of grant responses is the same as grant requests.
      self.testcase.assertEqual(len(grant_responses), len(grant_requests))

      for grant_response, grant_request in zip(grant_responses, grant_requests):
        if grant_response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
          cbsd_object = self.cbsd_objects[grant_request['cbsdId']]
          cbsd_object.grant_objects[grant_response['grantId']] = Grant(grant_response['grantId'], grant_request)
        else:
          logging.debug("Grant request failed for the cbsdId=%s",grant_request['cbsdId'])

    # Perform Heartbeat request for all grants.
    self.heartbeatForAllActiveGrants()

  def getCbsdsWithAtLeastOneAuthorizedGrant(self):
    """This function returns a list of CBSD with authorized grants.

    returns: list of CBSD objects.
    """
    cbsd_objects = []
    for cbsd_object in self.cbsd_objects.itervalues():
      if cbsd_object.hasAuthorizedGrant():
        cbsd_objects.append(cbsd_object)
    return cbsd_objects

  def GetDefaultDomainProxySSLCertPath(self):
  return os.path.join('certs', 'client.cert')

  def GetDefaultDomainProxySSLKeyPath(self):
    return os.path.join('certs', 'client.key')
