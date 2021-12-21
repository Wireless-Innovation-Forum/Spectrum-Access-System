from testcases.cu_pass.features.environment.utilities import sanitize_multiline_expected_string

EXPECTED_LOG_OUTPUT = sanitize_multiline_expected_string("""Inputs:
    DPA Name: HATCREEK
    Number of APs: 0
    Number of iterations: 1
    Simulation area radius: 2 kilometers
    Aggregate interference calculator: AggregateInterferenceCalculatorNtia
    Population retriever: PopulationRetrieverCensus
    Number of APs calculator: NumberOfApsCalculatorShipborne

Monte Carlo iteration 1

    Found parameter
        Input: 0
        Value: -inf


    Found parameter
        Input: 0
        Value: -inf


Results for APs:
    50th percentile: 0
    95th percentile: 0
    Standard Deviation: 0
    Minimum: 0
    Maximum: 0

Results for UEs:
    50th percentile: 0
    95th percentile: 0
    Standard Deviation: 0
    Minimum: 0
    Maximum: 0

Final results:
    Distance: 0
    Interference: -inf
    AP Distance: 0
    UE Distance: 0
    AP Interference: -inf
    UE Interference: -inf
""")
