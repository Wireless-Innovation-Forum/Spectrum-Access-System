import json
from contextlib import contextmanager

from worldpop_client.api import services_api
from worldpop_client.model.geo_json import GeoJson
from worldpop_client.model.stats_response import StatsResponse

from cu_pass.dpa_calculator.circle_to_geojson_converter import CircleToGeoJsonConverter
from cu_pass.dpa_calculator.point_distributor import AreaCircle
from cu_pass.dpa_calculator.population_retriever.helpers.worldpop_communicator import WorldPopCommunicator


class TaskCreator(WorldPopCommunicator):
    _dataset = 'wpgppop'
    _year = 2020

    def __init__(self, area: AreaCircle):
        self._area = area

    def create(self) -> str:
        with self._api as api_instance:
            api_response: StatsResponse = api_instance.services_stats_get(dataset=self._dataset,
                                                                          year=self._year,
                                                                          geojson=self._geojson_string)
            return api_response.taskid

    @property
    @contextmanager
    def _api(self) -> services_api.ServicesApi:
        with self._worldpop_api_client as api_client:
            yield services_api.ServicesApi(api_client)

    @property
    def _geojson_string(self) -> str:
        return json.dumps(self._geojson.to_dict())

    @property
    def _geojson(self) -> GeoJson:
        return CircleToGeoJsonConverter(area=self._area).convert()
