from math import inf
from typing import List

from behave import *

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.aggregate_interference_monte_carlo_calculator import \
    AggregateInterferenceMonteCarloCalculator, AggregateInterferenceMonteCarloResults, AggregateInterferenceTypes, \
    DEFAULT_AGGREGATE_INTERFERENCE_TYPE
from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_monte_carlo_calculator.support.definitions import \
    CbsdDeploymentOptions, PopulationRetrieverTypes
from cu_pass.dpa_calculator.constants import ALL_REGION_TYPES
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator import NumberOfApsTypes
from cu_pass.dpa_calculator.cbsd.cbsd import CbsdCategories, CbsdTypes
from cu_pass.dpa_calculator.number_of_aps.number_of_aps_calculator_shipborne import NumberOfCbsdsCalculatorShipborne
from reference_models.dpa.move_list import MINIMUM_INTERFERENCE_WINNFORUM
from testcases.cu_pass.dpa_calculator.features.helpers.utilities import get_expected_output_content, get_logging_file_handler, \
    sanitize_output_log
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.dpa import ContextDpa
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.monte_carlo_iterations import \
    ContextMonteCarloIterations
from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.common_steps.region_type import assign_arbitrary_dpa

use_step_matcher('parse')


class ContextNeighborhood(ContextDpa, ContextMonteCarloIterations):
    aggregate_interference_calculator_type: AggregateInterferenceTypes
    cbsd_deployment_options: CbsdDeploymentOptions
    include_ue_runs: bool
    neighborhood_categories: List[CbsdCategories]
    number_of_iterations: int
    result: AggregateInterferenceMonteCarloResults


@given("{organization} interference")
def step_impl(context: ContextNeighborhood, organization: str):
    map = {
        'NTIA_2015': AggregateInterferenceTypes.NTIA,
        'WinnForum': AggregateInterferenceTypes.WinnForum
    }
    context.aggregate_interference_calculator_type = map[organization]


@given("population by {population_type}")
def step_impl(context: ContextNeighborhood, population_type: str):
    map = {
        'census radius': PopulationRetrieverTypes.census,
        'region type': PopulationRetrieverTypes.region_type
    }
    context.cbsd_deployment_options.population_retriever_type = map[population_type]


@given("number of APs using {number_of_aps_type} analysis")
def step_impl(context: ContextNeighborhood, number_of_aps_type: str):
    map = {
        'ground based': NumberOfApsTypes.ground_based,
        'shipborne': NumberOfApsTypes.shipborne
    }
    context.cbsd_deployment_options.number_of_aps_calculator_class = map[number_of_aps_type]


@given("{number_of_ues:Integer} category {cbsd_category:CbsdCategory} UEs")
def set_number_of_ues(context: ContextNeighborhood, number_of_ues: int, cbsd_category: CbsdCategories):
    number_of_ues_to_simulate_one_ap = number_of_ues
    population = 1 / NumberOfCbsdsCalculatorShipborne._channel_scaling_factor / NumberOfCbsdsCalculatorShipborne._market_penetration_factor
    context.cbsd_deployment_options.population_override = population
    context.cbsd_deployment_options.number_of_cbsds_calculator_options.fraction_of_users_served_by_aps[cbsd_category] = {
        region_type: number_of_ues for region_type in ALL_REGION_TYPES
    }
    context.cbsd_deployment_options.number_of_cbsds_calculator_options.number_of_ues_per_ap_by_region_type[cbsd_category] = {
        region_type: number_of_ues_to_simulate_one_ap for region_type in ALL_REGION_TYPES
    }


@given("UE runs are included")
def step_impl(context: ContextNeighborhood):
    context.include_ue_runs = True


@given("neighborhood categories {neighborhood_categories:CbsdCategoryList}")
def step_impl(context: ContextNeighborhood, neighborhood_categories: List[CbsdCategories]):
    context.neighborhood_categories = neighborhood_categories


@when("the neighborhood radius is calculated")
def step_impl(context: ContextNeighborhood):
    """
    Args:
        context (behave.runner.Context):
    """
    if not hasattr(context, 'dpa'):
        assign_arbitrary_dpa(context=context)
    if not hasattr(context, 'aggregate_interference_calculator_type'):
        context.aggregate_interference_calculator_type = DEFAULT_AGGREGATE_INTERFERENCE_TYPE
    simulation_results = AggregateInterferenceMonteCarloCalculator(
        dpa=context.dpa,
        aggregate_interference_calculator_type=context.aggregate_interference_calculator_type,
        number_of_iterations=getattr(context, 'number_of_iterations', 1),
        cbsd_deployment_options=context.cbsd_deployment_options,
        include_ue_runs=context.include_ue_runs,
        neighborhood_categories=context.neighborhood_categories
    ).simulate()
    simulation_results.log()
    context.result = simulation_results


@then("the resulting category {cbsd_category:CbsdCategory} {cbsd_type:CbsdType} distance should be {expected_distance:Integer}")
def step_impl(context: ContextNeighborhood, cbsd_category: CbsdCategories, cbsd_type: CbsdTypes, expected_distance: int):
    distance = context.result.distance[cbsd_type][cbsd_category]
    assert distance == expected_distance, f'{distance} != {expected_distance}'


@then("the resulting category {cbsd_category:CbsdCategory} {cbsd_type:CbsdType} interference should be {expected_interference:Number}")
def step_impl(context: ContextNeighborhood, cbsd_category: CbsdCategories, cbsd_type: CbsdTypes, expected_interference: float):
    if expected_interference == -inf and context.aggregate_interference_calculator_type == AggregateInterferenceTypes.WinnForum:
        expected_interference = MINIMUM_INTERFERENCE_WINNFORUM
    interference = context.result.interference[cbsd_type][cbsd_category]
    assert interference == expected_interference, f'{interference} != {expected_interference}'


@then("the resulting category {cbsd_category:CbsdCategory} {cbsd_type:CbsdType} distance should not exist")
def step_impl(context: ContextNeighborhood, cbsd_category: CbsdCategories, cbsd_type: CbsdTypes):
    assert cbsd_category not in context.result.distance[cbsd_type], f'{cbsd_type} found in results.'


@then("the resulting category {cbsd_category:CbsdCategory} {cbsd_type:CbsdType} interference should not exist")
def step_impl(context: ContextNeighborhood, cbsd_category: CbsdCategories, cbsd_type: CbsdTypes):
    assert cbsd_category not in context.result.interference[cbsd_type], f'{cbsd_type} found in results.'


@then("the resulting {cbsd_type:CbsdType} distance should not exist")
def step_impl(context: ContextNeighborhood, cbsd_type: CbsdTypes):
    assert cbsd_type not in context.result.distance, f'{cbsd_type} found in results.'


@then("the resulting {cbsd_type:CbsdType} interference should not exist")
def step_impl(context: ContextNeighborhood, cbsd_type: CbsdTypes):
    assert cbsd_type not in context.result.interference, f'{cbsd_type} found in results.'


@then("it should run without error")
def step_impl(context: ContextNeighborhood):
    pass


@then("the output log should be")
def step_impl(context: ContextNeighborhood):
    expected_content = get_expected_output_content(context=context)
    output_log_filepath = get_logging_file_handler().baseFilename
    output_content = sanitize_output_log(log_filepath=output_log_filepath)
    assert output_content == expected_content
