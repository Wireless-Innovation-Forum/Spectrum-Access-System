import json
import re
from typing import Dict, List

from behave import *

from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.constants import REGION_TYPE_RURAL
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.docker.output_files import get_uploaded_result_content
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.docker.utilities import get_uploaded_log_content
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.contexts.context_docker import ContextDocker

use_step_matcher("parse")


@given("DPA name {dpa:Dpa}")
def step_impl(context: ContextDocker, dpa: str):
    context.dpa = dpa


@given("a beamwidth of {beamwidth:Number}")
def step_impl(context: ContextDocker, beamwidth: float):
    context.beamwidth = beamwidth


@given("a category {cbsd_category:CbsdCategory} EIRP distribution of {distributions:FractionalDistribution}")
def step_impl(context: ContextDocker, cbsd_category: CbsdCategories, distributions: List[FractionalDistribution]):
    context.eirp_distribution = {
        CbsdTypes.AP: {
            cbsd_category: {
                REGION_TYPE_RURAL: {
                    True: distributions[0],
                    False: distributions[0]
                }
            }
        }
    }


@then("\"{expected_log_portion}\" should be in the output log")
def step_impl(context: ContextDocker, expected_log_portion: str):
    output_content = get_uploaded_log_content(bucket_name=context.s3_bucket)
    expected_log_portion_sanitized = expected_log_portion.replace('[', '\[').replace(']', '\]')
    assert re.search(expected_log_portion_sanitized, output_content)


@then("the results should{not_included}include UE results")
def step_impl(context: ContextDocker, not_included: str):
    results = _inflate_results(context)
    ue_distance_exists = 'CbsdTypes.UE' in results['distance']
    if not_included.strip():
        assert not ue_distance_exists
    else:
        assert ue_distance_exists


@then("the results should{not_included}include category {cbsd_category:CbsdCategory} results")
def step_impl(context: ContextDocker, not_included: str, cbsd_category: CbsdCategories):
    results = _inflate_results(context)
    category_exists = str(cbsd_category) in results['distance'][str(CbsdTypes.AP)]
    if not_included.strip():
        assert not category_exists
    else:
        assert category_exists


def _inflate_results(context: ContextDocker) -> Dict:
    object_name = f'{context.s3_output_directory}/__RUNTIME__/result.json'
    output_content = get_uploaded_result_content(bucket_name=context.s3_bucket, object_name=object_name)
    return json.loads(output_content)
