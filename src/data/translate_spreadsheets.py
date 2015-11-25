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

# This script translates FCC spreadsheet files into CSV format. The files
# translated are the rural/non-rural census tracts and the spreadsheet
# containing the list of grandfathered FSS stations.

import csv
import os
import xlrd

# Read the given spreadsheet and emit a CSV file with the same contents.
# Note: this translates Excel date formats into ISO YYYY-MM-DD format.
def TranslateSpreadsheet(sheet, csvfile):
  print 'Translating spreadsheet %s to CSV %s' % (sheet, csvfile)
  wb = xlrd.open_workbook(sheet)
  sheet = wb.sheet_by_index(0)
  with open(csvfile, 'w') as out:
    writer = csv.writer(out, quotechar='\"')
    date_columns = []
    for rownum in range(0, sheet.nrows):
      row = sheet.row_values(rownum)
      for i in range(0, len(row)):
        if type(row[i]) == unicode:
          row[i] = row[i].encode('ascii', 'ignore')
      # For the first two rows, find any labels containing 'Date' substring...
      if rownum==0 or rownum==1:
        for i in range(0, len(row)):
          if isinstance(row[i], basestring) and 'Date' in row[i]:
            print 'Found date column %s at %d' % (row[i], i)
            date_columns.append(i)
      else:
        for i in date_columns:
          translated_date = xlrd.xldate_as_tuple(row[i], 0)
          row[i] = '%04d-%02d-%02d' % (translated_date[0], translated_date[1], translated_date[2])
      for i in range(0, len(row)):
        if type(row[i]) == float and int(row[i]) == row[i]:
          row[i] = int(row[i])

      # Translate all strings to ascii, throwing away any unknown characters
      writer.writerow(row)


# Find the directory of this script.
dir = os.path.dirname(os.path.realpath(__file__))
rootDir = os.path.dirname(os.path.dirname(dir))
fccDir = os.path.join(os.path.join(rootDir, 'data'), 'fcc')

# Translate the spreadsheets to CSV.
TranslateSpreadsheet(os.path.join(fccDir, 'DOC-333151A1.xlsx'),
                     os.path.join(fccDir, 'CBRS_3550_3700_GrandfatheredFSS.csv'))

TranslateSpreadsheet(os.path.join(fccDir, 'DOC-334099A1.xlsx'),
                     os.path.join(fccDir, '3.5GHzRuralCensusTracts.csv'))
