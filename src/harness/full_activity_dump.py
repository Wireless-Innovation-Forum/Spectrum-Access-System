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


class FullActivityDump(object):

  _valid_field_names = ['cbsd', 'esc_sensor', 'zone']

  def __init__(self, dump):
    """Initializes FAD object with the given dump.

    Args:
      dump: The data from the SAS UUT or test harness to hold. This is in the
        form of a dictionary with field names matching the recordType: cbsd,
        esc_sensor, zone. Within these fields is a list of all the records of
        that type. If a field is not present it will be added to the dictionary
        referring to an empty list.
    """
    self._dump_data = dump
    # Check no unknown fields exist in the dump and ensure all fields have data.
    for field_name in self._dump_data:
      if field_name not in self._valid_field_names:
        raise ValueError('Dump field name \"%s\" is not a valid field to be '
          'contained in a FullActivityDump' % field_name)
    for field_name in self._valid_field_names:
      if field_name not in self._dump_data:
        self._dump_data[field_name] = []

  def getData(self):
    """Returns all data in FAD.

    Returns:
      A copy of the internal dictionary of FAD data. See __init__ for the
      structure of the data.
    """
    return dict(self._dump_data)

  def _getRecords(self, record_type, filters):
    """Returns the given record type with filters applied."""
    if not filters:
      # Always return a copy for consistency
      return list(self._dump_data[record_type])
    response = self._dump_data[record_type]
    for f in filters:
      response = filter(f, response)
    return response

  def getCbsdRecords(self, filters=[]):
    """Returns all CBSD records matching ALL of the given filters.

    Example usage 1:
      fad = Full Activity dump with CBSDs 0 to N.
      s = Set(['cbsd12','cbsd23','cbsd41'])
      f = lambda x: x['id'] in s
      fad.getCbsdRecords([f]) # returns 'cbsd12','cbsd23','cbsd41' record list

    Example usage 2 (fad and s defined as in last example):
    def f(x, s):
      return x['id'] in s
    fad.getCbsdRecords([partial(f, s=s)]) # returns 'cbsd12','cbsd23','cbsd41'
    record list

    Args:
      filters: A list of functions which all return True iff a record passed as
        its only argument should be included in the result.
    Returns:
      A list of all cbsd records that match the filters. If there are no filters
      then all records will be returned.
    """
    return self._getRecords('cbsd', filters)

  def setCbsdRecords(self, records):
    """Sets the internal CBSD record data to the given list of records.

    Args:
      records: A list of CBSD records to store.
    """
    self._dump_data['cbsd'] = records

  def getEscSensorRecords(self, filters=[]):
    """Returns all ESC sensor records matching the given filters.

    Same usage as getCbsdRecords above.

    Args:
      filters: A list of functions which all return True iff a record passed as
        it's only argument should be included in the result.
    Returns:
      A list of all ESC sensor records that match the filters, if there are no
      filters then all records will be returned.
    """
    return self._getRecords('esc_sensor', filters)

  def setEscSensorRecords(self, records):
    """Sets the internal ESC sensor record data to the given list of records.

    Args:
      records: A list of ESC sensor records to store.
    """
    self._dump_data['esc_sensor'] = records

  def getZoneRecords(self, filters=[]):
    """Returns all Zone records matching the given filters.

    Same usage as getCbsdRecords above.

    Args:
      filters: A list of functions which all return True iff a record passed as
        it's only argument should be included in the result.
    Returns:
      A list of all zone records that match the filters, if there are no
      filters then all records will be returned.
    """
    return self._getRecords('zone', filters)

  def setZoneRecords(self, records):
    """Sets the internal zone record data to the given list of records.

    Args:
      records: A list of zone records to store.
    """
    self._dump_data['zone'] = records
