import json
import jsonschema
from pprint import pprint
import os

# Load in a schema file in the given filename.
def loadSchema(filename):
  with open(filename) as sfile:
    schema = json.load(sfile)
    jsonschema.Draft4Validator.check_schema(schema)
    print 'Loaded and verified schema in %s' % filename
    return schema

def loadJson(filename):
  with open(filename) as jfile:
    f = json.load(jfile)
    return f

def testJsonSchema(schema_file, test_file):
  schema = loadSchema(schema_file)
  data = loadJson(test_file)

  print 'Loaded test validation JSON value from %s:' % test_file

  dir = os.path.dirname(os.path.realpath(__file__))

  resolver = jsonschema.RefResolver(referrer=schema, base_uri='file://' + dir + '/')

  try:
    jsonschema.validate(data, schema, resolver=resolver)
  except jsonschema.exceptions.ValidationError as e:
    print e
    print 'FAILED VALIDATION for %s' % test_file
    pprint(data)
    return 1

  print 'Validated.'
  return 0

def testJsonSchemaObject(schema_file, test_file, schemaObject):
  schema = loadSchema(schema_file)
  data = loadJson(test_file)

  print 'Loaded test validation JSON value for %s:' % schemaObject
  pprint (data)

  jsonschema.validate(data, schema[schemaObject])
  print 'Validated.'


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

errors += testJsonSchema('InstallationParamData.schema.json', 'InstallationParamDataExample.json')

errors += testJsonSchema('RegistrationData.schema.json', 'RegistrationDataExample.json')

errors += testJsonSchema('GrantData.schema.json', 'GrantDataExample.json')

errors += testJsonSchema('GrantData.schema.json', 'GrantDataExample2.json')

if errors == 0:
  print 'PASS'
else:
  print 'FAIL: %d validation errors' % errors


