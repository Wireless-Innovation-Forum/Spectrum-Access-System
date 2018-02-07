import json
import os

import ppa_ref_model

ppa_ref_model.PpaCreationModel([json.load(open(os.path.join('test_data', 'device_a.json')))])
