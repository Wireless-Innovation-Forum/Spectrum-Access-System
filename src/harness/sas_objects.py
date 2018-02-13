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

from datetime import datetime
import json
import os
import shutil
import urllib

class Grant():
    """
        Holds the Grant related parameters
    """
    GRANTED, AUTHORIZED, OUT_OF_SYNC, TERMINATED, SUSPENDED = range(0, 5)

    def __init__(self, grant_id, grant_request):
        """
        Args:
           grant_id: grant id of the request
           grant_request: A dictionary with a single key-value pair where the key is
                            "grantRequest" and the value is grant request parameters

        """
        self.grant_id = grant_id
        self.grant_request = grant_request
        self.state = Grant.GRANTED

    def getGrantId(self):
        return self.grant_id

    def getGrantRequest(self):
        return self.grant_request

    def getRequestOperationParam(self):
        return self.grant_request['grantRequest'][0]['operationParam']

    def constructHeartbeatRequest(self):
        """
            This function constructs heartbeat request for the grant object
        """
        heartbeat_request = {
            'heartbeatRequest': [{
                'grantId': self.grant_id,
                'cbsdId': self.grant_request['grantRequest'][0]['cbsdId'],
                'operationState': "GRANTED"
            }]
        }
        return heartbeat_request

    def getState(self):
        return self.state

    def setState(self, state):
        self.state = state

    def isGrantAuthorizedInLastHeartbeat(self):
        """
            This function checks if the grant request was authorized in last heartbeat
        """
        if(Grant.AUTHORIZED == self.state):
            return True
        else:
            return False

    def isGrantActive(self):
        """
            This function check if the grant request is in Granted or Authorized state
        """
        if((Grant.AUTHORIZED == self.state) or (Grant.GRANTED == self.state)):
            return True
        else:
            return False


class Cbsd():
    """
        Holds the Cbsd related parameters
    """
    def __init__(self, cbsd_id, registration_request, grant_ids, grant_requests):
        """
        Args:
            cbsd_id:  cbsd id of the device extracted from the registration response
            registration_request: A dictionary with a single key-value pair where the key is
            "registrationRequest" and the value is a registration request content
            grant_ids: list of grant ids
            grant_requests: A list of dictionary with a single key-value pair where the key is
                "grantRequest" and the value is a list of individual CBSD grant
                requests (each of which is itself a dictionary).
        """
        assert (len(grant_requests) == len(grant_ids))
        self.cbsd_id = cbsd_id
        self.grant_objects = {}
        index = 0
        for grant_request in grant_requests:
            self.grant_objects[grant_ids[index]] = Grant(
                grant_ids[index], grant_request)
            index = index + 1
        self.registration_request = registration_request

    def getCbsdId(self):
        return self.cbsd_id

    def getGrantObject(self, grant_id):
        return self.grant_objects[grant_id]

    def getRegistrationRequest(self):
        return self.registration_request

    def doesCbsdHasActiveGrant(self):
        for grant_object in self.grant_objects.values():
            return grant_object.isGrantActive()

    def constructHeartbeatRequestForAllActiveGrants(self):
        """
        construct list of heartbeat requests of all active grants
        """
        heartbeat_requests = []
        for grant_object in self.grant_objects.values():
            if(grant_object.isGrantActive()):
                heartbeat_request = grant_object.constructHeartbeatRequest()
                heartbeat_requests.append(heartbeat_request)
        return heartbeat_requests

    def getOperationParamsOfAllAuthorizedGrants(self):
        """
        Returns the list of operation params of all authorized grants
        """
        operation_params = []
        for grant_object in self.grant_objects.values():
            if(grant_object.isGrantAuthorizedInLastHeartbeat()):
                operation_param = grant_object.getRequestOperationParam()
                operation_params.append(operation_param)
        return operation_params


