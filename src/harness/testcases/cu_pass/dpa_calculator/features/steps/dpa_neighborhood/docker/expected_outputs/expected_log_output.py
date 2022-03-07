from testcases.cu_pass.dpa_calculator.features.helpers.utilities import sanitize_multiline_expected_string

EXPECTED_LOG_OUTPUT = sanitize_multiline_expected_string("""Inputs:
	DPA Name: HATCREEK
	Number of iterations: 1
	Aggregate interference calculator: AggregateInterferenceCalculatorWinnforum

CbsdTypes.AP iteration 1
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
	CbsdCategories.A NEIGHBORHOOD RESULTS:
		Input: 0
		Value: 0
		Threshold used: -165 dBm
		Beamwidth: 0.98 degrees
		Expected interference: -1000 dBm

	CbsdCategories.B NEIGHBORHOOD RESULTS:
		Input: 0
		Value: 0
		Threshold used: -165 dBm
		Beamwidth: 0.98 degrees
		Expected interference: -1000 dBm


Final results:
	Distance: {<CbsdTypes.AP: 'AP'>: {<CbsdCategories.A: 'A'>: 0, <CbsdCategories.B: 'B'>: 0}}
	Interference: {<CbsdTypes.AP: 'AP'>: {<CbsdCategories.A: 'A'>: -1000.0, <CbsdCategories.B: 'B'>: -1000.0}}
""")
