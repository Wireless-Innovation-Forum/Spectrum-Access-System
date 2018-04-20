#    Copyright 2015 SAS Project Authors. All Rights Reserved.
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

# This script extracts a set of operating characteristics for 3650-3700
# devices (radio type 'NN') from the ULS data files.
# The script writes a CSV file into the data/uls directory.

import csv
import datetime
import os
import re
import shutil
import zipfile

# This utility loads the ULS schema file and creates a dict with the keys
# being the table names (the "dbo.PUBACC_" prefix is stripped) and the values
# being a dict of column names mapped to the positional index of that column
# in the dump files.
def LoadULSSchema(schema_file):
  print 'Loading ULS schema...'
  table_schema = {}
  with open(schema_file, 'r') as schema:
    content = schema.read()
  table_sources = content.split('\n)')
  for s in table_sources:
    lines = s.split('\n')
    table_name = ''
    column_index = 0
    for l in lines:
      if l.find('PUBACC_') != -1:
        index = l.find('PUBACC_') + len('PUBACC_')
        table_name = l[index:].strip()
        print '  Found table %s' % table_name
        table_schema[table_name] = {}
      elif table_name:
        tokens = re.split('\W+', l)
        if len(tokens) > 2:
          field = tokens[1]
          print '    Found field %s=%d' % (field, column_index)
          table_schema[table_name][field] = column_index
          column_index += 1
  return table_schema          
  

# Extract the wanted zipped data files from the given zipfile into the
# given temporary directory.
def UnzipNeededFiles(zip_filename, tmpDir):
  zf = zipfile.ZipFile(zip_filename, 'r')
  for datfile in zf.namelist():
    if datfile in ['AN.dat', 'FR.dat', 'HD.dat', 'LO.dat', 'EM.dat', 'EN.dat']:
      try:
        print '   extracting %s' % datfile
        content = zf.read(datfile)
        with open(os.path.join(tmpDir, datfile), 'w') as out:
          out.write(content)
      except Exception, err:
        raise Exception('Cannot extract ' + datfile + ' from ' + zip_filename)


# This is the definition of which fields are read from which table.
input_fields = {
  'HD' : [ 'unique_system_identifier',
           'license_status',
           'call_sign',
           'radio_service_code',
           'grant_date',
           'expired_date',
           'effective_date',
           'last_action_date'],
  'LO' : [ 'unique_system_identifier',
           'location_number',
           'location_city',
           'location_state',
           'structure_type',
           'location_name',
           'lat_degrees',
           'lat_minutes',
           'lat_seconds',
           'lat_direction',
           'long_degrees',
           'long_minutes',
           'long_seconds',
           'long_direction',
           'tower_registration_number'],
  'AN' : [ 'unique_system_identifier',
           'location_number',
           'antenna_number',
           'antenna_make',
           'antenna_model',
           'beamwidth',
           'tilt',
           'gain',
           'azimuth',
           'height_to_center_raat'],
  'FR' : [ 'unique_system_identifier',
           'location_number',
           'antenna_number',
           'eirp',
           'transmitter_model',
           'frequency_assigned',
           'frequency_upper_band'],
  'EM' : [ 'unique_system_identifier',
           'location_number',
           'antenna_number',
           'emission_code'],
  'EN' : [ 'unique_system_identifier',
           'licensee_id',
           'entity_name',
           'frn',
           'email']
}

# Extract a row from a particular table type into a dictionary where only
# the columns we're interested in are preserved.
# The tables are structured as follows:
# The HD table is the header table with the call sign.
#   The LO table is the location table with various specific sites in it.
#      The AN table has the radio emitters located at that site.
#         The FR table contains the frequency characteristics of emissions
#         from those antennas.
#         The EM table contains emission code designators for emissions
#         from those antennas.
def RowToRecord(row, schema, table):
  record = {}
  for f in input_fields[table]:
    # If the field is empty, then don't add it to the dict.
    val = row[schema[table][f]]
    if val:
      record[f] = val
  return record


# Some ULS database lines are denormalized: they do not escape line returns,
# and so have a record split onto multiple lines. Such lines do not have the
# right first column, so we will join them to the previous line.
def NormalizeLines(content, prefix):
  lines = content.split('\n')
  i = 0
  while i < len(lines):
    if lines[i].startswith(prefix):
      i += 1
      continue
    else:
      lines[i-1] = lines[i-1].strip() + ' ' + lines.pop(i).strip()
  return lines  


def ReadULSDataRecords(tmpDir, schema, table):
  records = []
  with open(os.path.join(tmpDir, table + '.dat'), 'r') as dat:
    content = dat.read()
    lines = NormalizeLines(content, table + '|')
    reader = csv.reader(lines, delimiter='|')
    for row in reader:
      r = RowToRecord(row, schema, table)
      records.append(r)
  return records


