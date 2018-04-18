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
"""Implementation of SasInterface."""

import ConfigParser
from request_handler import TlsConfig, RequestPost, RequestGet
import os
import sas_interface

def GetTestingSas():
  config_parser = ConfigParser.RawConfigParser()
  config_parser.read(['sas.cfg'])
  admin_api_base_url = config_parser.get('SasConfig', 'AdminApiBaseUrl')
  cbsd_sas_rsa_base_url = config_parser.get('SasConfig', 'CbsdSasRsaBaseUrl')
  cbsd_sas_ec_base_url = config_parser.get('SasConfig', 'CbsdSasEcBaseUrl')
  sas_sas_rsa_base_url = config_parser.get('SasConfig', 'SasSasRsaBaseUrl')
  sas_sas_ec_base_url = config_parser.get('SasConfig', 'SasSasEcBaseUrl')
  cbsd_sas_version = config_parser.get('SasConfig', 'CbsdSasVersion')
  sas_sas_version = config_parser.get('SasConfig', 'SasSasVersion')
  return SasImpl(cbsd_sas_rsa_base_url, cbsd_sas_ec_base_url, sas_sas_rsa_base_url,\
    sas_sas_ec_base_url, cbsd_sas_version, sas_sas_version), SasAdminImpl(admin_api_base_url)

