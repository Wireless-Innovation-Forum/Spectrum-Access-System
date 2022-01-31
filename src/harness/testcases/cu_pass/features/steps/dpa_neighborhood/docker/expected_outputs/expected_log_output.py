from testcases.cu_pass.features.helpers.utilities import sanitize_multiline_expected_string

EXPECTED_LOG_OUTPUT = sanitize_multiline_expected_string("""Inputs:
	DPA Name: HATCREEK
	Number of iterations: 1
	Aggregate interference calculator: AggregateInterferenceCalculatorWinnforum

Monte Carlo iteration 1
	CBSD Deployment:
		CBSD Type: CbsdTypes.AP
		Simulation area radius, category A: 0 kilometers
		Simulation area radius, category B: 0 kilometers
		CBSD Category: CbsdCategories.A
			Population: 0
			Number of APs: 0
			Number of UEs per AP: 3
			Population retriever: PopulationRetrieverCensus
			Number of APs calculator: NumberOfCbsdsCalculatorShipborne
		CBSD Category: CbsdCategories.B
			Population: 0
			Number of APs: 0
			Number of UEs per AP: 500
			Population retriever: PopulationRetrieverCensus
			Number of APs calculator: NumberOfCbsdsCalculatorShipborne

	Found parameter
		Input: 0
		Value: -1000

	CBSD Deployment:
		CBSD Type: CbsdTypes.UE
		Simulation area radius, category A: 0 kilometers
		Simulation area radius, category B: 0 kilometers
		CBSD Category: CbsdCategories.A
			Population: 0
			Number of UEs: 0
			Number of UEs per AP: 3
			Population retriever: PopulationRetrieverCensus
			Number of APs calculator: NumberOfCbsdsCalculatorShipborne
		CBSD Category: CbsdCategories.B
			Population: 0
			Number of UEs: 0
			Number of UEs per AP: 500
			Population retriever: PopulationRetrieverCensus
			Number of APs calculator: NumberOfCbsdsCalculatorShipborne

	Found parameter
		Input: 0
		Value: -1000


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
	Interference: -1000.0
	AP Distance: 0
	UE Distance: 0
	AP Interference: -1000.0
	UE Interference: -1000.0
""")
