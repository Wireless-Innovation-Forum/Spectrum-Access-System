from behave import *

import time
import worldpop.worldpop_client
from pprint import pprint
from worldpop.worldpop_client.api import services_api
from worldpop.worldpop_client.model.geo_json import GeoJson
from worldpop.worldpop_client.model.geo_json_features import GeoJsonFeatures
from worldpop.worldpop_client.model.geometry_object import GeometryObject
from worldpop.worldpop_client.model.stats_response import StatsResponse


@then("the population in the area should be 6,384,440")
def step_impl(context):
    """
    Args:
        context (behave.runner.Context):
    """
    with worldpop.worldpop_client.ApiClient() as api_client:
        # Create an instance of the API class
        api_instance = services_api.ServicesApi(api_client)
        dataset = 'wpgpop'
        year = 2020
        geojson = GeoJson(
            type="FeatureCollection",
            features=[
                GeoJsonFeatures(
                    type="Feature",
                    geometry=GeometryObject(
                        type="Polygon",
                        coordinates=[
                            [
                                3.14,
                            ],
                        ],
                    ),
                    properties={},
                ),
            ],
        )

        try:
            api_response = api_instance.services_stats_get(dataset, year, geojson, key=key)
            pprint(api_response)
        except worldpop.worldpop_client.ApiException as e:
            print("Exception when calling ServicesApi->services_stats_get: %s\n" % e)
