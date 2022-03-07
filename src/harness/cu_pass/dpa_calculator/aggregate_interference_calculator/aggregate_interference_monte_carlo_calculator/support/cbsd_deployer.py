from typing import List

from cached_property import cached_property

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.support.cbsd_category_deployer import \
    CbsdCategoryDeployer
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes

from cu_pass.dpa_calculator.cbsds_creator.cbsds_generator import CbsdsWithBearings
from cu_pass.dpa_calculator.utilities import get_dpa_calculator_logger, Point


class CbsdDeployer:
    def __init__(self,
                 center: Point,
                 is_user_equipment: bool,
                 cbsd_deployment_options: CbsdDeploymentOptions = CbsdDeploymentOptions()):
        self._cbsd_deployment_options = cbsd_deployment_options
        self._center = center
        self._is_user_equipment = is_user_equipment

    def log(self) -> None:
        logger = get_dpa_calculator_logger()
        logger.info('\tCBSD Deployment:')
        logger.info(f'\t\tCBSD Type: {self._cbsd_type}')
        logger.info(f'\t\tSimulation area radius, category A:'
                    f' {self._cbsd_deployment_options.simulation_distances_in_kilometers[CbsdCategories.A]} kilometers')
        logger.info(f'\t\tSimulation area radius, category B: '
                    f'{self._cbsd_deployment_options.simulation_distances_in_kilometers[CbsdCategories.B]} kilometers')

    @property
    def _cbsd_type(self) -> CbsdTypes:
        return CbsdTypes.UE if self._is_user_equipment else CbsdTypes.AP

    def deploy(self) -> CbsdsWithBearings:
        self.log()
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
                                     is_user_equipment=self._is_user_equipment)
                for cbsd_category in CbsdCategories]