# These are the fields to be written in the order they're written.
output_fields = [ 'unique_system_identifier',
                  'location_number',
                  'antenna_number',
                  'call_sign',
                  'grant_date',
                  'expired_date',
                  'location_city',
                  'location_state',
                  'lat_degrees',
                  'lat_minutes',
                  'lat_seconds',
                  'lat_direction',
                  'long_degrees',
                  'long_minutes',
                  'long_seconds',
                  'long_direction',
                  'height_to_center_raat',
                  'beamwidth',
                  'tilt',
                  'gain',
                  'azimuth',
                  'antenna_make',
                  'antenna_model',
                  'transmitter_model',
                  'location_name',
                  'emission_code',
                  'structure_type',
                  'frequency_assigned',
                  'frequency_upper_band',
                  'eirp',
                  'effective_date',
                  'tower_registration_number',
                  'last_action_date',
                  'licensee_id',
                  'entity_name',
                  'frn',
                  'email']


def WriteHeaderRecord(outfile):
  line = []
  for f in output_fields:
    line.append(f)
  outfile.writerow(line)


# Write a CSV line. |outfile| is the csv.writer
def WriteRecord(outfile, record):
  line = []
  for f in output_fields:
    if f in record:
      line.append(record[f])
    else:
      line.append('')
      print '!!! Missing field %s in %s' % (f, record)
  outfile.writerow(line)


