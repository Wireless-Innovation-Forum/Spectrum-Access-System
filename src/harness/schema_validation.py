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

"""Validate repository Draft 4 schemas with explicit local reference resources."""

import json
from pathlib import Path

from jsonschema import Draft4Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT4


def validator_for(schema_path):
  schema_path = Path(schema_path).resolve()

  def normalize_references(value):
    if isinstance(value, list):
      return [normalize_references(item) for item in value]
    if not isinstance(value, dict):
      return value
    normalized = {key: normalize_references(item) for key, item in value.items()}
    ref = normalized.get('$ref', '')
    if ref.startswith('file:') and not ref.startswith('file://'):
      name, separator, fragment = ref[5:].partition('#')
      target = schema_path.parent / name
      if target.is_file():
        # urljoin handles opaque file: URLs differently across Python versions.
        # Resolve the repository's historic references to canonical file URIs.
        normalized['$ref'] = target.resolve().as_uri() + (
            separator + fragment if separator else '')
    return normalized

  resources = []
  for path in schema_path.parent.glob('*.schema.json'):
    with path.open(encoding='utf-8') as stream:
      contents = normalize_references(json.load(stream))
    resource = Resource.from_contents(contents, default_specification=DRAFT4)
    # Existing WINNF schemas use the historic "file:Other.schema.json" form.
    resources.extend((uri, resource) for uri in
                     (path.as_uri(), 'file:' + path.name, path.name))
  registry = Registry().with_resources(resources)
  with schema_path.open(encoding='utf-8') as stream:
    schema = normalize_references(json.load(stream))
  Draft4Validator.check_schema(schema)
  return Draft4Validator(schema, registry=registry)
