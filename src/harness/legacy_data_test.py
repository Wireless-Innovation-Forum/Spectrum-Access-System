#    Copyright 2026 SAS Project Authors. All Rights Reserved.
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

"""Exercise Python 3 legacy data conversion without contacting upstream services."""

import csv
from datetime import datetime
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import warnings
import zipfile

from lxml import etree


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'src' / 'data' / 'legacy'


def load_script(name):
  specification = importlib.util.spec_from_file_location(
      'legacy_' + name, SCRIPTS / (name + '.py'))
  module = importlib.util.module_from_spec(specification)
  with warnings.catch_warnings():
    # ftputil announces a future default at import time. The retrieval script
    # explicitly configures UTF-8, so this default-change notice is irrelevant.
    warnings.filterwarnings(
        'ignore', category=DeprecationWarning,
        message=r'^In ftputil 6\.0\.0, the default file path encoding will change '
                r'from Latin-1 to UTF-8\. Explicitly specify encoding="latin-1" '
                r'for the path encoding if the remote file system uses Latin-1 '
                r'encoding\.$')
    specification.loader.exec_module(module)
  return module


class LegacyDataTest(unittest.TestCase):
  def test_imports_do_not_convert_or_download_data(self):
    with patch('builtins.open', side_effect=AssertionError('File opened on import')), \
         patch('urllib.request.urlopen', side_effect=AssertionError('Network on import')):
      for name in ('3650_3700_radar_sites', 'extract_ibfs', 'extract_uls_data',
                   'retrieve_ibfs', 'retrieve_uls_files', 'translate_spreadsheets'):
        with self.subTest(script=name):
          self.assertTrue(callable(load_script(name).main))

  def test_radar_generates_parseable_kml_in_archived_fcc_directory(self):
    module = load_script('3650_3700_radar_sites')
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      destination = directory / 'data' / 'fcc' / 'legacy'
      destination.mkdir(parents=True)
      with patch.object(module, '__file__', str(directory / 'src' / 'data' / 'legacy' / 'radar.py')):
        module.main()
      kml = etree.parse(str(destination / '3650_3700_radar_sites.kml'))
      namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
      self.assertEqual(len(kml.findall('.//kml:Placemark', namespace)), 6)
      for polygon in kml.findall('.//kml:Polygon', namespace):
        points = polygon.find('.//kml:coordinates', namespace).text.split()
        self.assertEqual(len(points), 73)
        self.assertEqual(points[0], points[-1])

  def test_ibfs_zip_records_convert_to_quoted_utf8_csv(self):
    module = load_script('extract_ibfs')
    fields = ['filing_key', 'address_key', 'filing_state', 'callsign',
              'status_code', 'subsystem_code', 'last_action',
              'last_action_date', 'date_grant', 'date_expire']
    schema = {'MAIN': {field: index for index, field in enumerate(fields)}}
    values = ['1', '2', '0', 'Caf\u00e9, Station', 'A', 'SES', 'Grant',
              '01/01/2020', '01/01/2020', '01/01/2030']
    contents = ('|'.join(values) + '|^|\r\n').encode('latin-1')
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      archive = directory / 'IBFS.zip'
      with zipfile.ZipFile(archive, 'w') as output:
        output.writestr('main.dat', contents)
        output.writestr('unused.dat', b'unused')
      module.UnzipNeededFiles(archive, directory)
      self.assertEqual((directory / 'main.dat').read_bytes(), contents)
      self.assertFalse((directory / 'unused.dat').exists())
      records = module.ReadULSDataRecords(directory, schema, 'main.dat', 'MAIN')
      target = directory / 'ibfs.csv'
      with target.open('w', encoding='utf-8', newline='') as output:
        module.WriteHeaderRecord(output)
        module.WriteRecord(output, records[0])
      with target.open(encoding='utf-8', newline='') as output:
        converted = list(csv.DictReader(output))
      self.assertEqual(len(converted), 1)
      self.assertEqual(converted[0]['callsign'], values[3])
      self.assertEqual(converted[0]['filing_key'], '1')

  def test_uls_zip_records_decode_legacy_text(self):
    module = load_script('extract_uls_data')
    schema = {'HD': {field: index + 1 for index, field in enumerate(module.input_fields['HD'])}}
    row = ['HD', '1', 'A', 'Caf\u00e9', 'CF', '01/01/2020',
           '01/01/2030', '01/01/2020', '01/01/2020']
    contents = ('|'.join(row) + '\r\n').encode('latin-1')
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      archive = directory / 'uls.zip'
      with zipfile.ZipFile(archive, 'w') as output:
        output.writestr('HD.dat', contents)
      module.UnzipNeededFiles(archive, directory)
      records = module.ReadULSDataRecords(directory, schema, 'HD')
      self.assertEqual(records[0]['call_sign'], 'Caf\u00e9')

  def test_uls_downloads_write_bytes_without_changing_working_directory(self):
    module = load_script('retrieve_uls_files')
    contents = b'archive bytes\x00\xff'
    original_directory = Path.cwd()
    def response(_url):
      stream = io.BytesIO(contents)
      stream.getcode = lambda: 200
      return stream
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      with patch.object(module, '__file__', str(directory / 'src' / 'data' / 'legacy' / 'retrieve.py')), \
           patch.object(module.urllib.request, 'urlopen', side_effect=response) as fetch:
        module.main()
      destination = directory / 'data' / 'uls'
      self.assertEqual(fetch.call_count, 9)
      self.assertEqual(len(list(destination.iterdir())), 9)
      self.assertEqual((destination / 'l_micro.zip').read_bytes(), contents)
      self.assertEqual((destination / 'pa_ddef49.txt').read_bytes(), contents)
      self.assertEqual(Path.cwd(), original_directory)

  def test_ibfs_retrieval_uses_current_ftp_lifetime_api(self):
    module = load_script('retrieve_ibfs')
    host = Mock(spec=['download_if_newer'])
    context = Mock()
    context.__enter__ = Mock(return_value=host)
    context.__exit__ = Mock(return_value=False)
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      with patch.object(module.ftputil, 'FTPHost', return_value=context), \
           patch.object(module, '__file__', str(directory / 'src' / 'data' / 'legacy' / 'retrieve.py')):
        module.main()
      context.__exit__.assert_called_once()
      destinations = [call.args[1] for call in host.download_if_newer.call_args_list]
      self.assertEqual(destinations, [str(directory / 'data' / 'ibfs' / filename)
                                     for filename in ('IBFS.zip', 'ibfs.txt')])

  def test_extractors_resolve_repository_data_directories(self):
    for name, method, folder in [('extract_ibfs', 'ExtractIBFSData', 'ibfs'),
                                 ('extract_uls_data', 'ProcessULS', 'uls')]:
      module = load_script(name)
      with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        with patch.object(module, '__file__', str(directory / 'src' / 'data' / 'legacy' / 'extract.py')), \
             patch.object(module, method) as extract:
          module.main()
        self.assertEqual(Path(extract.call_args.args[0]), directory / 'data' / folder)

  @unittest.skipUnless(importlib.util.find_spec('openpyxl'), 'requires the scripts extra')
  def test_spreadsheets_preserve_dates_numbers_and_csv_values(self):
    import openpyxl
    from openpyxl.utils.datetime import CALENDAR_MAC_1904, to_excel
    module = load_script('translate_spreadsheets')
    with tempfile.TemporaryDirectory() as temporary:
      directory = Path(temporary)
      source = directory / 'data.xlsx'
      destination = directory / 'converted.csv'
      workbook = openpyxl.Workbook()
      workbook.epoch = CALENDAR_MAC_1904
      sheet = workbook.active
      sheet.append(['Dataset', None, None])
      sheet.append(['Name', 'Action Date', 'Value'])
      sheet.append(['Caf\u00e9, Station', datetime(2026, 10, 11), 12.0])
      # Some old workbooks store serial dates without a date cell format.
      sheet.append(['Second', to_excel(datetime(2026, 10, 12), workbook.epoch), 13.5])
      workbook.save(source)
      workbook.close()
      module.TranslateSpreadsheet(source, destination)
      with destination.open(encoding='utf-8', newline='') as output:
        rows = list(csv.reader(output))
      self.assertEqual(rows[2], ['Caf, Station', '2026-10-11', '12'])
      self.assertEqual(rows[3], ['Second', '2026-10-12', '13.5'])


if __name__ == '__main__':
  unittest.main()
