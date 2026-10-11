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
from pathlib import Path

# Read the given spreadsheet and emit a CSV file with the same contents.
# Note: this translates Excel date formats into ISO YYYY-MM-DD format.
def TranslateSpreadsheet(sheet, csvfile):
  import openpyxl
  from openpyxl.utils.datetime import from_excel
  print('Translating spreadsheet %s to CSV %s' % (sheet, csvfile))
  wb = openpyxl.load_workbook(sheet, read_only=True, data_only=True)
  sheet = wb.worksheets[0]
  with open(csvfile, 'w', newline='', encoding='utf-8') as out:
    writer = csv.writer(out, quotechar='\"')
    date_columns = []
    for rownum, values in enumerate(sheet.iter_rows(values_only=True)):
      row = list(values)
      for i in range(0, len(row)):
        if type(row[i]) == str:
          row[i] = row[i].encode('ascii', 'ignore').decode('ascii')
      # For the first two rows, find any labels containing 'Date' substring...
      if rownum==0 or rownum==1:
        for i in range(0, len(row)):
          if isinstance(row[i], str) and 'Date' in row[i]:
            print('Found date column %s at %d' % (row[i], i))
            date_columns.append(i)
      else:
        for i in date_columns:
          if isinstance(row[i], (int, float)) and not isinstance(row[i], bool):
            row[i] = from_excel(row[i], epoch=wb.epoch)
          if hasattr(row[i], 'strftime'):
            row[i] = row[i].strftime('%Y-%m-%d')
      for i in range(0, len(row)):
        if type(row[i]) == float and int(row[i]) == row[i]:
          row[i] = int(row[i])

      # Translate all strings to ascii, throwing away any unknown characters
      writer.writerow(row)
  wb.close()


def main(root_dir=None):
  rootDir = Path(root_dir) if root_dir is not None else Path(__file__).resolve().parents[3]
  fccDir = rootDir / 'data' / 'fcc' / 'legacy'

  # Translate the spreadsheets to CSV.
  TranslateSpreadsheet(os.path.join(fccDir, 'DOC-333151A1.xlsx'),
                       os.path.join(fccDir, 'CBRS_3550_3700_GrandfatheredFSS.csv'))

  TranslateSpreadsheet(os.path.join(fccDir, 'DOC-334099A1.xlsx'),
                       os.path.join(fccDir, '3.5GHzRuralCensusTracts.csv'))


if __name__ == "__main__":
  main()
