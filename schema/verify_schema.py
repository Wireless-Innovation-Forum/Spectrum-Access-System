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

  print 'Loaded test validation JSON value:'
  pprint(data)

  dir = os.path.dirname(os.path.realpath(__file__))

  resolver = jsonschema.RefResolver(referrer=schema, base_uri='file://' + dir + '/')

  jsonschema.validate(data, schema, resolver=resolver)
  print 'Validated.'

def testJsonSchemaObject(schema_file, test_file, schemaObject):
  schema = loadSchema(schema_file)
  data = loadJson(test_file)

  print 'Loaded test validation JSON value for %s:' % schemaObject
  pprint (data)

  jsonschema.validate(data, schema[schemaObject])
  print 'Validated.'


testJsonSchema('AirInterface.schema.json', 'AirInterfaceExample.json')

testJsonSchema('InstallationParam.schema.json', 'InstallationParamExample.json')
testJsonSchema('InstallationParam.schema.json', 'InstallationParamExample2.json')

testJsonSchema('Error.schema.json', 'ErrorExample.json')
testJsonSchema('Error.schema.json', 'ErrorExample2.json')
testJsonSchema('Error.schema.json', 'ErrorExample3.json')

testJsonSchema('RegistrationRequest.schema.json', 'RegistrationRequestExample.json')
testJsonSchema('RegistrationRequest.schema.json', 'RegistrationRequestExample2.json')

testJsonSchema('RegistrationResponse.schema.json', 'RegistrationResponseExample.json')

testJsonSchema('FrequencyRange.schema.json', 'FrequencyRangeExample.json')

testJsonSchema('SpectrumInquiryRequest.schema.json', 'SpectrumInquiryRequestExample.json')

testJsonSchema('SpectrumInquiryResponse.schema.json', 'SpectrumInquiryResponseExample.json')

testJsonSchema('OperationParam.schema.json', 'OperationParamExample.json')

testJsonSchema('RelinquishmentRequest.schema.json', 'RelinquishmentRequestExample.json')

testJsonSchema('RelinquishmentResponse.schema.json', 'RelinquishmentResponseExample.json')

testJsonSchema('DeregistrationRequest.schema.json', 'DeregistrationRequestExample.json')

testJsonSchema('DeregistrationResponse.schema.json', 'DeregistrationResponseExample.json')

testJsonSchema('GrantRequest.schema.json', 'GrantRequestExample.json')

testJsonSchema('GrantResponse.schema.json', 'GrantResponseExample.json')

testJsonSchema('HeartbeatRequest.schema.json', 'HeartbeatRequestExample.json')

testJsonSchema('HeartbeatResponse.schema.json', 'HeartbeatResponseExample.json')



