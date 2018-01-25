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
import security_testcase
from util import winnforum_testcase
import json
import os
import sas
import urllib

class Grant:

    '''
	A Grant object has the following methods
	Initialize
   	   Parameters: grant ID, grant request
	Methods
	Retrieve internal information
	    grant ID,
	    grant request
	Retrieve operating params
	Construct heartbeat request
	Update “was authorized in last heartbeat? state

    '''

    def __init__(self,grantId,grantRequest):
        self.GrantId = grantId
        self.GrantRequest = grantRequest
        self.IsGrantAuthorisedInlastHeartbeat = False

    def GetGrantId(self):
        return self.GrantId

    def GetGrantRequest(self):
        return self.GrantRequest

    def GetRequestOperationParam(self):
        return self.GrantRequest['operationParam']

    def ConstructHeartBeatRequest(self):

        hearbeatRequest =  {
        "cbsdId": self.GrantRequest['cbsdId'],
        'grantId': self.GrantId,
        'operationState': "GRANTED"
        }
        return hearbeatRequest

    def UpdateGrantAuthorisedInlastHeartbeat(self,IsAuthorized):
        IsGrantAuthorisedInlastHeartbeat = IsAuthorized

class Cbsd:

    '''
	A CBSD object has the following methods…
		Initialize
			Parameters: CBSD ID, successful registration request, grant ID, successful grant request

		Retrieve internal information for below
		    CBSD ID,
		    successful registration request,
		    grant ID, successful
		    grant request
		Does this CBSD have at least one active grant?
		Construct heartbeat request for all active grants
		Return operating params for all grants wh{"grantId":"grantRequest"}ich are authorized to transmit
    '''
    def __init_(self,cbsdId,successfulRegRequest,grantId,granRequests):
        self.CbsdId = cbsdId
        self.GrantObjects = {"":Grant}
        for index,obj in enumerate(granRequests):
            self.GrantObjects[grantId[index]] = granRequests[index]
        self.SuccessfulRegRequest = successfulRegRequest

    def GetCbsdId(self):
        return self.CbsdId

    def GetGrantRequest(self,grantId):
        return self.GrantObjects[grantId]

    def GetRegistrationRequest(self,grantId):
        return self.SuccessfulRegRequest

    def IsCbsdIdhasAtleastOneGrant(self):
        for grantId,grantRequest in self.GrantObjects.items():
            if grantRequest['operationState'] == "GRANTED":
                return True
        return False

    def ConstructSingleHeartBeatRequest(self,cbsdId,grantId):
         hearbeatRequest = {
         "cbsdId": cbsdId,
         "grantId": grantId,
         "operationState": "GRANTED"}
         return hearbeatRequest

    def ConstructHeartBeatRequestForAllActiveGrant(self):
        heartBeatRequests = ""
        for grantId,grantRequest in self.GrantObjects.items():
             heartbeatRequest = self.ConstructSingleHeartBeatRequest(self.CbsdId,grantId)
             heartBeatRequests +=heartbeatRequest
        return heartBeatRequests

    def GetAllOperatingParamsofGrantRequest(self):
        OperationParams = []
        for grantId,granObject in self.GrantObjects.items():
            if granObject.IsGrantAuthorisedInlastHeartbeat:
             OperationParam = granObject['operationParam']
             OperationParams.insert(OperationParam)
        return OperationParams

