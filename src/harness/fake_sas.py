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


# Some parts of this software was developed by employees of 
# the National Institute of Standards and Technology (NIST), 
# an agency of the Federal Government. 
# Pursuant to title 17 United States Code Section 105, works of NIST employees 
# are not subject to copyright protection in the United States and are 
# considered to be in the public domain. Permission to freely use, copy, 
# modify, and distribute this software and its documentation without fee 
# is hereby granted, provided that this notice and disclaimer of warranty 
# appears in all copies.

# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER 
# EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY
# THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM 
# INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE 
# SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE. IN NO EVENT
# SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT, 
# INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM, 
# OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON 
# WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED
# BY PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED
# FROM, OR AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES 
# PROVIDED HEREUNDER.

# Distributions of NIST software should also include copyright and licensing 
# statements of any third-party software that are legally bundled with the 
# code in compliance with the conditions of those licenses.

"""A fake implementation of SasInterface, based on v1.0 of the SAS-CBSD TS.

A local test server could be run by using "python fake_sas.py".

"""

import argparse
from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import ConfigParser
from datetime import datetime
from datetime import timedelta
from testcases.WINNF_FT_S_PAT_testcase import computePropagationAntennaModel
import uuid
import json
import ssl
import os
import sas_interface

# Fake SAS server configurations.
PORT = 9000
CERT_FILE = 'certs/server.cert'
KEY_FILE = 'certs/server.key'
CA_CERT = 'certs/ca.cert'
CIPHERS = [
    'AES128-GCM-SHA256',              # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',              # TLS_RSA_WITH_AES_256_GCM_SHA384
    'ECDHE-RSA-AES128-GCM-SHA256',    # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
]
ECC_CERT_FILE = 'certs/server-ecc.cert'
ECC_KEY_FILE = 'certs/server-ecc.key'
ECC_CIPHERS = [
    'ECDHE-ECDSA-AES128-GCM-SHA256',  # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',  # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
]

MISSING_PARAM = 102
INVALID_PARAM = 103


