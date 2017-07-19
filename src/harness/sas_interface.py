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
"""SAS interfaces for testing."""

import abc


class SasInterface(object):
  """WinnForum standardized interfaces.

  Includes SAS-CBSD interface and (will include) SAS-SAS interface.

  """

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def Registration(self, request, ssl_cert=None, ssl_key=None):
    """SAS-CBSD Registration interface.

    Registers CBSDs.

    Request and response are both lists of dictionaries. Each dictionary
    contains all fields of a single request/response.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "registrationRequest" and the value is a list of individual CBSD
        registration requests (each of which is itself a dictionary).
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary with a single key-value pair where the key is
      "registrationResponse" and the value is a list of individual CBSD
      registration responses (each of which is itself a dictionary).
    """
    pass

  @abc.abstractmethod
  def SpectrumInquiry(self, request, ssl_cert=None, ssl_key=None):
    """SAS-CBSD SpectrumInquiry interface.

    Performs spectrum inquiry for CBSDs.

    Request and response are both lists of dictionaries. Each dictionary
    contains all fields of a single request/response.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "spectrumInquiryRequest" and the value is a list of individual CBSD
        spectrum inquiry requests (each of which is itself a dictionary).
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary with a single key-value pair where the key is
      "spectrumInquiryResponse" and the value is a list of individual CBSD
      spectrum inquiry responses (each of which is itself a dictionary).
    """
    pass

  @abc.abstractmethod
  def Grant(self, request, ssl_cert=None, ssl_key=None):
    """SAS-CBSD Grant interface.

    Request and response are both lists of dictionaries. Each dictionary
    contains all fields of a single request/response.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "grantRequest" and the value is a list of individual CBSD
        grant requests (each of which is itself a dictionary).
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary with a single key-value pair where the key is
      "grantResponse" and the value is a list of individual CBSD
      grant responses (each of which is itself a dictionary).
    """
    pass

  @abc.abstractmethod
  def Heartbeat(self, request, ssl_cert=None, ssl_key=None):
    """SAS-CBSD Heartbeat interface.

    Requests heartbeat for a grant for CBSDs.

    Request and response are both lists of dictionaries. Each dictionary
    contains all fields of a single request/response.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "heartbeatRequest" and the value is a list of individual CBSD
        heartbeat requests (each of which is itself a dictionary).
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary with a single key-value pair where the key is
      "heartbeatResponse" and the value is a list of individual CBSD
      heartbeat responses (each of which is itself a dictionary).
    """
    pass

  @abc.abstractmethod
  def Relinquishment(self, request, ssl_cert=None, ssl_key=None):
    """SAS-CBSD Relinquishment interface.

    Relinquishes grant for CBSDs.

    Request and response are both lists of dictionaries. Each dictionary
    contains all fields of a single request/response.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "relinquishmentRequest" and the value is a list of individual CBSD
        relinquishment requests (each of which is itself a dictionary).
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary with a single key-value pair where the key is
      "relinquishmentResponse" and the value is a list of individual CBSD
      relinquishment responses (each of which is itself a dictionary).
    """
    pass

  @abc.abstractmethod
  def Deregistration(self, request, ssl_cert=None, ssl_key=None):
    """SAS-CBSD Deregistration interface.

    Deregisters CBSDs.

    Request and response are both lists of dictionaries. Each dictionary
    contains all fields of a single request/response.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "deregistrationRequest" and the value is a list of individual CBSD
        deregistration requests (each of which is itself a dictionary).
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary with a single key-value pair where the key is
      "deregistrationResponse" and the value is a list of individual CBSD
      deregistration responses (each of which is itself a dictionary).
    """
    pass

  @abc.abstractmethod
  def GetSasImplementationRecord(self, request, ssl_cert=None, ssl_key=None):
    """SAS-SAS Implementation Record Exchange interface
    
    Requests a Pull Command to get the Sas Implementation Record
    
    Args:
      request: A string containing Sas Implementation Record Id
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary of Sas Implementation Message object specified in 
      WINNF-16-S-0096
    """
    pass

  @abc.abstractmethod
  def GetEscSensorRecord(self, request, ssl_cert=None, ssl_key=None):
    """SAS-SAS ESC Sensor Record Exchange interface

    Requests a Pull Command to get the ESC Sensor Data Message

    Args:
      request: A string containing Esc Sensor Record Id
      ssl_cert: Path to SSL cert file, if None, will use default cert file.
      ssl_key: Path to SSL key file, if None, will use default key file.
    Returns:
      A dictionary of Esc Sensor Data Message object specified in 
      WINNF-16-S-0096
    """
    pass


