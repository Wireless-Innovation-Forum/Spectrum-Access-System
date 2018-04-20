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

# This script extracts data from the IBFS database files retrieved from the
# FCC FTP site, writing results into the data/ibfs directory.

import csv
import os
import re
import zipfile

# This utility loads the IBFS schema file and creates a dict with the keys
# being the table names and the values being a dict of column names mapped
# to the positional index of that column in the dump files.
def LoadIBFSSchema(schema_file):
  print 'Loading IBFS schema...'
  table_schema = {}
  with open(schema_file, 'r') as schema:
    content = schema.read()
  table_sources = content.split('\n)')
  for s in table_sources:
    lines = s.split('\n')
    table_name = ''
    column_index = 0
    for l in lines:
      if l.find('create table ') != -1:
        index = l.find('create table ') + len('create table ')
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
    if datfile in ['main.dat', 'address.dat', 'anten.dat', 'freq.dat', 'freq_coord.dat', 'site.dat', 'ant_fx.dat']:
      try:
        print '   extracting %s' % datfile
        content = zf.read(datfile)
        with open(os.path.join(tmpDir, datfile), 'w') as out:
          out.write(content)
      except Exception, err:
        raise Exception('Cannot extract ' + datfile + ' from ' + zip_filename)


# Collapse an array of coordination records for a particular antenna.
# This will collapse the elevation/azimuth entries as a string.
# TODO: this needs some consideration -- if the arc is maintained it needs
# modification.
def CollapseCoordinationRecords(coord_rec):
  if len(coord_rec) == 1:
    return coord_rec[0]
  else:
    print 'Collapsing %s' % coord_rec
    result = coord_rec[0]
    for c in coord_rec[1:]:
      if 'elevation_west' in result and 'elevation_west' in c:
        result['elevation_west'] = result['elevation_west'] + ' ' + c['elevation_west']
      if 'elevation_east' in result and 'elevation_east' in c:
        result['elevation_east'] = result['elevation_east'] + ' ' + c['elevation_east']
      if 'azimuth_west' in result and 'azimuth_west' in c:
        result['azimuth_west'] = result['azimuth_west'] + ' ' + c['azimuth_west']
      if 'azimuth_east' in result and 'azimuth_east' in c:
        result['azimuth_east'] = result['azimuth_east'] + ' ' + c['azimuth_east']
    print ' --> to %s' % result
    return result
 
 
# Extract a row from a particular table type into a dictionary where only
# the columns we're interested in are preserved.
# The IBFS table structure is that the MAIN table has a filing_key,
# which is referenced by
#   The SITE table, having also a site_key
#     The ANTENNA table, which has a site_key and an antenna_key
#       The FREQUENCY table has an antenna_key and a frequency_key
#       The FREQ_COORD table, which has an antenna_key and a coord_key
def RowToRecord(row, schema, table):
  fields = {
    'MAIN' : [ 'filing_key',
               'address_key',
               'filing_state',
               'callsign',
               'status_code',
               'subsystem_code',
               'last_action',
               'last_action_date',
               'date_grant',
               'date_expire'],
    'SITE' : [ 'filing_key',
               'site_key',
               'site_city',
               'site_state',
               'lat_deg',
               'lat_min',
               'lat_sec',
               'lat_hemi',
               'long_deg',
               'long_min',
               'long_sec',
               'long_hemi' ],
    'ANTENNA' : [ 'site_key',
                  'antenna_key',
                  'antenna_id',
                  'diameter',
                  'height_max_agl',
                  'manufacturer',
                  'model'],
    'FREQUENCY' : [ 'antenna_key',
                    'frequency_key',
                    'polarization_code',
                    'eirp',
                    'frequency_lower',
                    'frequency_upper' ],
    'FREQ_COORD' : [ 'coord_key',
                     'antenna_key',
                     'azimuth_east',
                     'azimuth_west',
                     'elevation_east',
                     'elevation_west',
                     'freq_limit_low',
                     'freq_limit_high',
                     'horiz_max_density',
                     'sat_arc_east',
                     'sat_arc_west',
                     'sat_hemi_east',
                     'sat_hemi_west',
                     'sat_orbit_type' ]
    }

  record = {}
  for f in fields[table]:
    # If the field is empty, then don't add it to the dict.
    val = row[schema[table][f]]
    if val:
      record[f] = val
  return record