class FakeSas(sas_interface.SasInterface):
  """A fake implementation of SasInterface.

  Returns success for all requests with plausible fake values for all required
  response fields.

  """

  def __init__(self):
    pass

  def Registration(self, request, ssl_cert=None, ssl_key=None):
    response = {'registrationResponse': []}
    for req in request['registrationRequest']:
      if 'fccId' not in req or 'cbsdSerialNumber' not in req:
        response['registrationResponse'].append({
            'response': self._GetSuccessResponse()
        })
        continue
      response['registrationResponse'].append({
        'cbsdId': req['fccId'] + '/' + req['cbsdSerialNumber'],
        'response': self._GetSuccessResponse()
    })
    return response

  def SpectrumInquiry(self, request, ssl_cert=None, ssl_key=None):
    response = {'spectrumInquiryResponse': []}
    for req in request['spectrumInquiryRequest']:
      response['spectrumInquiryResponse'].append({
          'cbsdId': req['cbsdId'],
          'availableChannel': {
              'frequencyRange': {
                  'lowFrequency': 3620000000,
                  'highFrequency': 3630000000
              },
              'channelType': 'GAA',
              'ruleApplied': 'FCC_PART_96'
          },
          'response': self._GetSuccessResponse()
      })
    return response

  def Grant(self, request, ssl_cert=None, ssl_key=None):
    response = {'grantResponse': []}
    for req in request['grantRequest']:
      if ('cbsdId' not in req) :
        response['grantResponse'].append({
          'response': self._GetMissingParamResponse()
        })
      else :
        if (('highFrequency' not in req['operationParam']['operationFrequencyRange']) or \
           ('lowFrequency' not in req['operationParam']['operationFrequencyRange'])) :
           response['grantResponse'].append({
             'cbsdId': req['cbsdId'],
             'response': self._GetMissingParamResponse()
           })
        else:   
          response['grantResponse'].append({
            'cbsdId': req['cbsdId'],
            'grantId': 'fake_grant_id_%s' % datetime.utcnow().isoformat(),
            'channelType': 'GAA',
            'response': self._GetSuccessResponse()
          })
    return response

  def Heartbeat(self, request, ssl_cert=None, ssl_key=None):
    response = {'heartbeatResponse': []}
    for req in request['heartbeatRequest']:
      transmit_expire_time = datetime.utcnow().replace(
          microsecond=0) + timedelta(minutes=1)
      response['heartbeatResponse'].append({
          'cbsdId': req['cbsdId'],
          'grantId': req['grantId'],
          'transmitExpireTime': transmit_expire_time.isoformat() + 'Z',
          'response': self._GetSuccessResponse()
      })
    return response

  def Relinquishment(self, request, ssl_cert=None, ssl_key=None):
    response = {'relinquishmentResponse': []}
    for req in request['relinquishmentRequest']:
      response['relinquishmentResponse'].append({
          'cbsdId': req['cbsdId'],
          'grantId': req['grantId'],
          'response': self._GetSuccessResponse()
      })
    return response

  def Deregistration(self, request, ssl_cert=None, ssl_key=None):
    response = {'deregistrationResponse': []}
    for req in request['deregistrationRequest']:
      if ('cbsdId' not in req) :
        response['deregistrationResponse'].append({
          'response': self._GetMissingParamResponse()
        })
      else :
        response['deregistrationResponse'].append({
          'cbsdId': req['cbsdId'],
          'response': self._GetSuccessResponse()
        })
    return response

  def GetSasImplementationRecord(self, request, ssl_cert=None, ssl_key=None):
    # Get the Sas implementation record
    impl_record = json.load(
      open(os.path.join('testcases', 'testdata', 'impl_record_0.json')))
    if request == impl_record['id']:
      return impl_record
    else:
      # Return Empty if invalid Id
      return {}

  def GetEscSensorRecord(self, request, ssl_cert=None, ssl_key=None):
    # Get the Esc Sensor record
    esc_sensor_record = json.load(
      open(os.path.join('testcases', 'testdata', 'esc_sensor_record_0.json')))
    if request == esc_sensor_record['id']:
      return esc_sensor_record
    else:
      # Return Empty if invalid Id
      return {}

  def _GetSuccessResponse(self):
    return {'responseCode': 0}

  def _GetMissingParamResponse(self):
    return {'responseCode': MISSING_PARAM}


class FakeSasAdmin(sas_interface.SasAdminInterface):
  """Implementation of SAS Admin for Fake SAS."""

  def Reset(self):
    pass

  def InjectFccId(self, request):
    pass

  def InjectUserId(self, request):
    pass

  def BlacklistByFccId(self, request):
    pass

  def BlacklistByFccIdAndSerialNumber(self, request):
    pass

  def PreloadRegistrationData(self, request):
    pass

  def InjectZoneData(self, request, ssl_cert=None, ssl_key=None):
    return request['record']['id']

  def InjectPalDatabaseRecord(self, request):
    pass

  def InjectFss(self, request):
    pass

  def InjectWisp(self, request):
    pass

  def InjectSasAdministratorRecord(self, request):
    pass

  def InjectSasImplementationRecord(self, request):
    pass

  def InjectEscSensorDataRecord(self, request):
    pass

  def TriggerMeasurementReportRegistration(self):
    pass

  def TriggerMeasurementReportHeartbeat(self):
    pass

  def TriggerPpaCreation(self, request, ssl_cert=None, ssl_key=None):
    return 'zone/ppa/fake_sas/%s/%s' % (request['palIds'][0]['palId'],
                                        uuid.uuid4().hex)

  def TriggerDailyActivitiesImmediately(self):
    pass

  def QueryPropagationAndAntennaModel(self, request):
    return computePropagationAntennaModel(request)
	
  def GetDailyActivitiesStatus(self):
    return {'completed': True}

  def TriggerLoadDpas(self):  
    pass

  def TriggerBulkDpaActivation(self, request):
    pass

  def TriggerDpaActivation(self, request):
    pass 

  def TriggerDpaDeactivation(self, request):
    pass