# Read database files from a unzipped temp directory. Do a join of data
# from various input tables and consolidate the results into flat records.
def ProcessULSData(tmpDir, schema, outfile):
  print 'Processing data in %s into %s' % (tmpDir, outfile)
  outf = open(outfile, 'w')
  outwriter = csv.writer(outf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
  WriteHeaderRecord(outwriter)

  count = 0
  hd = {}
  records = ReadULSDataRecords(tmpDir, schema, 'HD')
  for r in records:
    # TODO: preserve inactive entries as well?
    # TODO: limit by license expiration date? Do other CBRS-based date math?
    if (r['radio_service_code'] == 'NN' and r['license_status'] == 'A'):
      hd_id = r['unique_system_identifier']
      hd[hd_id] = r
      count += 1
  print 'Found %d HD records' % count

  count = 0
  lo = {}
  records = ReadULSDataRecords(tmpDir, schema, 'LO')
  for r in records:
    hd_id = r['unique_system_identifier']
    if hd_id in hd:
      lo_id = r['unique_system_identifier'] + '.' + r['location_number']
      if 'location_name' not in r:
        r['location_name'] = '' 
      if 'tower_registration_number' not in r:
        r['tower_registration_number'] = '' 

      lo[lo_id] = r
      count += 1
  print 'Found %d LO records' % count

  count = 0
  en = {}
  records = ReadULSDataRecords(tmpDir, schema, 'EN')
  for r in records:
    hd_id = r['unique_system_identifier']
    if hd_id in hd:
      en_id = r['unique_system_identifier']
      # Note: there are duplicate EN records per HD record. They seem
      # to be used for different fields. Solution: merge the records.
      if en_id in en:
        # print 'Found existing EN record %s and %s' % (en[en_id], r)
        en[en_id].update(r)
      else:
        count += 1
        if 'licensee_id' not in r:
          r['licensee_id'] = ''
        if 'email' not in r:
          r['email'] = ''
        en[en_id] = r
  print 'Found %d EN records' % count

  count = 0
  an = {}
  records = ReadULSDataRecords(tmpDir, schema, 'AN')
  for r in records:
    hd_id = r['unique_system_identifier']
    lo_id = r['unique_system_identifier'] + '.' + r['location_number']
    if hd_id in hd and lo_id in lo:
      an_id = r['unique_system_identifier'] + '.' + r['location_number'] + '.' + r['antenna_number']
      an[an_id] = r
      count += 1
  print 'Found %d AN records' % count

  count = 0
  em = {}
  records = ReadULSDataRecords(tmpDir, schema, 'EM')
  for r in records:
    hd_id = r['unique_system_identifier']
    lo_id = r['unique_system_identifier'] + '.' + r['location_number']
    an_id = r['unique_system_identifier'] + '.' + r['location_number'] + '.' + r['antenna_number']
    if hd_id in hd and lo_id in lo and an_id in an:
      em_id = r['unique_system_identifier'] + '.' + r['location_number'] + '.' + r['antenna_number']
      if 'emission_code' not in r:
        r['emission_code'] = ''
      em[em_id] = r
      count += 1
  print 'Found %d EM records' % count
     
  count = 0
  fr = {}
  records = ReadULSDataRecords(tmpDir, schema, 'FR')
  for r in records:
    hd_id = r['unique_system_identifier']
    en_id = r['unique_system_identifier']
    lo_id = r['unique_system_identifier'] + '.' + r['location_number']
    an_id = r['unique_system_identifier'] + '.' + r['location_number'] + '.' + r['antenna_number']
    em_id = r['unique_system_identifier'] + '.' + r['location_number'] + '.' + r['antenna_number']
    if hd_id in hd and lo_id in lo and an_id in an:
      hdrec = hd[hd_id]
      enrec = en[en_id]
      lorec = lo[lo_id]
      anrec = an[an_id]
      emrec = {}
      if em_id in em:
        emrec = em[em_id]

      # Note: quite a few records are missing the frequency_upper_band field. When that's the case,
      # use 3700
      if 'frequency_upper_band' not in r:
        r['frequency_upper_band'] = '3700'

      frrec = r

      # Now we have the outer-joined records from HR, LO, AN, and FR. Can extract whatever fields
      # we want from them. This creates a composite record by just overwriting fields from earlier
      # records from later ones.
      reg = hdrec
      reg.update(enrec)
      reg.update(lorec)
      reg.update(anrec)
      reg.update(emrec)
      reg.update(frrec)
      # Now reg is the merged registration record ready for output.
      WriteRecord(outwriter, reg)
      count += 1
  print 'Found %d FR records' % count

  outf.close()
  

# This method extracts all the records from the zip files, flattens them,
# and writes them to csv files.
def ProcessULS(directory):
  schema = LoadULSSchema(os.path.join(directory, 'pa_ddef49.txt'))
  tmpDir = os.path.join(directory, 'tmp')
  print 'Unzipping weekly ULS files to %s' % tmpDir
  if not os.path.exists(tmpDir):
    os.mkdir(tmpDir)
  UnzipNeededFiles(os.path.join(directory, 'l_micro.zip'), tmpDir)
  ProcessULSData(tmpDir, schema, os.path.join(directory, 'l_micro.csv'))
  shutil.rmtree(tmpDir)

  days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
  for d in days:
    os.mkdir(tmpDir)
    UnzipNeededFiles(os.path.join(directory, 'l_mw_' + d + '.zip'), tmpDir)
    ProcessULSData(tmpDir, schema, os.path.join(directory, 'l_mw_' + d + '.csv'))
    shutil.rmtree(tmpDir)

  ConsolidateULSData(directory)


# Read a CSV flat file with ULS data. The column names are in the first row.
def LoadULSFlatFile(filename):
  records = {}
  header = []
  with open(filename, 'r') as data:
    reader = csv.reader(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for row in reader:
      if header == []:
        header = row
      else:
        r = {}
        for i in range(0, len(header)):
          r[header[i]] = row[i]
        key = r['unique_system_identifier'] + '.' + r['location_number'] + '.' + r['antenna_number']
        records[key] = r
        if len(row) != len(header):
          print '!!! Bad record: %s' % row
  print 'Read %d records from %s' % (len(records), filename)
  return records

# This method combines the extracted data from the CSV files, maintaining only
# the most recent 'last_action_date' entry for any particular rows.
# The keys for the row are the 'unique_system_identifer', 'location_number', and
# 'antenna_number' for the sector.
def ConsolidateULSData(directory):
  # Load the l_micro.csv file
  l_micro = LoadULSFlatFile(os.path.join(directory, 'l_micro.csv'))

  days = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
  for d in days:
    l_mw = LoadULSFlatFile(os.path.join(directory, 'l_mw_' + d + '.csv'))
    for k in l_mw:
      rec = l_mw[k]
      if k in l_micro and rec['last_action_date'] != l_micro[k]['last_action_date']:
        new_date = datetime.datetime.strptime(rec['last_action_date'], '%m/%d/%Y')
        orig_date = datetime.datetime.strptime(l_micro[k]['last_action_date'], '%m/%d/%Y')
        if orig_date < new_date:
          l_micro[k] = rec
        else:
          print '%s: Found later date %s in l_mw; %s in l_micro' % (
            k, rec['last_action_date'], l_micro[k]['last_action_date'])
      else:
        l_micro[k] = rec

  outf = open(os.path.join(directory, 'uls.csv'), 'w')
  outwriter = csv.writer(outf, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
  WriteHeaderRecord(outwriter)
  for row in l_micro:
    WriteRecord(outwriter, l_micro[row])
  outf.close()
  print 'Wrote %d total ULS records' % len(l_micro)


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
ulsDir = os.path.join(os.path.join(rootDir, 'data'), 'uls')
print 'Processing ULS files in dir=%s' % ulsDir

ProcessULS(ulsDir)

# TODO: The rows from the daily files, if different, supercede the weekly file, so
# they can be merged into a composite file. If the same key exists in multiple
# files, then the copy with greater last_action_date field takes precedence.
print 'Finished.'

