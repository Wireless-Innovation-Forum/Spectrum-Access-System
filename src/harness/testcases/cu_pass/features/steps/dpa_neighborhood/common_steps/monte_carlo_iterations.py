from behave import *

from testcases.cu_pass.features.environment.hooks import ContextSas


class ContextMonteCarloIterations(ContextSas):
    number_of_iterations: int


@given("{number_of_iterations:Integer} monte carlo iterations")
def step_impl(context: ContextMonteCarloIterations, number_of_iterations: int):
    context.number_of_iterations = number_of_iterations
