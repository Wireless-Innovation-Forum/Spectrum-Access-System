import re
from abc import ABC, abstractmethod
from typing import List

import parse

from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution import \
    FractionalDistribution
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution_normal import \
    FractionalDistributionNormal
from cu_pass.dpa_calculator.helpers.list_distributor.fractional_distribution.fractional_distribution_uniform import \
    FractionalDistributionUniform
from cu_pass.dpa_calculator.helpers.parsers import NUMBER_REGEX, parse_number, parse_number_range, RANGE_REGEX

PERCENTAGE_DELIMITER = ':'
DISTRIBUTION_REGEX_UNIFORM = rf'({NUMBER_REGEX}%{PERCENTAGE_DELIMITER} {RANGE_REGEX},? ?)'
DISTRIBUTION_REGEX_NORMAL = rf'({NUMBER_REGEX}%{PERCENTAGE_DELIMITER} PDF \[{RANGE_REGEX}\] mean {NUMBER_REGEX} std {NUMBER_REGEX},? ?)'
DISTRIBUTION_LIST_REGEX = rf'({DISTRIBUTION_REGEX_UNIFORM}|{DISTRIBUTION_REGEX_NORMAL})+'


class DistributionParser(ABC):
    @abstractmethod
    def parse(self, distribution_text: str) -> FractionalDistribution:
        pass

    @property
    @abstractmethod
    def distribution_regex(self) -> str:
        pass


class DistributionParserUniform(DistributionParser):
    @property
    def distribution_regex(self) -> str:
        return DISTRIBUTION_REGEX_UNIFORM

    def parse(self, distribution_text: str) -> FractionalDistributionUniform:
        percentage_text, range_text = distribution_text[0].split(PERCENTAGE_DELIMITER)
        range = parse_number_range(text=range_text)
        return FractionalDistributionUniform(
            range_maximum=range.high,
            range_minimum=range.low,
            fraction=parse_number(text=percentage_text) / 100,
        )


class DistributionParserNormal(DistributionParser):
    @property
    def distribution_regex(self) -> str:
        return DISTRIBUTION_REGEX_NORMAL

    def parse(self, distribution_text: str) -> FractionalDistributionNormal:
        percentage_text, range_text = distribution_text[0].split(PERCENTAGE_DELIMITER)
        range = parse_number_range(text=range_text)
        mean_text = re.compile(fr'mean {NUMBER_REGEX}').search(range_text)[0]
        standard_deviation_text = re.compile(fr'std {NUMBER_REGEX}').search(range_text)[0]
        return FractionalDistributionNormal(
            range_maximum=range.high,
            range_minimum=range.low,
            fraction=parse_number(text=percentage_text) / 100,
            mean=parse_number(mean_text),
            standard_deviation=parse_number(standard_deviation_text)
        )


class DistributionParserMain:
    def __init__(self, text: str):
        self._text = text

    def parse(self) -> List[FractionalDistribution]:
        for distribution_parser in (DistributionParserUniform(), DistributionParserNormal()):
            distribution_texts = self._get_distribution_texts(distribution_regex=distribution_parser.distribution_regex)
            if distribution_texts:
                return [distribution_parser.parse(distribution_text=distribution_text)
                        for distribution_text in distribution_texts]
        return []

    def _get_distribution_texts(self, distribution_regex: str) -> List[str]:
        return re.compile(distribution_regex).findall(self._text)


@parse.with_pattern(DISTRIBUTION_LIST_REGEX)
def parse_fractional_distribution(text: str) -> List[FractionalDistribution]:
    return DistributionParserMain(text=text).parse()
