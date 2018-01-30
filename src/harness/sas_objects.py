#    Copyright 2016 SAS Project Authors. All Rights Reserved.
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
import json
import os
import sas
import urllib


class Grant:

    """
    A Grant object has the following methods
     __init__
          Parameters: grant ID, grant request
    Retrieve  grant ID,
    Retrieve  grant request
    Retrieve operation params
    Construct heartbeat request
    Update was authorized in last heartbeat? state
    Retrieve was authorized in last heartbeat
    """

    def __init__(self, g_id, g_request):
        self.grant_id = g_id
        self.grant_request = g_request
        self.grant_authorized_in_last_heartbeat = False

    def get_grant_id(self):
        """

        :rtype: grant_id
        """
        return self.grant_id

    def get_grant_request(self):
        """

        :rtype: grant_request
        """
        return self.grant_request

    def get_request_operation_param(self):
        """

        :rtype: operationParam
        """
        return self.grant_request['grantRequest'][0]['operationParam']

    def construct_heartbeat_request(self):
        """

        :rtype: heartbeat_request
        """
        heartbeat_request = {
            'heartbeatRequest': [{
                'grantId': self.grant_id,
                'cbsdId': self.grant_request['grantRequest'][0]['cbsdId'],
                'operationState': "GRANTED"
            }]
        }
        return heartbeat_request

    def update_grant_authorized_in_last_heartbeat(self, is_authorized):
        self.grant_authorized_in_last_heartbeat = is_authorized

    def get_grant_authorized_in_last_heartbeat(self):
        """

        :rtype: grant_authorized_in_last_heartbeat
        """
        return self.grant_authorized_in_last_heartbeat


class Cbsd:

    """
    A CBSD object has the following methods
        __init__
            Parameters: CBSD ID, successful registration request, grant ID, successful grant request
        Retrieve   CBSD ID,
        Retrieve successful registration request,
        Retrieve grant request, successful
            Parameter: grant request
        Does this CBSD have at least one active grant?
        Construct heartbeat request for all active grants
        Return operating params for all grants which are authorized to transmit
    """
    def __init__(self, c_id, reg_request, g_id, grant_requests):
        self.cbsd_id = c_id
        self.grant_objects = {}
        for index, grantRequest in enumerate(grant_requests):
            self.grant_objects[g_id[index]] = Grant(g_id[index], grantRequest)
        self.successful_registration_request = reg_request

    def get_cbsd_id(self):
        """

        :rtype: cbsd_id
        """
        return self.cbsd_id

    def get_grant_request(self, grant_id):
        """

        :rtype: grant_objects
        """
        return self.grant_objects[grant_id]

    def get_registration_request(self):
        """

        :rtype: successful_registration_request
        """
        return self.successful_registration_request

    def cbsd_id_has_atleast_one_grant(self):
        """

        :rtype: bool
        """
        for grant_id, grant_request in self.grant_objects.items():
            if grant_request.get_grant_authorized_in_last_heartbeat():
                return True
        return False

    def construct_heartbeat_request_for_all_active_grant(self):
        """

        :rtype: heartbeat_requests
        """
        heartbeat_requests = []
        for grant_id, grant_object in self.grant_objects.items():
            heartbeat_request = grant_object.construct_heartbeat_request()
            heartbeat_requests.append(heartbeat_request)
        return heartbeat_requests

    def get_all_operation_params_of_grant_request(self):
        """

        :rtype: operation_params
        """
        operation_params = []
        for grant_id, grant_object in self.grant_objects.items():
            if True == grant_object.get_grant_authorized_in_last_heartbeat():
                operation_param = grant_object.get_request_operation_param()
                operation_params.append(operation_param)
        return operation_params


