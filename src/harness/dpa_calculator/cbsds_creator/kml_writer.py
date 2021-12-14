from pathlib import Path
from typing import List, Optional

from dpa_calculator.cbsd.cbsd import Cbsd
from dpa_calculator.utilities import get_distance_between_two_points, Point


class KmlWriter:
    def __init__(self, cbsds: List[Cbsd], output_filepath: Path, distance_to_exclude: int = 0, dpa_center: Optional[Point] = None):
        self._cbsds = cbsds
        self._distance_to_exclude = distance_to_exclude
        self._dpa_center = dpa_center
        self._output_filepath = output_filepath

    def write(self) -> None:
        with open(self._output_filepath, 'w') as file:
            file.write(self._header)
            file.write(self._placemarks)
            file.write(self._footer)

    @property
    def _header(self) -> str:
        return '''
            <?xml version="1.0" encoding="UTF-8"?>
                <kml xmlns="http://www.opengis.net/kml/2.2">
                    <Folder>
                        <name>KML Output</name>
                            <visibility>1</visibility>
        '''

    @property
    def _placemarks(self) -> str:
        coordinates = (f'''
            <Placemark>
                {self._placemark_color(cbsd=cbsd)}
                <Point>
                    <coordinates>{cbsd.location.longitude},{cbsd.location.latitude}</coordinates>
                </Point>
            </Placemark>
        ''' for cbsd in self._cbsds)
        return ''.join(coordinates)

    def _placemark_color(self, cbsd: Cbsd) -> str:
        distance = get_distance_between_two_points(point1=self._dpa_center, point2=cbsd.location)
        return '''
        <Style>
            <IconStyle>
                <scale>1</scale>
                <color>ff0000ff</color>
                <Icon>
                    <href>http://maps.google.com/mapfiles/kml/paddle/wht-blank.png</href>
                </Icon>
            </IconStyle>
        </Style>''' if distance <= self._distance_to_exclude else ''

    @property
    def _footer(self) -> str:
        return '''
            </Folder>
                </kml>
        '''