class SasAdminInterface(object):
  """Minimal test control interface for the SAS under test."""

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def Reset(self):
    """SAS admin interface to reset the SAS between test cases."""
    pass

  @abc.abstractmethod
  def InjectFccId(self, request):
    """SAS admin interface to inject fcc id information into SAS under test.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "fccId" and the value is a string of valid fccId which is going to be
        injected into SAS under test.
    """
    pass

  @abc.abstractmethod
  def BlacklistByFccId(self, request):
    """Inject an FCC ID which will be blacklisted by the SAS under test.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "fccId" and the value is the FCC ID (string) to be blacklisted.
    """
    pass

  @abc.abstractmethod
  def BlacklistByFccIdAndSerialNumber(self, request):
    """Inject an (FCC ID, serial number) pair which will be blacklisted by the
       SAS under test.

    Args:
      request: A dictionary with the following key-value pairs:
        "fccId": (string) blacklisted FCC ID
        "serialNumber": (string) blacklisted serial number
    """
    pass

  @abc.abstractmethod
  def PreloadRegistrationData(self, request):
    """SAS admin interface to preload registration data into SAS under test.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "registrationData" and the value is a list of individual CBSD
        registration data which need to be preloaded into SAS (each of which is
        itself a dictionary). The dictionary is a RegistrationRequest object,
        the fccId and cbsdSerialNumber fields are required, other fields are
        optional.
    """
    pass

  @abc.abstractmethod
  def InjectZoneData(self, request):
    """Inject PPA or NTIA zone information into SAS under test.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "record" and the value is ZoneData object to be injected into 
        SAS under test. For more information about ZoneData please see 
        the SAS-SAS TS (WINNF-16-S-0096).
    """
    pass

  @abc.abstractmethod
  def InjectClusterList(self, request):
    """"Associate a cluster list with an injected PPA.
    The SAS under test will act as if the specified CBSDs were used to create
    the PPA.

    Args:
      request: a dictionary with the following key-value pairs:
        "zoneId": (string) the ID of the PPA to which this cluster list should
        be added.
        "cbsdIds": (array of string) the CBSD IDs of the devices in the cluster
        list.
    """
    pass

  @abc.abstractmethod
  def InjectPalDatabaseRecord(self, request):
    """Inject a PAL Database record into the SAS under test.

    Args:
      request:
      For the contents of this request, please refer to the PAL Database TS
      (WINNF-16-S-0245).
    """
    pass

  @abc.abstractmethod
  def InjectFss(self, request):
    """SAS admin interface to inject FSS information into SAS under test.

    Args:
        request: A dictionary with a single key-value pair where the key is
        "record" and the value is a fixed satellite service object
        (which is itself a dictionary). The dictionary is an
        IncumbentProtectionData object (specified in SAS-SAS TS).
    """
    pass

  @abc.abstractmethod
  def InjectWisp(self, request):
    """SAS admin interface to inject WISP information into SAS under test.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "record" and the value is a wireless internet service provider
        object (which is itself a dictionary). The dictionary is an
        IncumbentProtectionData object (specified in SAS-SAS TS).
    Note: IncumbentProtectionData must include a zoneId which can be
    obtained by first injecting the WISP zone.
    """
    pass

  @abc.abstractmethod
  def InjectSasAdministratorRecord(self, request):
    """SAS admin interface to inject SAS Administrator Record into SAS under test.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "record" and the value is a SAS Administrator information (which is 
        itself a dictionary). The dictionary is an SASAdministrator object 
        (Specified in SAS-SAS TS WINNF-16-S-0096)
    """
    pass

  @abc.abstractmethod
  def InjectSasImplementationRecord(self, request):
    """SAS admin interface to inject SAS Implementation Record into SAS under test.

    Args:
      request: A dictionary with a single key-value pair where the key is "record" 
      and the value is a SasImplementation object (which is itself a dictionary 
      specified in the SAS-SAS TS, WINNF-16-S-0096).
    """
    pass

  @abc.abstractmethod
  def InjectEscSensorDataRecord(self, request):
    """SAS admin interface to inject ESC Sensor Data Record into SAS under test.

    Args:
      request: A dictionary with a single key-value pair where the key is
        "record" and the value is a EscSensorData object (which is 
        itself a dictionary specified in SAS-SAS TS WINNF-16-S-0096)
    Behavior: SAS should act as if it is connected to an ESC sensor with 
    the provided parameters.
    """
    pass

  @abc.abstractmethod
  def TriggerMeasurementReportRegistration(self, request):
    """SAS admin interface to trigger measurement report request for all subsequent
    registration request 
  
    Args:
      request: A dictionary with a single key-value pair where the key is
        "measReportConfig" and the value is an array of string of permitted 
        enumerations specified in WINNF-16-S-0016
    Note: The SAS should request a measurement report in the RegistrationResponse 
    (if status == 0)
    """
    pass

  @abc.abstractmethod
  def TriggerMeasurementReportHeartbeat(self, request):
    """SAS admin interface to trigger measurement report request for all subsequent
    heartbeat request 
  
    Args:
      request: A dictionary with a single key-value pair where the key is
        "measReportConfig" and the value is an array of string of permitted 
        enumerations specified in WINNF-16-S-0016
    Note: The SAS should request a measurement report in the HeartbeatResponse 
    (if status == 0)
    """
    pass


class SasTestcaseInterface(object):
  """Includes Helper Function interface for SAS-CBSD and SAS-SAS Testcases"""

  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def assertContainsRequiredFields(self, schema_filename, response):
    """Assertion of Required Fields in Response validating it with Schema

    Args:
      schema_filename: A string containing the filename of the schema to be used
      to validate. (The schema file should exist in /schema directory)
      response: A dictionary containing the response to validate for required
      fields using the schema.
    """
    pass

  @abc.abstractmethod
  def assertValidResponseFormatForApprovedGrant(self, grant_response):
    """Validate an approved grant response.

    Check presence and basic validity of each required field.
    Check basic validity of optional fields if they exist.
    Args:
      grant_response: A dictionary with a single grant response object from an
        array originally returned by a SAS server as specified in TS

    Returns:
      Nothing. It asserts if something about the response is broken/not per
      specs. Assumes it is dealing with an approved request.
    """
    pass
