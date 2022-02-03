from behave import *

from testcases.cu_pass.dpa_calculator.features.steps.dpa_neighborhood.environment.contexts.context_monte_carlo_iterations import \
    ContextMonteCarloIterations


@given("{number_of_iterations:Integer} monte carlo iterations")
def step_impl(context: ContextMonteCarloIterations, number_of_iterations: int):
    context.number_of_iterations = number_of_iterations
