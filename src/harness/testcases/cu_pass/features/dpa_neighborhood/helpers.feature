Feature: DPA Neighborhood helpers
  Scenario Outline: A binary search algorithm correctly finds inputs, assuming the function results lessen as the input grows
    Given a function whose output is the element of array <result_array> at the given index
    And a target of <target>
    When the algorithm is run with step size <step_size>
    Then the resulting input should be <expected_input>
    And the resulting return value should be <expected_value>

    Examples: Finds number while expanding
      | result_array | target | expected_input | expected_value | step_size |
      | [0]          | 0      | 0              | 0              | 1         |
      | [1,0]        | 0      | 1              | 0              | 1         |

    Examples: Finds number after expanding
      | result_array | target | expected_input | expected_value | step_size |
      | [3,2,1,0]    | 1      | 2              | 1              | 1         |

    Examples: Target does not exist but is in range
      | result_array | target | expected_input | expected_value | step_size |
      | [3,2,2,0]    | 1      | 3              | 0              | 1         |

    Examples: Target is greater than what you would get with the minimum input
      | result_array | target | expected_input | expected_value | step_size |
      | [0]          | 1      | 0              | 0              | 1         |

    Examples: Target is less than what you would get with the maximum input
      | result_array | target | expected_input | expected_value | step_size |
      | [3,2,1,0]    | -1     | 3              | 0              | 1         |

    Examples: Step size is configurable
      | result_array | target | expected_input | expected_value | step_size |
      | [3,2,1,0]    | 2      | 2              | 1              | 2         |

    Examples: Max is the next step size if max is not a multiple of the step size
      | result_array | target | expected_input | expected_value | step_size |
      | [3,2,1]      | -1     | 2              | 1              | 2         |
      | [3,2,1,0]    | -1     | 4              | -infinity      | 2         |


  Scenario Template: A monte carlo simulation is run
    Given functions whose results return the next element of <function_results> each time it runs
    When a monte carlo simulation of the function is run for the 95 percentile
    Then the simulation results should be <expected_simulation_results>

    Examples:
      | function_results            | expected_simulation_results |
      | [[1,2,3,4,5]]               | [4]                         |
      | [[1,2,3,4,5], [10,9,8,7,6]] | [4, 9]                      |

  Scenario: Logging is captured
    Given random seed 0
    And 2 category A UEs
    And 2 category B UEs
    And 2 monte carlo iterations
    When the neighborhood radius is calculated
    Then the output log should be
      """
      Inputs:
          DPA Name: MCKINNEY
          Number of iterations: 2
          Aggregate interference calculator: AggregateInterferenceCalculatorWinnforum

      Monte Carlo iteration 1
          CBSD Deployment:
              CBSD Type: CbsdTypes.AP
              Simulation area radius, category A: 250 kilometers
              Simulation area radius, category B: 500 kilometers
              CBSD Category: CbsdCategories.A
                  Population: 50.0
                  Number of APs: 1
                  Number of UEs per AP: 2
                  Population retriever: PopulationRetrieverCensus
                  Number of APs calculator: NumberOfCbsdsCalculatorShipborne
              CBSD Category: CbsdCategories.B
                  Population: 50.0
                  Number of APs: 1
                  Number of UEs per AP: 2
                  Population retriever: PopulationRetrieverCensus
                  Number of APs calculator: NumberOfCbsdsCalculatorShipborne

          Found parameter
              Input: 0
              Value: -147.68087540754377

          CBSD Deployment:
              CBSD Type: CbsdTypes.UE
              Simulation area radius, category A: 250 kilometers
              Simulation area radius, category B: 500 kilometers
              CBSD Category: CbsdCategories.A
                  Population: 50.0
                  Number of UEs: 2
                  Number of UEs per AP: 2
                  Population retriever: PopulationRetrieverCensus
                  Number of APs calculator: NumberOfCbsdsCalculatorShipborne
              CBSD Category: CbsdCategories.B
                  Population: 50.0
                  Number of UEs: 2
                  Number of UEs per AP: 2
                  Population retriever: PopulationRetrieverCensus
                  Number of APs calculator: NumberOfCbsdsCalculatorShipborne

          Found parameter
              Input: 0
              Value: -158.71014878819602

      Monte Carlo iteration 2
          CBSD Deployment:
              CBSD Type: CbsdTypes.AP
              Simulation area radius, category A: 250 kilometers
              Simulation area radius, category B: 500 kilometers
              CBSD Category: CbsdCategories.A
                  Population: 50.0
                  Number of APs: 1
                  Number of UEs per AP: 2
                  Population retriever: PopulationRetrieverCensus
                  Number of APs calculator: NumberOfCbsdsCalculatorShipborne
              CBSD Category: CbsdCategories.B
                  Population: 50.0
                  Number of APs: 1
                  Number of UEs per AP: 2
                  Population retriever: PopulationRetrieverCensus
                  Number of APs calculator: NumberOfCbsdsCalculatorShipborne

          Found parameter
              Input: 0
              Value: -179.86587466161478

          CBSD Deployment:
              CBSD Type: CbsdTypes.UE
              Simulation area radius, category A: 250 kilometers
              Simulation area radius, category B: 500 kilometers
              CBSD Category: CbsdCategories.A
                  Population: 50.0
                  Number of UEs: 2
                  Number of UEs per AP: 2
                  Population retriever: PopulationRetrieverCensus
                  Number of APs calculator: NumberOfCbsdsCalculatorShipborne
              CBSD Category: CbsdCategories.B
                  Population: 50.0
                  Number of UEs: 2
                  Number of UEs per AP: 2
                  Population retriever: PopulationRetrieverCensus
                  Number of APs calculator: NumberOfCbsdsCalculatorShipborne

          Found parameter
              Input: 0
              Value: -209.5981262579205


      Results for APs:
          50th percentile: 0
          95th percentile: 0
          Standard Deviation: 0.0
          Minimum: 0
          Maximum: 0

      Results for UEs:
          50th percentile: 0
          95th percentile: 0
          Standard Deviation: 0.0
          Minimum: 0
          Maximum: 0

      Final results:
          Distance: 0
          Interference: -161.25454766168224
          AP Distance: 0
          UE Distance: 0
          AP Interference: -149.29012537024732
          UE Interference: -161.25454766168224

      """