# Some IBFS database lines are denormalized: they do not escape line returns,
# and so have a record split onto multiple lines. Such lines do not have the
# right final signal field ("^", so we will join them to the next line.
def NormalizeLines(content, suffix):
  lines = content.split('\n')
  i = 0
  while i < len(lines):
    if lines[i].strip().endswith(suffix):
      i += 1
      continue
    else:
      if i >= len(lines)-1:
        i += 1
        continue
      if i < len(lines) - 1:
        # print '\n\nMerging lines %s\n and \n%s' % (lines[i], lines[i+1])
        lines[i] = lines[i].strip() + ' ' + lines.pop(i+1).strip()
        # print '\n\nHAVE: \n%s' % lines[i]
      else:
        raise Exception('Ran out of lines!')
  return lines  


def ReadULSDataRecords(tmpDir, schema, filename, table):
  records = []
  with open(os.path.join(tmpDir, filename), 'r') as dat:
    content = dat.read()
    lines = NormalizeLines(content, '|^|')
    reader = csv.reader(lines, delimiter='|')
    for row in reader:
      if len(row) == 0:
        continue
      r = RowToRecord(row, schema, table)
      records.append(r)
  return records


# These are the fields to be written in the order they're written.
output_fields = [ 'filing_key',
                  'address_key',
                  'filing_state',
                  'callsign',
                  'status_code',
                  'subsystem_code',
                  'last_action',
                  'last_action_date',
                  'date_grant',
                  'date_expire',
                  'site_city',
                  'site_state',
                  'lat_deg',
                  'lat_min',
                  'lat_sec',
                  'lat_hemi',
                  'long_deg',
                  'long_min',
                  'long_sec',
                  'long_hemi',
                  'antenna_id',
                  'diameter',
                  'height_max_agl',
                  'manufacturer',
                  'model',
                  'polarization_code',
                  'eirp',
                  'frequency_lower',
                  'frequency_upper',
                  'azimuth_east',
                  'azimuth_west',
                  'elevation_east',
                  'elevation_west',
                  'freq_limit_low',
                  'freq_limit_high',
                  'horiz_max_density',
                  'sat_arc_east',
                  'sat_arc_west',
                  'sat_hemi_east',
                  'sat_hemi_west',
                  'sat_orbit_type' ]

def WriteHeaderRecord(outfile):
  line = ''
  for f in output_fields:
    if line:
      line += ','
    line += f
  line += '\n'
  outfile.write(line)


def WriteRecord(outfile, record):
  line = ''
  for f in output_fields:
    if line:
      line += ','
    if f in record:
      line += str(record[f])
  line += '\n'
  outfile.write(line)