class DomainProxyObject:

    '''
	A DP object has the following methods
		Initialize
				Parameters: certificate, N registration requests, N grant requests
				Send N registration requests, expect success for all
			    Send N grant requests, allow failure
		Behavior:
		Make one CBSD object per successful grant request
		Retrieve CBSD object with CBSD ID = C
		Heartbeat all CBSDs/Grants (and update internal state)
		Heartbeat/relinquish/grant/heartbeat request for all CBSDs (and update internal state)
			Heartbeat on all active grants (allow all failures)
			If any HBs contain suggested operating params, relinquish the corresponding grant
			For all grants in the previous step, request a new grant with the suggested operating parameters (allow failure)
			Heartbeat all active grants (allow all failures)
		Retrieve all CBSD objects with at least one grant which is authorized to transmit


    '''
    DpCertificate = " "
    DpKey = " "
    CbsdObjects = {"":Cbsd}

    def __init__(self,certificate,key,registrationRequests,grantRequests):
        if len(registrationRequests)!= len(grantRequests):
            return
        self.DpCertificate = certificate
        self.DpKey = key
        cbsdId = []
        for registerRequest in registrationRequests[:]:
            response = self._sas.Registration(registerRequest,self.DpCertificate,self.DpKey)['registrationResponse'][0]
            cbsdId.insert(response['cbsdId'])
            self.assertEqual(response['response']['responseCode'], 0)
         # here the registrationRequest & grant request has 1to1 mapping
         # The variable index used as subscript of registration request while looping through grant requests
        for index,grantRequest in enumerate(grantRequests[:]):
            grantRequest['cbsdId'] = cbsdId[index]
            response = self._sas.Grant(grantRequest,self.DpCertificate,self.DpKey)['grantResponse'][0]
            if response['response']['responseCode'] == "0":
                cbsdobject = Cbsd(cbsdId[index],registrationRequests[index],response['grantId'],grantRequest)
                self.CbsdObjects[response['cbsdId']] = cbsdobject

    def GetCbsdObject(self,cbsdId):
        return self.CbsdObjects[cbsdId]

    def HeartBeatRequestForAllGrants(self):
        for cbsdId, cbsdObjectItem in self.CbsdObjects.items():
            for grantId, grantObject in cbsdObjectItem.GrantObjects.items():
                heartbeatRequests = cbsdObjectItem.ConstructHeartBeatRequestForAllActiveGrant()
                hbResponses = self._sas.Heartbeat(heartbeatRequests)['heartbeatResponse'][0]
                for hbReponse in hbResponses:
                    grantobject = cbsdObjectItem.GrantObjects[hbReponse['grantId']]
                    if hbReponse['response']['responseCode'] == "0":
                        grantobject.UpdateGrantAuthorisedInlastHeartbeat(True)
                    else:
                        grantobject.UpdateGrantAuthorisedInlastHeartbeat(False)

    #TODO self review is in progress for this function
    def HeartBeatRequestForAllGrantAndUpdateGrants(self):
        for cbsdId, cbsdObjectItem in self.CbsdObjects.items():
            for grantId, grantObject in cbsdObjectItem.GrantObjects.items():
                relinquishhbResponses = {}
                #Heartbeat on all active grants
                heartbeatRequests = cbsdObjectItem.ConstructHeartBeatRequestForAllActiveGrant()
                hbResponses = self._sas.Heartbeat(heartbeatRequests)['heartbeatResponse'][0]
                for hbReponse in hbResponses:
                    grantobject = cbsdObjectItem.GrantObjects[hbReponse['grantId']]
                    if hbReponse['response']['responseCode'] == "0":
                        grantobject.UpdateGrantAuthorisedInlastHeartbeat(True)
                    else:
                        grantobject.UpdateGrantAuthorisedInlastHeartbeat(False)
                        #	If any HBs contain suggested operating params, relinquish the corresponding grant
                        if 'operationParam' in hbReponse:
                            RelinquishRequest = {
                                'relinquishmentRequest': [{
                                    'cbsdId': hbReponse['cbsdId'],
                                    'grantId': hbReponse['grantId']
                                }]
                            }
                            self._sas.Relinquishment(RelinquishRequest, self.DpCertificate, self.DpKey)
                            relinquishhbResponses[hbReponse['cbsdId']] = hbReponse
                            del cbsdObjectItem.grantObjects[grantId]
                for cbsdId,hbresponse in relinquishhbResponses.items():
                        grant_0 = json.load(
                            open(os.path.join('testcases', 'testdata', 'grant_0.json')))
                        grant_0['cbsdId'] = cbsdId
                        grant_0['operationParam']['maxEirp'] = hbresponse['operationParam']['maxEirp']
                        grant_0['operationParam']['operationFrequencyRange']['lowFrequency'] = \
                            hbresponse['operationParam']['operationFrequencyRange']['lowFrequency']
                        grant_0['operationParam']['operationFrequencyRange']['highFrequency'] = \
                            hbresponse['operationParam']['operationFrequencyRange']['highFrequency']
                        tempGrantRequest = {'grantRequest': [grant_0]}
                        response = self._sas.Grant(tempGrantRequest,self.DpCertificate,self.DpKey)['grantResponse'][0]
                        self.CbsdObjects.GrantObjects[response['grantId']] = tempGrantRequest
                        if response['response']['responseCode'] == "0":
                            self.CbsdObject.HeartBeatRequestForAllGrants()

    def GetAllCbsdObjectwithAtleastOneGrant(self):
        cbsdObjects = []
        for cbsdId, CbsdObject in self.CbsdObjects.items():
            for grantId, grantObject in CbsdObject.GrantObjects.items():
                if grantObject['operationState'] == "GRANTED":
                    cbsdObjects.insert(CbsdObject)
        return cbsdObjects