class DomainProxy:

    """
    A DP object has the following methods
        __init__
                Parameters: certificate, N registration requests, N grant requests
                Send N registration requests, expect success for all
                Send N grant requests, allow failure

        Retrieve CBSD object with CBSD ID = C
        Heartbeat all CBSDs/Grants (and update internal state)
        Heartbeat/relinquish/grant/heartbeat request for all CBSDs (and update internal state)
            Heartbeat on all active grants (allow all failures)
            If any HBs contain suggested operating params, relinquish the corresponding grant
            For all grants in the previous step, request a new grant with the suggested operating parameters
                            (allow failure)
            Heartbeat all active grants (allow all failures)
        Retrieve all CBSD objects with at least one grant which is authorized to transmit
    """

    def __init__(self, certificate, key, registration_requests, grant_requests):
        # checking for the number of registration requests matches number of grant requests
        if len(registration_requests) != len(grant_requests):
            return
        self.dp_certificate = certificate
        self.dp_key = key
        self.cbsd_objects = {}
        cbsd_id = []
        self.sas_admin = sas.GetTestingSas()
        for registerRequest in registration_requests[:]:
            response = self.sas_admin.Registration(registerRequest, self.dp_certificate, self.dp_key)\
                                                                  ['registrationResponse'][0]
            cbsd_id.append(response['cbsdId'])
            self.sas_admin.assertEqual(response['response']['responseCode'], 0)
        # here the registrationRequest & grant request has 1to1 mapping
        # The variable index used as subscript of registration request while looping through
        #   the grant requests since they are 1to1 mapped
        # Make one CBSD object per successful grant request
        for index, grant_request in enumerate(grant_requests[:]):
            grant_request['cbsdId'] = cbsd_id[index]
            response = self.sas_admin.Grant(grant_request,self.dp_certificate,self.dp_key)['grantResponse'][0]
            if response['response']['responseCode'] == "0":
                cbsdobject = Cbsd(cbsd_id[index],registration_requests[index],response['grantId'],grant_request)
                self.cbsd_objects.update({response['cbsdId'],cbsdobject})

    def get_cbsd_object(self,cbsd_id):
        """

        :rtype: cbsd_objects
        """
        return self.cbsd_objects[cbsd_id]

    def heartbeat_request_for_all_grants(self):
        for cbsdId, cbsdObjectItem in self.cbsd_objects.items():
            for grantId, grantObject in cbsdObjectItem.Grant_Objects.items():
                heartbeatRequests = cbsdObjectItem.construct_heartbeat_request_for_all_active_grant()
                hbResponses = self.sas_admin.Heartbeat(heartbeatRequests,self.dp_certificate,self.dp_key) \
                                ['heartbeatResponse'][0]
                for hbReponse in hbResponses:
                    grantobject = cbsdObjectItem.Grant_Objects[hbReponse['grantId']]
                    if hbReponse['response']['responseCode'] == "0":
                        grantobject.update_grant_authorized_in_last_heartbeat(True)
                    else:
                        grantobject.update_grant_authorized_in_last_heartbeat(False)

    def heartbeat_request_for_all_grant_and_update_grants(self):
        for cbsd_id, cbsd_object_item in self.cbsd_objects.items():
            for grant_id, grant_object in cbsd_object_item.grant_objects.items():
                relinquish_hb_responses = {}
                # Heartbeat on all active grants
                heartbeat_requests = cbsd_object_item.construct_heartbeat_request_for_all_active_grant()
                hb_responses = self.sas_admin.Heartbeat(heartbeat_requests,
                                                        self.dp_certificate, self.dp_key)['heartbeatResponse'][0]
                for hb_reponse in hb_responses:
                    grantobject = cbsd_object_item.grant_objects[hb_reponse['grantId']]
                    if hb_reponse['response']['responseCode'] == "0":
                        grantobject.update_grant_authorized_in_last_heartbeat(True)
                    else:
                        grantobject.update_grant_authorized_in_last_heartbeat(False)
                        #    If any HBs contain suggested operating params, relinquish the corresponding grant
                        if 'operationParam' in hb_reponse:
                            relinquish_request = {
                                'relinquishmentRequest': [{
                                    'cbsdId': hb_reponse['cbsdId'],
                                    'grantId': hb_reponse['grantId']
                                }]
                            }
                            self.sas_admin.Relinquishment(relinquish_request, self.dp_certificate, self.dp_key)
                            relinquish_hb_responses.update({hb_reponse['cbsdId']: hb_reponse})
                            del cbsd_object_item.grant_objects[grant_id]
                #For all grants in the previous step, request a new grant with the
                # suggested operating parameters (allow failure)
                for cbsdId, hbresponse in relinquish_hb_responses.items():
                        grant_0 = json.load(
                            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
                        grant_0['cbsdId'] = cbsdId
                        grant_0['operationParam']['maxEirp'] = hbresponse['operationParam']['maxEirp']
                        grant_0['operationParam']['operationFrequencyRange']['lowFrequency'] = \
                            hbresponse['operationParam']['operationFrequencyRange']['lowFrequency']
                        grant_0['operationParam']['operationFrequencyRange']['highFrequency'] = \
                            hbresponse['operationParam']['operationFrequencyRange']['highFrequency']
                        temp_grant_request = {'grantRequest': [grant_0]}
                        response = self.sas_admin.Grant(temp_grant_request,self.dp_certificate,self.dp_key)['grantResponse'][0]
                        self.cbsd_objects.grant_objects.update({response['grantId']: temp_grant_request})
                        if response['response']['responseCode'] == "0":
                            #Heartbeat all active grants
                            self.heartbeat_request_for_all_grants()

    def get_all_cbsd_object_with_atleast_one_grant(self):
        """

        :rtype: cbsd_objects
        """
        cbsd_objects = []
        for cbsd_id, cbsd_object in self.cbsd_objects.items():
            for grantId, grant_object in cbsd_object.grant_objects.items():
                if grant_object.get_grant_authorized_in_last_heartbeat():
                    cbsd_objects.append(cbsd_object)
        return cbsd_objects


class FullActivityDump:
    """
    A FAD  object has the following methods
        __init__:
            Parameters
                SAS certificate (to present when pulling)
                URL for SAS UUT/Test Harness
        initiate_full_activity_dump:
            Pulls FAD and all related files from SAS UUT
            Does light checking of response
            Logs all file data
            Aggregate CBSD objects into a single internal data structure
            On deletion, the downloaded files are deleted from disk.

    """
    cbsd_dump_data = []
    ppa_dump_data = []
    esc_sensor_dump_data = []

    def __init__(self, certificate, key, url):
        self.certificate = certificate
        self.key = key
        self.url = url
        self.sas_admin = sas.GetTestingSas()
        self.folder_name = "./FadContent/"

    def initiate_full_activity_dump(self):
        os.mkdir(self.folder_name)
        self.folder_name = "./FadContent/" + urllib.urlencode(self.url[8])
        # if the folder exist it will be removed
        os.removedirs(self.folder_name)
        os.mkdir(self.folder_name)
        response = self.sas_admin._SasRequest("GET", self.url, self.certificate, self.key)
        for dump_file in response['files']:
            self.sas_admin.assertContainsRequiredFields("ActivityDumpFile.schema.json", dump_file[0])
            if dump_file['recordType'] == 'cbsd':
                url = dump_file['url']
                lastpart = url.rsplit('/', 1)
                cbsd_file_content = self.sas_admin.DownloadFile(dump_file['url'])['recordData']
                filename = urllib.urlencode(lastpart)+"cbsd" + ".txt"
                file_obj = open(filename, "a+")
                file_obj.write(cbsd_file_content)
                self.cbsd_dump_data.append(cbsd_file_content)

            elif dump_file['recordType'] == 'esc_sensor':
                url = dump_file['url']
                lastpart = url.rsplit('/', 1)
                esc_file_content = self.sas_admin.DownloadFile(dump_file['url'])['recordData']
                filename = urllib.urlencode(lastpart)+"escSensor" + ".txt"
                file_obj = open(filename, "a+")
                file_obj.write(esc_file_content)
                self.cbsd_dump_data.append(esc_file_content)

            elif dump_file['recordType'] == 'zone':
                url = dump_file['url']
                lastpart = url.rsplit('/', 1)
                self.ppa_dump_data.append(self.sas_admin.DownloadFile(dump_file['url'])['recordData'])
                zone_file_content = self.sas_admin.DownloadFile(dump_file['url'])['recordData']
                filename = urllib.urlencode(lastpart)+"zone" + ".txt"
                file_obj = open(filename, "a+")
                file_obj.write(zone_file_content)
                self.cbsd_dump_data.append(zone_file_content)

    def get_cbsds(self):
        """

        :rtype: cbsd_dump_data
        """
        return self.cbsd_dump_data

    def __del__(self):
        os.removedirs(self.folder_name)
