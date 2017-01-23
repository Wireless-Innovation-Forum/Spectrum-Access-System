#    Copyright 2017 SAS Project Authors. All Rights Reserved.
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

# This function maps the NLCD classification codes into the NLCD_LAND_CATEGORY
# designations used in WINNF-15-S-0112, R2-SGN-04.
def NlcdLandCategory(nlcd_code):
  if nlcd_code == 22:
    return 'SUBURBAN'

  if nlcd_code == 23 or nlcd_code == 24:
    return 'URBAN'

  # if classification is not 22, 23, or 24, regard it as rural
  return 'RURAL'

# TODO: land/water classification for marking mixed paths.
# (code 11 is "Open Water")
