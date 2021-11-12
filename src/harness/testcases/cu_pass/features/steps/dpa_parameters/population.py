from dataclasses import dataclass

from behave import *

import worldpop_client
from pprint import pprint
from worldpop_client.api import services_api

from dpa_calculator.circle_to_geojson_converter import CircleToGeoJsonConverter
from testcases.cu_pass.features.steps.dpa_parameters.area import ContextArea


@dataclass
class ContextPopulation(ContextArea):
    pass


@then("the population in the area should be 6,384,440")
def step_impl(context: ContextPopulation):
    """
    Args:
        context (behave.runner.Context):
    """
    with worldpop_client.ApiClient() as api_client:
        api_instance = services_api.ServicesApi(api_client)
        dataset = 'wpgppop'
        year = 2020
        geojson = CircleToGeoJsonConverter(area=context.area).convert()

        try:
            api_response = api_instance.services_stats_get(dataset=dataset, year=year, geojson=geojson)
            pprint(api_response)
        except worldpop_client.ApiException as e:
            print("Exception when calling ServicesApi->services_stats_get: %s\n" % e)