class SasImpl(sas_interface.SasInterface):
  """Implementation of SasInterface for SAS certification testing."""

  def __init__(self, cbsd_sas_rsa_base_url, cbsd_sas_ec_base_url,\
    sas_sas_rsa_base_url, sas_sas_ec_base_url, cbsd_sas_version, sas_sas_version):
    self._cbsd_sas_rsa_base_url = cbsd_sas_rsa_base_url
    self._cbsd_sas_ec_base_url = cbsd_sas_ec_base_url
    self._sas_sas_rsa_base_url = sas_sas_rsa_base_url
    self._sas_sas_ec_base_url = sas_sas_ec_base_url
    self.cbsd_sas_active_base_url = cbsd_sas_rsa_base_url
    self.sas_sas_active_base_url = sas_sas_rsa_base_url
    self.cbsd_sas_version = cbsd_sas_version
    self.sas_sas_version = sas_sas_version
    self._tls_config = TlsConfig()

  def Registration(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('registration', request, ssl_cert, ssl_key)

  def SpectrumInquiry(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('spectrumInquiry', request, ssl_cert, ssl_key)

  def Grant(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('grant', request, ssl_cert, ssl_key)

  def Heartbeat(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('heartbeat', request, ssl_cert, ssl_key)

  def Relinquishment(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('relinquishment', request, ssl_cert, ssl_key)

  def Deregistration(self, request, ssl_cert=None, ssl_key=None):
    return self._CbsdRequest('deregistration', request, ssl_cert, ssl_key)

  def GetEscSensorRecord(self, request, ssl_cert=None, ssl_key=None):
    return self._SasRequest('esc_sensor', request, ssl_cert, ssl_key)

  def GetFullActivityDump(self, ssl_cert=None, ssl_key=None):
    return self._SasRequest('dump', None, ssl_cert, ssl_key)

  def _SasRequest(self, method_name, request, ssl_cert=None, ssl_key=None):

    url = 'https://%s/%s/%s' % (self.sas_sas_active_base_url, self.sas_sas_version, method_name)
    if request is not None:
      url += '/%s' % request
    return RequestGet(url,
                      self._tls_config.WithClientCertificate(
                          ssl_cert or self._GetDefaultSasSSLCertPath(),
                          ssl_key or self._GetDefaultSasSSLKeyPath()))

  def _CbsdRequest(self, method_name, request, ssl_cert=None, ssl_key=None):
    return RequestPost('https://%s/%s/%s' % (self.cbsd_sas_active_base_url, self.cbsd_sas_version,
                                             method_name), request,
                       self._tls_config.WithClientCertificate(
                           ssl_cert or self._GetDefaultCbsdSSLCertPath(),
                           ssl_key or self._GetDefaultCbsdSSLKeyPath()))

  def DownloadFile(self, url, ssl_cert=None, ssl_key=None):
    return RequestGet(url,
                      self._tls_config.WithClientCertificate(
                          ssl_cert if ssl_cert else
                          self._GetDefaultSasSSLCertPath(), ssl_key
                          if ssl_key else self._GetDefaultSasSSLKeyPath()))

  def UpdateSasRequestUrl(self, cipher):
    if 'ECDSA' in cipher:
      sas_sas_active_base_url = self._sas_sas_ec_base_url
    else:
      sas_sas_active_base_url = self._sas_sas_rsa_base_url

  def UpdateCbsdRequestUrl(self, cipher):
    if 'ECDSA' in cipher:
      self.cbsd_sas_active_base_url = self._cbsd_sas_ec_base_url
    else:
      self.cbsd_sas_active_base_url = self._cbsd_sas_rsa_base_url

  def _GetDefaultCbsdSSLCertPath(self):
    return os.path.join('certs', 'client.cert')

  def _GetDefaultCbsdSSLKeyPath(self):
    return os.path.join('certs', 'client.key')

  def _GetDefaultSasSSLCertPath(self):
    return os.path.join('certs', 'client.cert')

  def _GetDefaultSasSSLKeyPath(self):
    return os.path.join('certs', 'client.key')

class SasAdminImpl(sas_interface.SasAdminInterface):
  """Implementation of SasAdminInterface for SAS certification testing."""

  def __init__(self, base_url):
    self._base_url = base_url
    self._tls_config = TlsConfig().WithClientCertificate(
        self._GetDefaultAdminSSLCertPath(), self._GetDefaultAdminSSLKeyPath())

  def Reset(self):
    RequestPost('https://%s/admin/reset' % self._base_url, None,
                self._tls_config)

  def InjectFccId(self, request):
    if 'fccMaxEirp' not in request:
      request['fccMaxEirp'] = 47
    RequestPost('https://%s/admin/injectdata/fcc_id' % self._base_url, request,
                self._tls_config)

  def InjectUserId(self, request):
    RequestPost('https://%s/admin/injectdata/user_id' % self._base_url, request,
                self._tls_config)

  def InjectEscZone(self, request):
    return RequestPost('https://%s/admin/injectdata/esc_zone' % self._base_url,
                       request, self._tls_config)

  def InjectExclusionZone(self, request):
    return RequestPost(
        'https://%s/admin/injectdata/exclusion_zone' % self._base_url, request,
        self._tls_config)

  def InjectZoneData(self, request):
    return RequestPost('https://%s/admin/injectdata/zone' % self._base_url,
                       request, self._tls_config)

  def InjectPalDatabaseRecord(self, request):
    RequestPost(
        'https://%s/admin/injectdata/pal_database_record' % self._base_url,
        request, self._tls_config)

  def InjectClusterList(self, request):
    RequestPost('https://%s/admin/injectdata/cluster_list' % self._base_url,
                request, self._tls_config)

  def BlacklistByFccId(self, request):
    RequestPost('https://%s/admin/injectdata/blacklist_fcc_id' % self._base_url,
                request, self._tls_config)

  def BlacklistByFccIdAndSerialNumber(self, request):
    RequestPost('https://%s/admin/injectdata/blacklist_fcc_id_and_serial_number'
                % self._base_url, request, self._tls_config)

  def TriggerEscZone(self, request):
    RequestPost('https://%s/admin/trigger/esc_detection' % self._base_url,
                request, self._tls_config)

  def ResetEscZone(self, request):
    RequestPost('https://%s/admin/trigger/esc_reset' % self._base_url, request,
                self._tls_config)

  def PreloadRegistrationData(self, request):
    RequestPost(
        'https://%s/admin/injectdata/conditional_registration' % self._base_url,
        request, self._tls_config)

  def InjectFss(self, request):
    RequestPost('https://%s/admin/injectdata/fss' % self._base_url, request,
                self._tls_config)

  def InjectWisp(self, request):
    RequestPost('https://%s/admin/injectdata/wisp' % self._base_url, request,
                self._tls_config)

  def InjectSasAdministratorRecord(self, request):
    RequestPost('https://%s/admin/injectdata/sas_admin' % self._base_url,
                request, self._tls_config)

  def TriggerMeasurementReportRegistration(self):
    RequestPost('https://%s/admin/trigger/meas_report_in_registration_response'
                % self._base_url, None, self._tls_config)

  def TriggerMeasurementReportHeartbeat(self):
    RequestPost('https://%s/admin/trigger/meas_report_in_heartbeat_response' %
                self._base_url, None, self._tls_config)

  def InjectEscSensorDataRecord(self, request):
    RequestPost('https://%s/admin/injectdata/esc_sensor' % self._base_url,
                request, self._tls_config)

  def TriggerPpaCreation(self, request):
    return RequestPost('https://%s/admin/trigger/create_ppa' % self._base_url,
                       request, self._tls_config)

  def TriggerDailyActivitiesImmediately(self):
    RequestPost('https://%s/admin/trigger/daily_activities_immediately' %
                self._base_url, None, self._tls_config)

  def QueryPropagationAndAntennaModel(self, request):
    return RequestPost('https://%s/admin/query/propagation_and_antenna_model' %
                 self._base_url, request, self._tls_config)

  def GetDailyActivitiesStatus(self):
    return RequestPost(
        'https://%s/admin/get_daily_activities_status' % self._base_url, None,
        self._tls_config)

  def InjectCpiUser(self, request):
    RequestPost('https://%s/admin/injectdata/cpi_user' % self._base_url,
                request, self._tls_config)

  def TriggerLoadDpas(self):
    RequestPost('https://%s/admin/trigger/load_dpas' % self._base_url, None,
                self._tls_config)

  def TriggerBulkDpaActivation(self, request):
    RequestPost('https://%s/admin/trigger/bulk_dpa_activation' % self._base_url,
                request, self._tls_config)

  def TriggerDpaActivation(self, request):
    RequestPost('https://%s/admin/trigger/dpa_activation' % self._base_url,
                request, self._tls_config)

  def TriggerDpaDeactivation(self, request):
    RequestPost('https://%s/admin/trigger/dpa_deactivation' % self._base_url,
                request, self._tls_config)

  def TriggerFullActivityDump(self):
    RequestPost(
        'https://%s/admin/trigger/create_full_activity_dump' % self._base_url,
        None, self._tls_config)

  def _GetDefaultAdminSSLCertPath(self):
    return os.path.join('certs', 'admin_client.cert')

  def _GetDefaultAdminSSLKeyPath(self):
    return os.path.join('certs', 'admin_client.key')

  def InjectPeerSas(self, request):
    RequestPost('https://%s/admin/injectdata/peer_sas' % self._base_url,
                request, self._tls_config)
