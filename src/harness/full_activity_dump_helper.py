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
"""Container for Full Activity Dump information."""

from datetime import datetime
import logging
import signal
import time
from full_activity_dump import FullActivityDump
import util
import traceback


def getFullActivityDumpSasUut(sas, sas_admin, ssl_cert=None, ssl_key=None):
  """Returns a FullActivityDump object from the SAS UUT in its current state.

  Args:
    sas: SasInterface to request FAD data from.
    sas_admin: SasAdminInterface to trigger FAD creation over.
    ssl_cert: Optional. ssl certificate to use when making get/post requests.
    ssl_key: Optional. ssl key to use when making get/post requests.
  Returns:
    A Full Activity Dump object containing FAD data from the given SAS.
  """
  dump = _triggerFullActivityDumpAndWaitUntilComplete(sas, sas_admin, ssl_cert,
                                                      ssl_key)
  return _processDump(sas, dump, ssl_cert, ssl_key)


def getFullActivityDumpSasTestHarness(sas):
  """Returns a FullActivityDump object for the current state of a SAS test harness.

  Args:
    sas: SasInterface to request FAD data from.
  Returns:
    A Full Activity Dump object containing FAD data from the given SAS test
    harness.
  Raises:
    TestComponentError: Any failures will be caught and re-emitted as a
      TestComponentError. This signifies that a non-SAS UUT error occurred.
  """
  try:
    dump = sas.GetFullActivityDump()
    return _processDump(sas, dump)
  except Exception as e:
    # Any exception caused in reading and processing a FAD from a test
    # harness is not the fault of the SAS UUT.
    traceback.print_exc()
    raise util.TestComponentError('SAS Test Harness Failed')


def _triggerFullActivityDumpAndWaitUntilComplete(sas, sas_admin, ssl_cert,
                                                 ssl_key):
  """Triggers generation and loading of dump files from the SAS UUT.

  Will timeout and cause an exception after 7200 seconds (2 hours).

  Args:
    sas: The SAS to trigger FAD generation of and download the Full Activity
      Dump Message for.
    sas_admin: The SasAdminInterface to trigger Full Activity Dump generation
      on.
    ssl_cert: ssl certificate to use when making get requests.
    ssl_key: ssl key to use when making get requests.
  Returns:
    Dictionary containing the Full Activity Dump Message from the SAS.
  Raises:
    EnvironmentError: If the 7200 second timer is exceeded.
  """
  request_time = datetime.utcnow().replace(microsecond=0)
  sas_admin.TriggerFullActivityDump()
  signal.signal(signal.SIGALRM,
                lambda signum,
                frame: (_ for _ in ()).
                  throw(EnvironmentError('Full Activity Dump '
                                         'generation in SAS UUT timed out')))
  # Timeout after 2 hours if it's not completed.
  signal.alarm(7200)
  # Check generation date of full activity dump.
  while True:
    dump_message = sas.GetFullActivityDump(ssl_cert, ssl_key)
    dump_time = datetime.strptime(dump_message['generationDateTime'],
                                  '%Y-%m-%dT%H:%M:%SZ')
    if request_time <= dump_time:
      break
    time.sleep(10)
  signal.alarm(0)
  return dump_message


def _processDump(sas, dump, ssl_cert=None, ssl_key=None):
  """Clears any existing dump data and downloads current data.

  Args:
    sas: A SasInterface object to request
    dump: The https://base_url/version/dump message response, used to extract
      the files to be downloaded.
    ssl_cert: Optional. ssl certificate to use when making get requests.
    ssl_key: Optional. ssl key to use when making get requests.
  Returns:
    A Full Activity Dump with the FAD data from the given SAS as a dictionary
    with the fields: cbsd, esc_sensor, zone. Each field is a list of the
    recordType represented in dictionaries.
  Raises:
    AssertError: The FAD response does not match the expected schema or a
      request does not return 200.
  """
  util.assertContainsRequiredFields('FullActivityDump.schema.json', dump)
  dump_data = {'cbsd': [], 'esc_sensor': [], 'zone': []}
  for dump_file in dump['files']:
    if dump_file['recordType'] == 'coordination':
      logging.debug(
          'Coordination event record skipped in downloading Full Activity Dump')
      continue
    util.assertContainsRequiredFields('ActivityDumpFile.schema.json', dump_file)
    dump_data[dump_file['recordType']].extend(
        sas.DownloadFile(dump_file['url'], ssl_cert=ssl_cert,
                         ssl_key=ssl_key)['recordData'])
    logging.debug('%s record added to Full Activity Dump',
                  dump_file['recordType'])

  return FullActivityDump(dump_data)