class FullActivityDumpObject:
    '''
	A FAD  object has the following methods
		Initialize:
			Parameters
				SAS certificate (to present when pulling)
				URL for SAS UUT/Test Harness
		Behavior:
			Pulls FAD and all related files from SAS UUT
			Does light checking of response
			Logs all file data
			Aggregate CBSD objects into a single internal data structure
			Data retrieval methods (TBD)
			On deletion, the downloaded files are deleted from disk.

    '''
    cbsd_dump_data = []
    ppa_dump_data = []
    esc_sensor_dump_data = []
    def Initialize(self, certificate,key, url):
        self.folderName = "./FadContent/"
        os.mkdir(self.folderName)
        self.folderName = "./FadContent/" + urllib.urlencode(url[8])
        os.mkdir(self.folderName)
        response = self._sas._SasRequest("GET",url,certificate,key)
        for dumpFile in response['files']:
            sas.assertContainsRequiredFields("ActivityDumpFile.schema.json",dumpFile[0])
            if dumpFile['recordType'] ==  'cbsd':
                url = dumpFile['url']
                lastpart = url.rsplit('/', 1)
                cbsdFileContent = self._sas.DownloadFile(dumpFile['url'])['recordData']
                filename = urllib.urlencode(lastpart)+"cbsd" + ".txt"
                fileObj = open(filename, "w+")
                fileObj.write(cbsdFileContent)
                self.cbsd_dump_data.append(cbsdFileContent)

            elif dumpFile['recordType'] ==  'esc_sensor':
                url = dumpFile['url']
                lastpart = url.rsplit('/', 1)
                escFileContent = self._sas.DownloadFile(dumpFile['url'])['recordData']
                filename = urllib.urlencode(lastpart)+"escSensor" + ".txt"
                fileObj = open(filename, "a+")
                fileObj.write(escFileContent)
                self.cbsd_dump_data.append(escFileContent)

            elif dumpFile['recordType'] ==  'zone':
                url = dumpFile['url']
                lastpart = url.rsplit('/', 1)
                self.ppa_dump_data.append(self._sas.DownloadFile(dumpFile['url'])['recordData'])
                zoneFileContent = self._sas.DownloadFile(dumpFile['url'])['recordData']
                filename = urllib.urlencode(lastpart)+"zone" + ".txt"
                fileObj = open(filename, "a+")
                fileObj.write(zoneFileContent)
                self.cbsd_dump_data.append(zoneFileContent)

    def getCbsds(self):
        return self.cbsd_dump_data
    def __del__(self):
        os.removedirs(self.folderName)







