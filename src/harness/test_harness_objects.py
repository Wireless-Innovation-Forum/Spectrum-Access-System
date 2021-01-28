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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import logging
import math

import six
from six.moves import zip

import sas
import common_strings
from common_types import ResponseCodes
from sas_test_harness import generateCbsdReferenceId

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
        'operationState': 'GRANTED',
        'grantRenew': True
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
    if len(grant_requests) != len(grant_ids):
      raise ValueError('Cbsd builder: invalid grant_ids number')
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
    for grant_object in six.itervalues(self.grant_objects):
      if grant_object.isActive():
        return True
    return False

  def hasAuthorizedGrant(self):
    for grant_object in six.itervalues(self.grant_objects):
      if grant_object.isGrantAuthorizedInLastHeartbeat():
        return True
    return False

  def getAuthorizedGrants(self):
    grants = []
    for grant_object in six.itervalues(self.grant_objects):
      if grant_object.isGrantAuthorizedInLastHeartbeat():
        grants.append(grant_object)
    return grants

  def constructHeartbeatRequestForAllActiveGrants(self):
    """Construct list of heartbeat requests of all active grants."""
    heartbeat_requests = []
    for grant_object in  six.itervalues(self.grant_objects):
      if grant_object.isActive():
        heartbeat_requests.append(grant_object.constructHeartbeatRequest())
    return heartbeat_requests

  def getOperationParamsOfAllAuthorizedGrants(self):
    """Returns the list of operation params of all authorized grants."""
    operation_params = []
    for grant_object in six.itervalues(self.grant_objects):
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
    self.ssl_cert = ssl_cert if ssl_cert else sas.GetDefaultDomainProxySSLCertPath()
    self.ssl_key = ssl_key if ssl_key else sas.GetDefaultDomainProxySSLKeyPath()
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
    try:
      cbsd_ids = self._tryRegistrationWithMaximumBatchSize(
          registration_requests, conditional_registration_data)
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION)
      raise

    # Copy the cbsdId from Registration response to grant requests, omitting
    # grant requests for CBSDs which were not successfully registered.
    actual_grant_requests = []
    for cbsd_id, grant_request in zip(cbsd_ids, grant_requests):
      if cbsd_id:  # cbsd_id is None if registration was unsuccessful.
        grant_request['cbsdId'] = cbsd_id
        actual_grant_requests.append(grant_request)

    # Perform grant operation.
    grant_responses = self._grantRequestWithMaximumBatchSize(actual_grant_requests)

    # Check the length of grant responses is the same as grant requests.
    self.testcase.assertEqual(len(grant_responses), len(actual_grant_requests))

    # Extract only the successful registration requests and corresponding CBSD IDs.
    actual_registration_requests = [req for req, cbsd_id in zip(registration_requests, cbsd_ids) if cbsd_id]
    actual_cbsd_ids = [cbsd_id for cbsd_id in cbsd_ids if cbsd_id]

    # Make one CBSD object per successful grant request.
    # All arrays in the zip() will have the same length based on the filtering
    # above, but we'll double-check to be sure.
    self.testcase.assertEqual(len(actual_grant_requests), len(actual_registration_requests))
    self.testcase.assertEqual(len(actual_grant_requests), len(actual_cbsd_ids))
    for grant_request, grant_response, registration_request, cbsd_id in zip(
        actual_grant_requests, grant_responses, actual_registration_requests, actual_cbsd_ids):
      if grant_response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
        self._mergeConditionals(registration_request, conditional_registration_data)
        cbsd_object = Cbsd(cbsd_id, registration_request,
                           [grant_response['grantId']], [grant_request])
        self.cbsd_objects[cbsd_id] = cbsd_object

  def registerCbsdsAndRequestGrantsWithPpa(self,
                                           registration_requests,
                                           grant_requests,
                                           ppa_record,
                                           cluster_list,
                                           conditional_registration_data=None):
    """Construct CBSD object based on the result of registration and
    grant requests. Registers the CBSDs, injects the PPA, and requests grants.

    Args
      registration_requests: A list of dictionary elements, where each list
        element is an individual CBSD registration request (which is itself a
        dictionary).
      grant_requests: A list of dictionary elements, where each list element is
        an individual CBSD grant request (which is itself a dictionary).
      ppa_record: the PPA record to inject after registration.
      cluster_list: indices indicating which CBSDs are on the cluster list.
      conditional_registration_data: A list of individual CBSD registration
        data that need to be preloaded into SAS (each of which is a dictionary).
        The dictionary is a RegistrationRequest object, the fccId and
        cbsdSerialNumber fields are required, other fields are optional.

    Returns
      ppa_record_with_cbsd_ids: the input PPA record with the cluster list (of
        CBSD IDs) added.
      ppa_record_with_reference_ids: the input PPA record with the cluster list
        (of CBSD reference IDs) added.
    """
    # Checking if the number of registration requests matches number of grant requests.
    # There should be exactly one grant request per registration request.
    self.testcase.assertEqual(len(grant_requests), len(registration_requests))
    try:
      cbsd_ids = self._tryRegistrationWithMaximumBatchSize(
          registration_requests, conditional_registration_data)
    except Exception:
      logging.error(common_strings.EXPECTED_SUCCESSFUL_REGISTRATION)
      raise

    # BEGIN PPA-specific logic.
    # Form the cluster list from the CBSD IDs corresponding to the input
    # indices, taking care to only include those which were actually registered.
    cbsd_id_cluster_list = [cbsd_ids[i] for i in cluster_list if cbsd_ids[i]]
    ppa_record['ppaInfo']['cbsdReferenceId'] = cbsd_id_cluster_list
    self.testcase._sas_admin.InjectZoneData({'record': ppa_record})
    ppa_record_with_cbsd_ids = ppa_record
    # But the reference model will be looking to compare with CBSD reference
    # IDs, which are not necessarily the same as the CBSD IDs. So now that the
    # PPA has been injected, we need to put the CBSD reference IDs into the PPA
    # record so that the reference model will do the right thing.
    ppa_record_with_reference_ids = copy.deepcopy(ppa_record)
    def makeReferenceId(reg_request):
      return 'cbsd/' + generateCbsdReferenceId(reg_request['fccId'],
                                               reg_request['cbsdSerialNumber'])
    reference_id_cluster_list = []
    for i in cluster_list:
      if not cbsd_ids[i]:
        continue  # Skip if not registered.
      reference_id_cluster_list.append(makeReferenceId(registration_requests[i]))
    ppa_record_with_reference_ids['ppaInfo'][
        'cbsdReferenceId'] = reference_id_cluster_list
    # END PPA-specific logic. (Note: return statement also added.)

    # Copy the cbsdId from Registration response to grant requests, omitting
    # grant requests for CBSDs which were not successfully registered.
    actual_grant_requests = []
    for cbsd_id, grant_request in zip(cbsd_ids, grant_requests):
      if cbsd_id:  # cbsd_id is None if registration was unsuccessful.
        grant_request['cbsdId'] = cbsd_id
        actual_grant_requests.append(grant_request)

    # Perform grant operation.
    grant_responses = self._grantRequestWithMaximumBatchSize(actual_grant_requests)

    # Check the length of grant responses is the same as grant requests.
    self.testcase.assertEqual(len(grant_responses), len(actual_grant_requests))

    # Extract only the successful registration requests and corresponding CBSD IDs.
    actual_registration_requests = [req for req, cbsd_id in zip(registration_requests, cbsd_ids) if cbsd_id]
    actual_cbsd_ids = [cbsd_id for cbsd_id in cbsd_ids if cbsd_id]

    # Make one CBSD object per successful grant request.
    # All arrays in the zip() will have the same length based on the filtering
    # above, but we'll double-check to be sure.
    self.testcase.assertEqual(len(actual_grant_requests), len(actual_registration_requests))
    self.testcase.assertEqual(len(actual_grant_requests), len(actual_cbsd_ids))
    for grant_request, grant_response, registration_request, cbsd_id in zip(
        actual_grant_requests, grant_responses, actual_registration_requests, actual_cbsd_ids):
      if grant_response['response']['responseCode'] == ResponseCodes.SUCCESS.value:
        self._mergeConditionals(registration_request, conditional_registration_data)
        cbsd_object = Cbsd(cbsd_id, registration_request,
                           [grant_response['grantId']], [grant_request])
        self.cbsd_objects[cbsd_id] = cbsd_object

    return ppa_record_with_cbsd_ids, ppa_record_with_reference_ids


  def _mergeConditionals(self, registration_request, conditionals):
    if not conditionals:
      return
    for conditional in conditionals:
      if conditional['fccId'] == registration_request['fccId'] and conditional['cbsdSerialNumber'] == registration_request['cbsdSerialNumber']:
        for key, value in six.iteritems(conditional):
          if key not in registration_request:
            registration_request[key] = value
        break

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
    heartbeat_responses = []
    for cbsd_object_item in six.itervalues(self.cbsd_objects):
      heartbeat_requests.extend(cbsd_object_item.constructHeartbeatRequestForAllActiveGrants())

    if len(heartbeat_requests):
      heartbeat_responses = self._heartbeatRequestWithMaximumBatchSize(
          heartbeat_requests)

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
      grant_object.authorized_in_last_heartbeat = False
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
            grant_requests.append(self._constructGrantRequest(heartbeat_response))

            # Delete the grant object
            del self.cbsd_objects[heartbeat_response['cbsdId']].grant_objects[heartbeat_response['grantId']]

    # Perform relinquishment since operation param present in heartbeat response.
    if len(relinquishment_requests):
      relinquishment_responses = self._relinquishmentRequestWithMaximumBatchSize(relinquishment_requests)

      # Check the length of relinquishment responses is the same as relinquishment request.
      self.testcase.assertEqual(len(relinquishment_responses), len(relinquishment_requests))

      # Validate the response of the relinquishment request.
      for relinquishment_request, relinquishment_response in zip(
          relinquishment_requests, relinquishment_responses):
        self.testcase.assertEqual(relinquishment_response['response']['responseCode'],
                                  ResponseCodes.SUCCESS.value)
        self.testcase.assertEqual(relinquishment_response['cbsdId'], relinquishment_request['cbsdId'])
        self.testcase.assertEqual(relinquishment_response['grantId'], relinquishment_request['grantId'])

    # Check if any grant request need to be sent.
    if len(grant_requests):
      # Perform Grant for relinquished grants.
      grant_responses = self._grantRequestWithMaximumBatchSize(grant_requests)

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
    for cbsd_object in six.itervalues(self.cbsd_objects):
      if cbsd_object.hasAuthorizedGrant():
        cbsd_objects.append(cbsd_object)
    return cbsd_objects

  def _withMaximumBatchSize(self, requests, request_name):
    """Split the requests into batches and call the given function.

    Args:
      requests: The requests to split by batchsize.
      request_name: The name of the request. For logging.
    Yields:
      Lists of requests containing at most maximum_batch_size requests.
    """
    maximum_batch_size = self.testcase._sas.maximum_batch_size
    num_batches = int(math.ceil(len(requests) / float(maximum_batch_size)))
    logging.info('Sending %i %s requests in batches of %i (%i batches)',
                 len(requests), request_name, maximum_batch_size, num_batches)
    for iteration in range(0, num_batches):
      batch_requests = requests[iteration * maximum_batch_size:(iteration + 1) *
                                maximum_batch_size]
      yield batch_requests

  def _tryRegistration(self,
                   registration_request,
                   conditional_registration_data=None,
                   cert=None,
                   key=None):
    """Similar to |SasTestCase.assertRegistered|, but ignores errors."""
    if not registration_request:
      return []
    for device in registration_request:
      self.testcase._sas_admin.InjectFccId({'fccId': device['fccId']})
      self.testcase._sas_admin.InjectUserId({'userId': device['userId']})
    if conditional_registration_data:
      self.testcase._sas_admin.PreloadRegistrationData({
          'registrationData': conditional_registration_data
      })

    # Pass the correct client cert and key in Registration request
    ssl_cert = cert if cert is not None else self._sas._tls_config.client_cert
    ssl_key = key if key is not None else self._sas._tls_config.client_key

    request = {'registrationRequest': registration_request}
    response = self.testcase._sas.Registration(
        request, ssl_cert=ssl_cert, ssl_key=ssl_key)['registrationResponse']

    self.testcase.assertEqual(len(response), len(registration_request))
    # Check the registration response; collect CBSD IDs.
    cbsd_ids = []
    for request, resp in zip(registration_request, response):
      if resp['response']['responseCode'] == 0:
        self.testcase.assertTrue('cbsdId' in resp)
        cbsd_ids.append(resp['cbsdId'])
      else:
        logging.warning(
            'CBSD registration failed: unexpected response %s for request %s',
            resp, request)
        cbsd_ids.append(None)

    # Return list of cbsd_ids
    return cbsd_ids

  def _tryRegistrationWithMaximumBatchSize(self, registration_requests,
                                            conditional_registration_data):
    """Sends registration requests in batches up to the maximum batch size.

    Args:
      registration_requests: All registration requests we wish to send.
      conditional_registration_data: Optional, any conditional registration data
        for the CBSDs.
    Returns:
      The cbsd_ids from each registration request.
    Raises:
      AssertionError: If any registration responses are invalid.
    """
    # Make sure FccId and userId are injected before conditionals. The
    # optimization in the SAS interface will prevent duplicate requests from
    # being sent.
    if conditional_registration_data:
      for device in registration_requests:
        self.testcase._sas_admin.InjectFccId({'fccId': device['fccId']})
        self.testcase._sas_admin.InjectUserId({'userId': device['userId']})
      for data in self._withMaximumBatchSize(conditional_registration_data,
                                             'PreloadRegistrationData'):
        self.testcase._sas_admin.PreloadRegistrationData({
            'registrationData': data
        })
    cbsd_ids = []
    for requests in self._withMaximumBatchSize(registration_requests,
                                               'Registration'):
      cbsd_ids.extend(
          self._tryRegistration(requests, cert=self.ssl_cert, key=self.ssl_key))
    return cbsd_ids

  def _grantRequestWithMaximumBatchSize(self, grant_requests):
    """Sends grant requests in batches up to the maximum batch size.

    Args:
      grant_requests: All grant requests we wish to send.
    Returns:
      The grant responses for each grant_request.
    """
    grant_responses = []
    for requests in self._withMaximumBatchSize(grant_requests, 'Grant'):
      # Wrapped version of the grant requests.
      grant_requests_wrap = {'grantRequest': requests}
      grant_responses.extend(
          self.testcase._sas.Grant(grant_requests_wrap, self.ssl_cert,
                                   self.ssl_key)['grantResponse'])
    return grant_responses

  def _heartbeatRequestWithMaximumBatchSize(self, heartbeat_requests):
    """Sends heartbeat requests in batches up to the maximum batch size.

    Args:
      heartbeat_requests: All heartbeat requests we wish to send.
    Returns:
      The heartbeat responses for each heartbeat_request.
    """
    heartbeat_responses = []
    for requests in self._withMaximumBatchSize(heartbeat_requests, 'Heartbeat'):
      # Wrapped version of the heartbeat requests.
      heartbeat_requests_wrap = {'heartbeatRequest': requests}
      heartbeat_responses.extend(
          self.testcase._sas.Heartbeat(heartbeat_requests_wrap, self.ssl_cert,
                                       self.ssl_key)['heartbeatResponse'])
    return heartbeat_responses

  def _relinquishmentRequestWithMaximumBatchSize(self, relinquishment_requests):
    """Sends relinquishment requests in batches up to the maximum batch size.

    Args:
      relinquishment_requests: All relinquishment requests we wish to send.
    Returns:
      The relinquishment responses for each relinquishment_request.
    """
    relinquishment_responses = []
    for requests in self._withMaximumBatchSize(relinquishment_requests,
                                               'Relinquishment'):
      # Wrapped version of the grant requests.
      relinquishment_requests_wrap = {'relinquishmentRequest': requests}
      relinquishment_responses.extend(
          self.testcase._sas.Relinquishment(
              relinquishment_requests_wrap, self.ssl_cert,
              self.ssl_key)['relinquishmentResponse'])
    return relinquishment_responses
