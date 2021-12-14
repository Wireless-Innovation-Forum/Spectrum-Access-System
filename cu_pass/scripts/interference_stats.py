import re
from os import getenv

import numpy
from dotenv import load_dotenv

load_dotenv()


LOG_FILEPATH = getenv('LOG_FILEPATH')


PARAMETER_VALUE_REGEX = re.compile(r'CBSD 4722 / 4722\n\n\tFound parameter\n\t\tInput: 90\n\t\tValue: (-?[0-9]+(\.[0-9]+)?)')


if __name__ == '__main__':
    log: str
    with open(LOG_FILEPATH) as f:
        log = f.read()

    found_values_all_groups = PARAMETER_VALUE_REGEX.findall(log)
    found_values = [float(found_value[0]) for found_value in found_values_all_groups]
    interference = numpy.percentile(found_values, 95, interpolation='lower')
    interference
