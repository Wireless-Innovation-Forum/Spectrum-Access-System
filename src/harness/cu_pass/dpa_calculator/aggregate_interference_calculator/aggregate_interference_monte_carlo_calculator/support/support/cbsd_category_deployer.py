from typing import Dict, Type

from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions, PopulationRetrieverTypes
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.cbsds_creator.cbsds_generator import CbsdsGenerator, CbsdsWithBearings
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NUMBER_OF_CBSDS_PER_CATEGORY_TYPE, \
    NumberOfApsTypes, NumberOfCbsdsCalculator
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfCbsdsCalculatorShipborne
from cu_pass.dpa_calculator.point_distributor import AreaCircle
from cu_pass.dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from cu_pass.dpa_calculator.population_retriever.population_retriever_census import PopulationRetrieverCensus
from cu_pass.dpa_calculator.population_retriever.population_retriever_region_type import PopulationRetrieverRegionType
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger, Point


class CbsdCategoryDeployer:
    def __init__(self,
                 center: Point,
                 cbsd_category: CbsdCategories,
                 cbsd_deployment_options: CbsdDeploymentOptions,
                 is_user_equipment: bool):
        self._center = center
        self._cbsd_category = cbsd_category
        self._cbsd_deployment_options = cbsd_deployment_options
        self._is_user_equipment = is_user_equipment
        self._number_of_cbsds_calculator_options = self._cbsd_deployment_options.number_of_cbsds_calculator_options

    def log(self) -> None:
        logger = get_dpa_calculator_logger()
        logger.info(f'\t\tCBSD Category: {self._cbsd_category}')
        logger.info(f'\t\t\tPopulation: {self._population}')
        logger.info(f'\t\t\tNumber of {self._cbsd_type.name}s: {self._number_of_cbsds}')
        logger.info(f'\t\t\tNumber of UEs per AP: '
                    f'{self._number_of_cbsds_calculator.get_number_of_users_served_per_ap(category=self._cbsd_category)}')
        logger.info(f'\t\t\tPopulation retriever: {self._population_retriever_class.__name__}')
        logger.info(f'\t\t\tNumber of APs calculator: {self._number_of_cbsds_calculator_class.__name__}')

    def deploy(self) -> CbsdsWithBearings:
        self.log()
        category_simulation_zone = self._dpa_test_zone[self._cbsd_category]
        if category_simulation_zone.radius_in_kilometers:
            cbsds_creator = CbsdsGenerator(cbsd_category=self._cbsd_category,
                                           cbsd_type=self._cbsd_type,
                                           dpa_zone=category_simulation_zone,
                                           number_of_cbsds=self._number_of_cbsds)
            return cbsds_creator.create()
        else:
            return CbsdsWithBearings(
                bearings=[],
                cbsds=[]
            )

    @property
    def _number_of_cbsds(self) -> int:
        number_of_cbsds_for_category = self._number_of_cbsds_all.get(self._cbsd_category, {})
        return number_of_cbsds_for_category.get(self._cbsd_type, 0)

    @property
    def _cbsd_type(self) -> CbsdTypes:
        return CbsdTypes.UE if self._is_user_equipment else CbsdTypes.AP

    @cached_property
    def _number_of_cbsds_all(self) -> NUMBER_OF_CBSDS_PER_CATEGORY_TYPE:
        return self._number_of_cbsds_calculator.get_number_of_cbsds()

    @property
    def _number_of_cbsds_calculator(self) -> NumberOfCbsdsCalculator:
        return self._number_of_cbsds_calculator_class(
            center_coordinates=self._center,
            simulation_population=self._population,
            number_of_cbsds_calculator_options=self._number_of_cbsds_calculator_options)

    @property
    def _number_of_cbsds_calculator_class(self) -> Type[NumberOfCbsdsCalculator]:
        map = {
            NumberOfApsTypes.shipborne: NumberOfCbsdsCalculatorShipborne
        }
        return map[self._number_of_cbsds_calculator_options.number_of_cbsds_calculator_type]

    @cached_property
    def _population(self) -> int:
        max_area = self._dpa_test_zone[self._cbsd_category]
        population = self._cbsd_deployment_options.population_override \
                     or self._population_retriever_class(area=max_area).retrieve()
        return population

    @property
    def _dpa_test_zone(self) -> Dict[CbsdCategories, AreaCircle]:
        return {cbsd_category: AreaCircle(
            center_coordinates=self._center,
            radius_in_kilometers=self._cbsd_deployment_options.simulation_distances_in_kilometers[cbsd_category]
        ) for cbsd_category in CbsdCategories}

    @property
    def _population_retriever_class(self) -> Type[PopulationRetriever]:
        map = {
            PopulationRetrieverTypes.census: PopulationRetrieverCensus,
            PopulationRetrieverTypes.region_type: PopulationRetrieverRegionType
        }
        return map[self._cbsd_deployment_options.population_retriever_type]
