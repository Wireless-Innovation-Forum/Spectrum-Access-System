from typing import List, Tuple

from cu_pass.dpa_calculator.aggregate_interference_calculator.aggregate_interference_calculator import \
    AggregateInterferenceCalculator
from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.move_list import HIGH_FREQ_COCH, LOW_FREQ_COCH

COCHANNEL_BANDWIDTH = 10
HERTZ_IN_MEGAHERTZ = 1e6


class AggregateInterferenceCalculatorWinnforum(AggregateInterferenceCalculator):
    def calculate(self, minimum_distance: float) -> float:
        self._dpa.neighbor_distances = (150, minimum_distance, 0, 0)
        self._dpa.SetGrantsFromList(grants=self._grants_with_inband_frequences)
        self._dpa.ComputeMoveLists()
        return self._dpa.CalcKeepListInterference(channel=self._first_inband_channel)[0]

    @property
    def _grants_with_inband_frequences(self) -> List[CbsdGrantInfo]:
        return [grant._replace(low_frequency=self._low_inband_frequency,
                               high_frequency=self._high_inband_frequency)
                for index, grant in enumerate(self._grants)]

    @property
    def _high_inband_frequency(self) -> float:
        return self._frequency_in_hertz(self._low_inband_frequency + COCHANNEL_BANDWIDTH)

    @property
    def _low_inband_frequency(self) -> float:
        return self._frequency_in_hertz(self._first_inband_channel[0])

    @property
    def _first_inband_channel(self) -> Tuple[float, float]:
        return next(channel for channel in self._dpa._channels if self._channel_is_cochannel(channel))

    def _channel_is_cochannel(self, channel: Tuple[float, float]) -> bool:
        return self._frequency_in_hertz(channel[0]) >= LOW_FREQ_COCH and self._frequency_in_hertz(channel[1]) <= HIGH_FREQ_COCH

    @staticmethod
    def _frequency_in_hertz(frequency_in_megahertz: float) -> float:
        return frequency_in_megahertz * HERTZ_IN_MEGAHERTZ

    @property
    def _grants(self) -> List[CbsdGrantInfo]:
        return [cbsd.to_grant() for cbsd in self._cbsds]
