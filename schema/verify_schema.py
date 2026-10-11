import json
import jsonschema
from pprint import pprint
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src' / 'harness'))
from schema_validation import validator_for

SCHEMA_DIR = Path(__file__).resolve().parent

# Load in a schema file in the given filename.
def loadSchema(filename):
  with (SCHEMA_DIR / filename).open(encoding='utf-8') as sfile:
    schema = json.load(sfile)
    jsonschema.Draft4Validator.check_schema(schema)
    print('Loaded and verified schema in %s' % filename)
    return schema

def loadJson(filename):
  with (SCHEMA_DIR / filename).open(encoding='utf-8') as jfile:
    f = json.load(jfile)
    return f

def testJsonSchema(schema_file, test_file):
  schema = loadSchema(schema_file)
  data = loadJson(test_file)

  print('Loaded test validation JSON value from %s:' % test_file)

  try:
    validator_for(SCHEMA_DIR / schema_file).validate(data)
  except jsonschema.exceptions.ValidationError as e:
    print(e)
    print('FAILED VALIDATION for %s' % test_file)
    pprint(data)
    return 1

  print('Validated.')
  return 0

def testJsonSchemaObject(schema_file, test_file, schemaObject):
  schema = loadSchema(schema_file)
  data = loadJson(test_file)

  print('Loaded test validation JSON value for %s:' % schemaObject)
  pprint (data)

  jsonschema.validate(data, schema[schemaObject])
  print('Validated.')


def main():
  errors = 0

  errors += testJsonSchema('InstallationParam.schema.json', 'InstallationParamExample.json')
  errors += testJsonSchema('InstallationParam.schema.json', 'InstallationParamExample2.json')

  errors += testJsonSchema('Response.schema.json', 'ResponseExample.json')
  errors += testJsonSchema('Response.schema.json', 'ResponseExample2.json')
  errors += testJsonSchema('Response.schema.json', 'ResponseExample3.json')

  errors += testJsonSchema('RegistrationRequest.schema.json', 'RegistrationRequestExample.json')
  errors += testJsonSchema('RegistrationRequest.schema.json', 'RegistrationRequestExample2.json')

  errors += testJsonSchema('RegistrationResponse.schema.json', 'RegistrationResponseExample.json')

  errors += testJsonSchema('FrequencyRange.schema.json', 'FrequencyRangeExample.json')

  errors += testJsonSchema('SpectrumInquiryRequest.schema.json', 'SpectrumInquiryRequestExample.json')

  errors += testJsonSchema('SpectrumInquiryResponse.schema.json', 'SpectrumInquiryResponseExample.json')

  errors += testJsonSchema('OperationParam.schema.json', 'OperationParamExample.json')

  errors += testJsonSchema('RelinquishmentRequest.schema.json', 'RelinquishmentRequestExample.json')

  errors += testJsonSchema('RelinquishmentResponse.schema.json', 'RelinquishmentResponseExample.json')

  errors += testJsonSchema('DeregistrationRequest.schema.json', 'DeregistrationRequestExample.json')

  errors += testJsonSchema('DeregistrationResponse.schema.json', 'DeregistrationResponseExample.json')

  errors += testJsonSchema('GrantRequest.schema.json', 'GrantRequestExample.json')

  errors += testJsonSchema('GrantResponse.schema.json', 'GrantResponseExample.json')

  errors += testJsonSchema('HeartbeatRequest.schema.json', 'HeartbeatRequestExample.json')

  errors += testJsonSchema('HeartbeatResponse.schema.json', 'HeartbeatResponseExample.json')

  errors += testJsonSchema('MeasReport.schema.json', 'MeasReportExample.json')

  errors += testJsonSchema('PalRecord.schema.json', 'PalRecordExample.json')

  errors += testJsonSchema('FullActivityDump.schema.json', 'FullActivityDumpExample.json')

  errors += testJsonSchema('InstallationParamData.schema.json', 'InstallationParamDataExample.json')

  errors += testJsonSchema('CbsdRecordData.schema.json', 'CbsdRecordDataExample.json')

  errors += testJsonSchema('GrantRecord.schema.json', 'GrantRecordExample.json')

  errors += testJsonSchema('ZoneData.schema.json', 'ZoneDataOfPpaExample.json')

  errors += testJsonSchema('EscSensorRecord.schema.json', 'EscSensorRecordExample.json')

  if errors == 0:
    print('PASS')
  else:
    print('FAIL: %d validation errors' % errors)


  return 0 if errors == 0 else 1


if __name__ == '__main__':
  sys.exit(main())
