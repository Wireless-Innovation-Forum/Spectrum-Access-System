# Copyright 2016 SAS Project Authors. All Rights Reserved.
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

# This file contains a mock SAS client. The commands available on the mock
# client allow the caller to issue particular commands to the server and
# inspect the results.

import json
import os
import requests
import urllib
import urllib3.contrib.pyopenssl

urllib3.contrib.pyopenssl.inject_into_urllib3()

class SASClient:

  def setup(self, sas_cbsd_server_url, sas_sas_server_url, cert):
    self.sas_cbsd_server = sas_cbsd_server_url
    self.sas_sas_server = sas_sas_server_url
    print('Using cert verification bundle at ' + cert)
    self.cert_path = cert

  def issueRequest(self, url, requestData):
    print('Issuing request to ' + url)
    headers = {'content-type': 'application/json'}
    try:
      response = requests.post(url, json.dumps(requestData), headers=headers, verify=self.cert_path)
      if response.status_code != 200:
        raise requests.ConnectionError('Bad HTTP status ' + str(response.status_code))
      if response.headers['content-type'] != 'application/json':
        raise requests.ConnectionError('Bad return type: ' + response.headers['content-type'])
      print('content = ' + response.content)
      return json.loads(response.content)
    except requests.ConnectionError as e:
      print('Connection error to SAS: ' + str(e))
      return {}

  def issueGet(self, url):
    print('Getting data from ' + url)
    headers = {'content-type': 'application/json'}
    try:
      response = requests.get(url, headers=headers, verify=self.cert_path)
      if response.status_code != 200:
        raise requests.ConnectionError('Bad HTTP status ' + str(response.status_code))
      if response.headers['content-type'] != 'application/json':
        raise requests.ConnectionError('Bad return type: ' + response.headers['content-type'])
      return json.loads(response.content)
    except requests.ConnectionError as e:
      print('Connection error to SAS: ' + str(e))
      return {}

  # SAS-CBSD methods
  def doRegistration(self, registrationRequest):
    url = self.sas_cbsd_server + '/registration'
    return self.issueRequest(url, registrationRequest)

  def doSpectrumInquiry(self, spectrumInquiryRequest):
    url = self.sas_cbsd_server + '/spectrumInquiry'
    return self.issueRequest(url, spectrumInquiryRequest)

  def doGrantRequest(self, grantRequest):
    url = self.sas_cbsd_server + '/grant'
    return self.issueRequest(url, grantRequest)

  def doHeartbeat(self, heartbeatRequest):
    url = self.sas_cbsd_server + '/heartbeat'
    return self.issueRequest(url, heartbeatRequest)

  def doRelinquish(self, relinquishmentRequest):
    url = self.sas_cbsd_server + '/relinquishment'
    return self.issueRequest(url, relinquishmentRequest)

  def doDeregistration(self, deregistrationRequest):
    url = self.sas_cbsd_server + '/deregistration'
    return self.issueRequest(url, deregistrationRequest)

  # SAS-SAS single-record retrieval methods
  def getSasAdmin(self, id):
    url = self.sas_sas_server + '/sas_admin/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getEscAdmin(self, id):
    url = self.sas_sas_server + '/esc_admin/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getSasImpl(self, id):
    url = self.sas_sas_server + '/sas/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getEscImpl(self, id):
    url = self.sas_sas_server + '/esc/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getCbsdType(self, id):
    url = self.sas_sas_server + '/cbsd_type/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getCbsd(self, id):
    url = self.sas_sas_server + '/cbsd/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getIncumbent(self, id):
    url = self.sas_sas_server + '/incumbent/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getZone(self, id):
    url = self.sas_sas_server + '/zone/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getOperator(self, id):
    url = self.sas_sas_server + '/operator/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getDomainProxy(self, id):
    url = self.sas_sas_server + '/domain/' + urllib.quote(id.encode('utf8'), safe='')
    return self.issueGet(url)

  def getDump(self):
    url = self.sas_sas_server + '/dump'
    return self.issueGet(url)

  # TODO: implement SAS-SAS multiple-record retrieval methods and notification methods.

dir = os.path.dirname(os.path.realpath(__file__))

c = SASClient()
c.setup('https://localhost:8008/cbsd/v1.0', 'https://localhost:8008/sas/v1.0',
        dir + '/server.crt')

# Some test fetches to illustrate behavior
# print(c.getDump())
# print(c.getCbsdType('aaa'))
# print(c.doGrantRequest({'a':'b'}))

