from dataclasses import dataclass

from behave import runner


@dataclass
class ContextSas(runner.Context):
    with_integration: bool
