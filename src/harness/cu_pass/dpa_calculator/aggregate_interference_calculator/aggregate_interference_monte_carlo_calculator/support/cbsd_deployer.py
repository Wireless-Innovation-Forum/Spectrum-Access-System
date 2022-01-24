import logging
from typing import List

from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.support.cbsd_category_deployer import \
    CbsdCategoryDeployer
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories

from cu_pass.dpa_calculator.cbsds_creator.cbsds_creator import CbsdsWithBearings
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfCbsdsCalculatorOptions
from cu_pass.dpa_calculator.utilities import Point


class CbsdDeployer:
    def __init__(self,
                 center: Point,
                 is_user_equipment: bool,
                 cbsd_deployment_options: CbsdDeploymentOptions = CbsdDeploymentOptions(),
                 number_of_cbsds_calculator_options: NumberOfCbsdsCalculatorOptions = NumberOfCbsdsCalculatorOptions()):
        self._cbsd_deployment_options = cbsd_deployment_options
        self._center = center
        self._is_user_equipment = is_user_equipment
        self._number_of_cbsds_calculator_options = number_of_cbsds_calculator_options

    def log(self) -> None:
        logging.info('CBSD Deployment:')
        logging.info(f'\tSimulation area radius, category A:'
                     f' {self._cbsd_deployment_options.simulation_distances_in_kilometers[CbsdCategories.A]} kilometers')
        logging.info(f'\tSimulation area radius, category B: '
                     f'{self._cbsd_deployment_options.simulation_distances_in_kilometers[CbsdCategories.B]} kilometers')
        for deployer in self._cbsd_category_deployers:
            deployer.log()
        logging.info('')

    def deploy(self) -> CbsdsWithBearings:
        category_deployments = [deployer.deploy() for deployer in self._cbsd_category_deployers]
        flattened = CbsdsWithBearings(
            bearings=[],
            cbsds=[]
        )
        for cbsds_with_bearings in category_deployments:
            flattened.bearings.extend(cbsds_with_bearings.bearings)
            flattened.cbsds.extend(cbsds_with_bearings.cbsds)
        return flattened

    @cached_property
    def _cbsd_category_deployers(self) -> List[CbsdCategoryDeployer]:
        return [CbsdCategoryDeployer(center=self._center,
                                     cbsd_category=cbsd_category,
                                     cbsd_deployment_options=self._cbsd_deployment_options,
                                     number_of_cbsds_calculator_options=self._number_of_cbsds_calculator_options,
                                     is_user_equipment=self._is_user_equipment)
                for cbsd_category in CbsdCategories]
