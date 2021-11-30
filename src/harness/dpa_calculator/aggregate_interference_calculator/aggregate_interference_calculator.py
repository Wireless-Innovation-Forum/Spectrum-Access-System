from abc import ABC, abstractmethod
from typing import List, Tuple

from reference_models.common.data import CbsdGrantInfo
from reference_models.dpa.dpa_mgr import Dpa
from reference_models.dpa.move_list import HIGH_FREQ_COCH, LOW_FREQ_COCH

COCHANNEL_BANDWIDTH = 10
HERTZ_IN_MEGAHERTZ = 1e6


class AggregateInterferenceCalculator(ABC):
    def __init__(self, dpa: Dpa, grants: List[CbsdGrantInfo]):
        self._dpa = dpa
        self._grants = grants

    @abstractmethod
    def calculate(self) -> float:
        raise NotImplementedError

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