def ExtractIBFSData(directory):
  schema = LoadIBFSSchema(os.path.join(directory, 'ibfs.txt'))

  # Open the IBFS.zip file and extract the data files we'd like from it.
  UnzipNeededFiles(os.path.join(directory, 'IBFS.zip'), directory)  

  main = {}
  count = 0
  records = ReadULSDataRecords(directory, schema, 'main.dat', 'MAIN')
  for r in records:
    count += 1
    if (r['subsystem_code'] == 'SES' and 
        (r['filing_state'] == '0' or r['filing_state'] == '1')):
      main[r['filing_key']] = r
  print 'Found %d MAIN records of %d' % (len(main), count)

  site = {}
  records = ReadULSDataRecords(directory, schema, 'site.dat', 'SITE')
  count = 0
  for r in records:
    count += 1
    if not r['filing_key'] in main:
      continue
    site[r['site_key']] = r
  print 'Found %d SITE records of %d' % (len(site), count)

  antenna = {}
  records = ReadULSDataRecords(directory, schema, 'anten.dat', 'ANTENNA')
  count = 0
  for r in records:
    count += 1
    if not r['site_key'] in site:
      continue
    antenna[r['antenna_key']] = r
  print 'Found %d ANTENNA records of %d' % (len(antenna), count)

  freq = {}
  records = ReadULSDataRecords(directory, schema, 'freq.dat', 'FREQUENCY')
  count = 0
  c2 = 0
  for r in records:
    count += 1

    if not r['antenna_key'] in antenna:
      continue
    c2 += 1

    if not 'frequency_upper' in r and not 'frequency_lower' in r:
      print 'No frequency fields in %s' % r
      continue
    if not 'frequency_lower' in r:
      print 'No frequency_lower in %s' % r
      r['frequency_lower'] = r['frequency_upper']
    if not 'frequency_upper' in r:
      print 'No frequency_upper in %s' % r
      r['frequency_upper'] = r['frequency_lower']
    r['frequency_lower'] = float(r['frequency_lower'])
    r['frequency_upper'] = float(r['frequency_upper'])

    if not (r['frequency_lower'] >= 3950.0 or
            r['frequency_upper'] <= 3450.0):
      if not r['antenna_key'] in freq:
        freq[r['antenna_key']] = r
      else:
        prev = freq[r['antenna_key']]
        # print 'Combining %s and  %s' % (prev, r)
        freq[r['antenna_key']]['frequency_lower'] = min(prev['frequency_lower'],
                                                        r['frequency_lower'])
        freq[r['antenna_key']]['frequency_upper'] = max(prev['frequency_upper'],
                                                        r['frequency_upper'])
        # print '-->Combined to %s' % freq[r['antenna_key']]
  print 'Found %d FREQUENCY records of %d : %d' % (len(freq), c2, count)

  coord = {}
  records = ReadULSDataRecords(directory, schema, 'freq_coord.dat', 'FREQ_COORD')
  count = 0
  c2 = 0
  for r in records:
    count += 1
    if not r['antenna_key'] in antenna:
      continue
    c2 += 1

    if not 'freq_limit_low' in r and not 'freq_limit_high' in r:
      print 'No frequency fields in %s' % r
      continue
    if not 'freq_limit_low' in r:
      # print 'No freq_limit_low in %s' % r
      r['freq_limit_low'] = r['freq_limit_high']
    if not 'freq_limit_high' in r:
      # print 'No freq_limit_high in %s' % r
      r['freq_limit_high'] = r['freq_limit_low']
    r['freq_limit_low'] = float(r['freq_limit_low'])
    r['freq_limit_high'] = float(r['freq_limit_high'])

    if not (r['freq_limit_low'] >= 3950.0 or
            r['freq_limit_high'] <= 3450.0):
      if not r['antenna_key'] in coord:
        coord[r['antenna_key']] = [r]
      else:
        coord[r['antenna_key']].append(r)
  print 'Found %d FREQ_COORD records of %d : %d' % (len(coord), count, c2)

  # Now consolidate the records by antenna (the device in SAS usage).
  outfile = open(os.path.join(directory, 'ibfs.csv'), 'w')
  WriteHeaderRecord(outfile)
  count = 0
  for d in antenna:
    antenna_rec = antenna[d]
    if not antenna_rec['antenna_key'] in freq:
      continue
    site_rec = site[antenna_rec['site_key']]
    main_rec = main[site_rec['filing_key']]
    freq_rec = freq[antenna_rec['antenna_key']]
    coord_rec = []
    if antenna_rec['antenna_key'] in coord:
      coord_rec = coord[antenna_rec['antenna_key']]

    record = antenna_rec
    record.update(freq_rec)
    record.update(site_rec)
    record.update(main_rec)
    if len(coord_rec) > 0:
      record.update(CollapseCoordinationRecords(coord_rec))

    WriteRecord(outfile, record)
    count += 1
  print 'Wrote %d CSV records' % count


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
ibfsDir = os.path.join(os.path.join(rootDir, 'data'), 'ibfs')

print 'Extracting IBFS data file from database files in dir=%s' % ibfsDir
ExtractIBFSData(ibfsDir)