class FakeSasHandler(BaseHTTPRequestHandler):
  @classmethod
  def SetVersion(cls, version):
    cls.version = version

  def _parseUrl(self, url):
    """Parse the Url into the path and value."""
    splitted_url = url.split('/')[1:]
    # Returns path and value
    return '/'.join(splitted_url[0:2]), '/'.join(splitted_url[2:])

  def do_POST(self):
    """Handles POST requests."""

    length = int(self.headers.getheader('content-length'))
    if length > 0:
      request = json.loads(self.rfile.read(length))
    if self.path == '/%s/registration' % self.version:
      response = FakeSas().Registration(request)
    elif self.path == '/%s/spectrumInquiry' % self.version:
      response = FakeSas().SpectrumInquiry(request)
    elif self.path == '/%s/grant' % self.version:
      response = FakeSas().Grant(request)
    elif self.path == '/%s/heartbeat' % self.version:
      response = FakeSas().Heartbeat(request)
    elif self.path == '/%s/relinquishment' % self.version:
      response = FakeSas().Relinquishment(request)
    elif self.path == '/%s/deregistration' % self.version:
      response = FakeSas().Deregistration(request)
    elif self.path == '/admin/injectdata/zone':
      response = FakeSasAdmin().InjectZoneData(request)
    elif self.path == 'admin/trigger/create_ppa':
      response = FakeSasAdmin().TriggerPpaCreation(request)
    elif self.path == 'admin/get_daily_activities_status':
      response = FakeSasAdmin().GetDailyActivitiesStatus()
    elif self.path == '/admin/query/propagation_and_antenna_model':
      try:
          response = FakeSasAdmin().QueryPropagationAndAntennaModel(request)
      except ValueError:
          self.send_response(400)
          return 	  
    elif self.path in ('/admin/reset', '/admin/injectdata/fcc_id',
                       '/admin/injectdata/user_id',
                       '/admin/injectdata/conditional_registration',
                       '/admin/injectdata/blacklist_fcc_id',
                       '/admin/injectdata/blacklist_fcc_id_and_serial_number',
                       '/admin/injectdata/fss', '/admin/injectdata/wisp',
                       '/admin/injectdata/cluster_list',
                       '/admin/injectdata/pal_database_record',
                       '/admin/injectdata/sas_admin',
                       '/admin/injectdata/sas_impl',
                       '/admin/injectdata/esc_sensor',
                       '/admin/injectdata/cpi_user',
                       '/admin/trigger/meas_report_in_registration_response',
                       '/admin/trigger/meas_report_in_heartbeat_response',
                       '/admin/trigger/daily_activities_immediately',
                       '/admin/trigger/load_dpas',
                       '/admin/trigger/dpa_activation',
                       '/admin/trigger/dpa_deactivation',
                       '/admin/trigger/bulk_dpa_activation'):
      response = ''
    else:
      self.send_response(404)
      return
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(response))

  def do_GET(self):
    """Handles GET requests."""
    path, value = self._parseUrl(self.path)
    if path == '%s/sas_impl' % self.version:
     response = FakeSas().GetSasImplementationRecord(value)
    elif path == '%s/esc_sensor' % self.version:
      response = FakeSas().GetEscSensorRecord(value)
    else:
      self.send_response(404)
      return
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()
    self.wfile.write(json.dumps(response))


def RunFakeServer(version, is_ecc):
  FakeSasHandler.SetVersion(version)
  if is_ecc:
    assert ssl.HAS_ECDH
  server = HTTPServer(('localhost', PORT), FakeSasHandler)

  server.socket = ssl.wrap_socket(
      server.socket,
      certfile=ECC_CERT_FILE if is_ecc else CERT_FILE,
      keyfile=ECC_KEY_FILE if is_ecc else KEY_FILE,
      ca_certs=CA_CERT ,
      cert_reqs=ssl.CERT_REQUIRED,  # CERT_NONE to disable client certificate check
      ssl_version=ssl.PROTOCOL_TLSv1_2,
      ciphers=':'.join(ECC_CIPHERS if is_ecc else CIPHERS),
      server_side=True)
  print 'Will start server at localhost:%d, use <Ctrl-C> to stop.' % PORT
  server.serve_forever()


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--ecc', help='Use ECDSA certificate', action='store_true')
  args = parser.parse_args()

  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(['sas.cfg'])
  version = config_parser.get('SasConfig', 'Version')
  RunFakeServer(version, args.ecc)


