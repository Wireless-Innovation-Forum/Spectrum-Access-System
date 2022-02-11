from enum import Enum
from pathlib import Path
from typing import List

from cu_pass.dpa_calculator.cbsd.cbsd import Cbsd


class KmlColor(Enum):
    RED = 'http://www.google.com/intl/en_us/mapfiles/ms/icons/red-dot.png'
    BLUE = 'http://www.google.com/intl/en_us/mapfiles/ms/icons/blue-dot.png'
    WHITE = 'http://maps.google.com/mapfiles/kml/paddle/wht-blank.png'


class KmlWriter:
    def __init__(self,
                 cbsds: List[Cbsd],
                 output_filepath: Path,
                 color: KmlColor = KmlColor.BLUE):
        self._cbsds = cbsds
        self._color = color
        self._output_filepath = output_filepath

    def write(self) -> None:
        with open(self._output_filepath, 'w') as file:
            file.write(self._header)
            file.write(self._placemarks)
            file.write(self._footer)

    @property
    def _header(self) -> str:
        return f'''
            <?xml version="1.0" encoding="UTF-8"?>
                <kml xmlns="http://www.opengis.net/kml/2.2">
                    <Document>
                        <name>KML Output</name>
                        {self._color_list}
        '''

    @property
    def _color_list(self) -> str:
        return '\n'.join([self._placemark_color(color=color) for color in KmlColor])

    def _placemark_color(self, color: KmlColor) -> str:
        return f'''
        <Style id="{color.name}">
            <IconStyle>
                <Icon>
                    <href>{color.value}</href>
                </Icon>
            </IconStyle>
        </Style>'''

    @property
    def _placemarks(self) -> str:
        coordinates = (f'''
            <Placemark>
                <styleUrl>#{self._color.name}</styleUrl>
                <Point>
                    <coordinates>{cbsd.location.longitude},{cbsd.location.latitude}</coordinates>
                </Point>
            </Placemark>
        ''' for cbsd in self._cbsds)
        return ''.join(coordinates)

    @property
    def _footer(self) -> str:
        return '''
            </Document>
                </kml>
        '''
