from typing import Dict

from cu_pass.dpa_calculator.aggregate_interference_calculator.configuration.configuration import Configuration


CONFIGURATION_DPA_CALCULATOR_NAME = 'DPA_CALCULATOR'


class ConfigurationManager:
    _configurations: Dict[str, Configuration] = {}

    @staticmethod
    def get_configuration(name: str = CONFIGURATION_DPA_CALCULATOR_NAME) -> Configuration:
        configuration = ConfigurationManager._configurations.get(name, Configuration())
        ConfigurationManager._configurations[name] = configuration
        return configuration

    @staticmethod
    def set_configuration(configuration: Configuration, name: str = CONFIGURATION_DPA_CALCULATOR_NAME) -> None:
        ConfigurationManager._configurations[name] = configuration