class DomainProxy():
    """
        Holds the domain proxy related parameters
    """

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

    def initialize(self, registration_requests, grant_requests):
        """
        Args
            registration_requests:  A list of dictionary with a single key-value pair
                where the key is"registrationRequest" and the value is a list of
                individual CBSD registration  requests (each of which is itself a dictionary).
            grant_requests: A list of dictionary with a single key-value pair
                where the key is"grantRequest" and the value is a list of
                individual CBSD grant requests (each of which is itself a dictionary).
                There should be exactly one grant request per registration request.
        """
        #Checking if the number of registration requests matches number of grant requests
        #There should be exactly one grant request per registration request.
        assert (len(grant_requests) == len(registration_requests))
        cbsd_ids = self.testcase.assertRegistered(registration_requests)

        #Make one CBSD object per successful grant request
        for index, grant_request in enumerate(grant_requests):
            grant_request["grantRequest"][0]["cbsdId"] = cbsd_ids[index]
            grant_response = self.testcase._sas.Grant(grant_request, self.ssl_cert, self.ssl_key)[
                'grantResponse'][0]
            if grant_response['response']['responseCode'] == 0:
                cbsdobject = Cbsd(cbsd_ids[index], registration_requests[index],
                                  [grant_response['grantId']], [grant_request])
                self.cbsd_objects.update(
                    {grant_response['cbsdId']: cbsdobject})

    def getCbsdObjectById(self, cbsd_id):
        return self.cbsd_objects[cbsd_id]

    def heartbeatRequestForAllGrants(self):
        """
            This function performs heartbeat request for all grants
        """
        for cbsd_object_item in self.cbsd_objects.values():
            heartbeat_requests = cbsd_object_item.constructHeartbeatRequestForAllActiveGrants()
            for heartbeat_request in heartbeat_requests:
                heartbeat_response = self.testcase._sas.Heartbeat(
                    heartbeat_request, self.ssl_cert, self.ssl_key)['heartbeatResponse'][0]
                grant_object = cbsd_object_item.grant_objects[heartbeat_response['grantId']]
                if heartbeat_response['response']['responseCode'] == 0:
                    transmit_expire_time = datetime.strptime(heartbeat_response['transmitExpireTime'],
                                                             '%Y-%m-%dT%H:%M:%SZ')
                    self.testcase.assertLess(datetime.utcnow(), transmit_expire_time)
                    self.testcase.assertLessEqual(
                        (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
                    grant_object.setState(Grant.AUTHORIZED)
                else:
                    self.mapResponseCodeToGrantState(
                        heartbeat_response['response']['responseCode'], grant_object)

    def mapResponseCodeToGrantState(self, heartbeat_response_code, grant_object):
        """
            This function maps the heartbeat response code to the grant state
        """
        if (heartbeat_response_code == 502):
            grant_object.setState(Grant.OUT_OF_SYNC)
        elif (heartbeat_response_code == 500):
            grant_object.setState(Grant.TERMINATED)
        elif (heartbeat_response_code == 501):
            grant_object.setState(Grant.SUSPENDED)
        else:
            assert(not "Invalid grant response code")


    def performHeartbeatAndUpdateGrants(self):
        """
            This function construct heartbeat request for all active grants and updates the grants
        """
        for cbsd_object_item in self.cbsd_objects.values():
            heartbeat_responses_with_operation_parameters = {}

            #Heartbeat on all active grants
            heartbeat_requests = cbsd_object_item.constructHeartbeatRequestForAllActiveGrants()
            for heartbeat_request in heartbeat_requests:
                heartbeat_response = self.testcase._sas.Heartbeat(
                    heartbeat_request, self.ssl_cert, self.ssl_key)['heartbeatResponse'][0]
                grant_object = cbsd_object_item.grant_objects[heartbeat_response['grantId']]
                if heartbeat_response['response']['responseCode'] == 0:
                    transmit_expire_time = datetime.strptime(heartbeat_response['transmitExpireTime'],
                                                             '%Y-%m-%dT%H:%M:%SZ')
                    self.testcase.assertLess(datetime.utcnow(), transmit_expire_time)
                    self.testcase.assertLessEqual(
                        (transmit_expire_time - datetime.utcnow()).total_seconds(), 240)
                    grant_object.setState(Grant.AUTHORIZED)
                else:
                    self.mapResponseCodeToGrantState(
                        heartbeat_response['response']['responseCode'], grant_object)

                    #If any heartbeats contain suggested operating params,
                    #relinquish the corresponding grant
                    if 'operationParam' in heartbeat_response:
                        relinquish_request = {
                            'relinquishmentRequest': [{
                                'cbsdId': grant_object.getGrantRequest()['cbsdId'],
                                'grantId': grant_object.getGrantRequest()['grantId']
                            }]
                        }
                        self.testcase._sas.Relinquishment(
                            relinquish_request, self.ssl_cert, self.ssl_key)
                        heartbeat_responses_with_operation_parameters.update(
                            {heartbeat_response['cbsdId']: heartbeat_response})
                        del cbsd_object_item.grant_objects[heartbeat_response['grant_id']]

            #For all grants in the previous step, request a new grant with the
            #suggested operation parameters
            for cbsd_id, heartbeatResponse in heartbeat_responses_with_operation_parameters.items():
                grant_0 = json.load(
                    open(os.path.join('testcases', 'testdata', 'grant_0.json')))
                grant_0['cbsdId'] = cbsd_id
                grant_0['operationParam']['maxEirp'] = heartbeatResponse['operationParam']['maxEirp']
                grant_0['operationParam']['operationFrequencyRange']['lowFrequency'] = \
                    heartbeatResponse['operationParam']['operationFrequencyRange']['lowFrequency']
                grant_0['operationParam']['operationFrequencyRange']['highFrequency'] = \
                    heartbeatResponse['operationParam']['operationFrequencyRange']['highFrequency']
                request = {'grantRequest': [grant_0]}
                response = self.testcase._sas.Grant(request , self.ssl_cert, self.ssl_key)[
                    'grantResponse'][0]
                self.cbsd_objects.grant_objects.update(
                    {response['grantId']: request })
                if response['response']['responseCode'] == "0":
                    #Heartbeat all active grants
                    self.heartbeatRequestForAllGrants()

    def getCbsdsWithAtLeastOneAuthorizedGrant(self):
        """
        returns:
            cbsd_objects: list of cbsd objects
        """
        cbsd_objects = []
        for cbsd_object in self.cbsd_objects.values():
            for grant_object in cbsd_object.grant_objects.values():
                if(grant_object.getState() == Grant.AUTHORIZED):
                    cbsd_objects.append(cbsd_object)
        return cbsd_objects

class FullActivityDump():
    """
        Holds the full activity dump related parameters
    """
    cbsd_records = []
    ppa_records = []
    esc_records = []

    def __init__(self, ssl_cert, ssl_key, url, testcase):
        """
            ssl_cert: Path to SSL cert file
            ssl_key: Path to SSL key file
            url: url of the full activity dump record
            testcase: test case object from the caller
        """
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.url = url
        self.testcase = testcase
        self.folder_name = os.getcwd()+"/fad_content"

    def initiateFullActivityDump(self):
        """
        This function performs full activity dump operation
        """
        if not os.path.exists(self.folder_name):
            try:
                os.mkdir(self.folder_name, 0755)
            except:
                raise OSError(
                    "Can't create destination directory (%s)!" % self.folder_name)
        self.folder_name = self.folder_name + "/"+urllib.quote_plus(self.url)
        try:
            # if the folder exist it will be removed
            os.system("rm -rf  " + self.folder_name)
            os.mkdir(self.folder_name, 0755)
        except:
            raise OSError("Can't create destination directory (%s)!" %
                          self.folder_name)

        response = self.testcase._sas.GetUrl(self.url, self.ssl_cert, self.ssl_key)
        record = ""
        for dump_file in response['files']:
            #self.testcase.assertContainsRequiredFields("ActivityDumpFile.schema.json", dump_file)
            if dump_file['recordType'] == 'cbsd':
                record = self.downloadFileAndAppendRecord(
                    dump_file, dump_file['recordType'])
                #self.testcase.assertContainsRequiredFields("CbsdData.schema.json", record)
                self.cbsd_records.append(record)
            elif dump_file['recordType'] == 'esc_sensor':
                record = self.downloadFileAndAppendRecord(
                    dump_file, dump_file['recordType'])
                #self.testcase.assertContainsRequiredFields("EscSensorRecord.schema.json", record)
                self.esc_records.append(record)
            elif dump_file['recordType'] == 'zone':
                record = self.downloadFileAndAppendRecord(
                    dump_file, dump_file['recordType'])
                #self.testcase.assertContainsRequiredFields("zone.schema.json",record)
                self.ppa_records.append(record)

    def downloadFileAndAppendRecord(self, dump_file, record_type):
        """
        Args
            dump_file: json object received from peer SAS
            record_type: type of the record
        returns
            record fetched from peer SAS
        """
        url = dump_file['url']
        lastpart = url.rsplit('/', 1)
        record_dump = self.testcase._sas.DownloadFile(dump_file['url'])['recordData']
        filename = urllib.quote_plus(lastpart[1]) + record_type + ".json"
        file_obj = open(self.folder_name + "/" + filename, "a+")
        file_obj.write(str(record_dump))
        file_obj.close()
        return record_dump

    def getCbsdRecords(self):
        return self.cbsd_records

    def getEscSensorRecords(self):
        return self.esc_records

    def getPpaRecords(self):
        return self.ppa_records

    def __del__(self):
        shutil.rmtree(self.folder_name, ignore_errors=False, onerror=None)
