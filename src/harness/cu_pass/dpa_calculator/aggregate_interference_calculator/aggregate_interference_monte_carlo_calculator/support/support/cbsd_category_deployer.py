import logging
from typing import Dict, Type

from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions, NumberOfApsTypes, PopulationRetrieverTypes
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator import CbsdsCreator, CbsdsWithBearings
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator_access_point import CbsdsCreatorAccessPoint
from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator_user_equipment import CbsdsCreatorUserEquipment
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NUMBER_OF_CBSDS_PER_CATEGORY_TYPE, \
    NumberOfCbsdsCalculator, NumberOfCbsdsCalculatorOptions
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfCbsdsCalculatorShipborne
from cu_pass.dpa_calculator.point_distributor import AreaCircle
from cu_pass.dpa_calculator.population_retriever.population_retriever import PopulationRetriever
from cu_pass.dpa_calculator.population_retriever.population_retriever_census import PopulationRetrieverCensus
from cu_pass.dpa_calculator.population_retriever.population_retriever_region_type import PopulationRetrieverRegionType
from cu_pass.dpa_calculator.utilities import Point


class CbsdCategoryDeployer:
    def __init__(self,
                 center: Point,
                 cbsd_category: CbsdCategories,
                 cbsd_deployment_options: CbsdDeploymentOptions,
                 number_of_cbsds_calculator_options: NumberOfCbsdsCalculatorOptions,
                 is_user_equipment: bool):
        self._center = center
        self._cbsd_category = cbsd_category
        self._cbsd_deployment_options = cbsd_deployment_options
        self._is_user_equipment = is_user_equipment
        self._number_of_cbsds_calculator_options = number_of_cbsds_calculator_options

    def log(self) -> None:
        logging.info(f'\tCBSD Category: {self._cbsd_category}')
        logging.info(f'\t\tNumber of APs: {self._number_of_cbsds_all}')
        logging.info(f'\t\tPopulation retriever: {self._population_retriever_class.__name__}')
        logging.info(f'\t\tNumber of APs calculator: {self._number_of_cbsds_calculator_class.__name__}')

    def deploy(self) -> CbsdsWithBearings:
        cbsds_creator = self._cbsd_creator_class(cbsd_category=self._cbsd_category,
                                                 dpa_zone=self._dpa_test_zone[self._cbsd_category],
                                                 number_of_cbsds=self._number_of_cbsds)
        return cbsds_creator.create()

    @property
    def _number_of_cbsds(self) -> int:
        number_of_cbsds_for_category = self._number_of_cbsds_all.get(self._cbsd_category, {})
        cbds_type = CbsdTypes.UE if self._is_user_equipment else CbsdTypes.AP
        return number_of_cbsds_for_category.get(cbds_type, 0)

    @property
    def _cbsd_creator_class(self) -> Type[CbsdsCreator]:
        return CbsdsCreatorUserEquipment if self._is_user_equipment else CbsdsCreatorAccessPoint

    @cached_property
    def _number_of_cbsds_all(self) -> NUMBER_OF_CBSDS_PER_CATEGORY_TYPE:
        population = self._cbsd_deployment_options.population_override or self._population_retriever_class(area=self._dpa_test_zone[CbsdCategories.B]).retrieve()
        number_of_cbsds_calculator = self._number_of_cbsds_calculator_class(
            center_coordinates=self._center,
            simulation_population=population,
            number_of_cbsds_calculator_options=self._number_of_cbsds_calculator_options)
        return number_of_cbsds_calculator.get_number_of_cbsds()

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

    @property
    def _number_of_cbsds_calculator_class(self) -> Type[NumberOfCbsdsCalculator]:
        map = {
            NumberOfApsTypes.shipborne: NumberOfCbsdsCalculatorShipborne
        }
        return map[self._cbsd_deployment_options.number_of_aps_calculator_type]
