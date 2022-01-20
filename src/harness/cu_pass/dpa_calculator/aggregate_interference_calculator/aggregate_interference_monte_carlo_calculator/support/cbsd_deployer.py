import logging
from dataclasses import dataclass
from enum import auto, Enum
from typing import Optional, Type

from cached_property import cached_property

from cu_pass.dpa_calculator.cbsd.cbsd_getter.cbsd_getter import CbsdCategories
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator import CbsdsWithBearings
from cu_pass.dpa_calculator.cbsds_creator.utilities import get_cbsds_creator
from cu_pass.dpa_calculator.dpa.dpa import Dpa
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfApsCalculator
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator_ground_based import NumberOfApsCalculatorGroundBased
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfApsCalculatorShipborne
from cu_pass.dpa_calculator.point_distributor import AreaCircle
from cu_pass.dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from cu_pass.dpa_calculator.population_retriever.population_retriever_census import PopulationRetrieverCensus
from cu_pass.dpa_calculator.population_retriever.population_retriever_region_type import PopulationRetrieverRegionType
from cu_pass.dpa_calculator.utilities import get_dpa_center

DEFAULT_SIMULATION_RADIUS_IN_KILOMETERS = 500


class NumberOfApsTypes(Enum):
    ground_based = auto()
    shipborne = auto()


class PopulationRetrieverTypes(Enum):
    census = auto()
    region_type = auto()


@dataclass
class CbsdDeploymentOptions:
    number_of_aps: Optional[int] = None
    simulation_area_radius_in_kilometers: int = DEFAULT_SIMULATION_RADIUS_IN_KILOMETERS
    population_retriever_type: PopulationRetrieverTypes = PopulationRetrieverTypes.census
    number_of_aps_calculator_type: NumberOfApsTypes = NumberOfApsTypes.shipborne


class CbsdDeployer:
    def __init__(self, dpa: Dpa, is_user_equipment: bool, cbsd_deployment_options: CbsdDeploymentOptions = CbsdDeploymentOptions):
        self._cbsd_deployment_options = cbsd_deployment_options
        self._dpa = dpa
        self._is_user_equipment = is_user_equipment

    def log(self) -> None:
        logging.info('CBSD Deployment:')
        logging.info(f'\tNumber of APs: {self._number_of_aps}')
        logging.info(f'\tSimulation area radius: {self._cbsd_deployment_options.simulation_area_radius_in_kilometers} kilometers')
        logging.info(f'\tPopulation retriever: {self._population_retriever_class.__name__}')
        logging.info(f'\tNumber of APs calculator: {self._number_of_aps_calculator_class.__name__}')
        logging.info('')

    def deploy(self) -> CbsdsWithBearings:
        cbsds_creator = get_cbsds_creator(cbsd_category=CbsdCategories.A,
                                          dpa_zone=self._dpa_test_zone,
                                          is_user_equipment=self._is_user_equipment,
                                          number_of_aps=self._number_of_aps)
        cbsds = cbsds_creator.create()
        return cbsds

    @cached_property
    def _number_of_aps(self) -> int:
        if self._cbsd_deployment_options.number_of_aps is not None:
            return self._cbsd_deployment_options.number_of_aps
        population = self._population_retriever_class(area=self._dpa_test_zone).retrieve()
        return self._number_of_aps_calculator_class(center_coordinates=self._dpa_test_zone.center_coordinates,
                                                    simulation_population=population).get_number_of_aps()

    @property
    def _population_retriever_class(self) -> Type[PopulationRetriever]:
        map = {
            PopulationRetrieverTypes.census: PopulationRetrieverCensus,
            PopulationRetrieverTypes.region_type: PopulationRetrieverRegionType
        }
        return map[self._cbsd_deployment_options.population_retriever_type]

    @property
    def _dpa_test_zone(self) -> AreaCircle:
        return AreaCircle(
            center_coordinates=get_dpa_center(dpa=self._dpa),
            radius_in_kilometers=self._cbsd_deployment_options.simulation_area_radius_in_kilometers
        )

    @property
    def _number_of_aps_calculator_class(self) -> Type[NumberOfApsCalculator]:
        map = {
            NumberOfApsTypes.ground_based: NumberOfApsCalculatorGroundBased,
            NumberOfApsTypes.shipborne: NumberOfApsCalculatorShipborne
        }
        return map[self._cbsd_deployment_options.number_of_aps_calculator_type]
