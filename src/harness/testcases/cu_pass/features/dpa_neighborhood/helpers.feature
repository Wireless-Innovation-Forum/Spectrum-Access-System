Feature: DPA Neighborhood helpers
  Scenario Outline: A binary search algorithm correctly finds inputs, assuming the function results lessen as the input grows
    Given a function whose output is the element of array <result_array> at the given index
    And a target of <target>
    When the algorithm is run
    Then the resulting input should be <expected_input>
    And the resulting return value should be <expected_value>

    Examples: Finds number while expanding
      | result_array | target | expected_input | expected_value |
      | [0]          | 0      | 0              | 0              |
      | [1,0]        | 0      | 1              | 0              |

    Examples: Finds number after expanding
      | result_array | target | expected_input | expected_value |
      | [3,2,1,0]    | 1      | 2              | 1              |

    Examples: Target does not exist but is in range
      | result_array | target | expected_input | expected_value |
      | [3,2,2,0]    | 1      | 3              | 0              |

    Examples: Target is greater than what you would get with the minimum input
      | result_array | target | expected_input | expected_value |
      | [0]          | 1      | 0              | 0              |

    Examples: Target is less than what you would get with the maximum input
      | result_array | target | expected_input | expected_value |
      | [3,2,1,0]    | -1     | 3              | 0              |

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
    And 2 category A APs
    And 2 category B APs
    And 2 monte carlo iterations
    When the neighborhood radius is calculated
    Then the output log should be
      """
      Inputs:
          DPA Name: MCKINNEY
          Number of APs: 2
          Number of iterations: 2
          Simulation area radius: 100 kilometers
          Aggregate interference calculator: AggregateInterferenceCalculatorNtia
          Population retriever: PopulationRetrieverCensus
          Number of APs calculator: NumberOfApsCalculatorShipborne

      Monte Carlo iteration 1
          CBSD 1 / 2
          CBSD 2 / 2

          Found parameter
              Input: 0
              Value: -147.7689308696676

          CBSD 1 / 6
          CBSD 2 / 6
          CBSD 3 / 6
          CBSD 4 / 6
          CBSD 5 / 6
          CBSD 6 / 6

          Found parameter
              Input: 0
              Value: -151.99414909249862

      Monte Carlo iteration 2
          CBSD 1 / 2
          CBSD 2 / 2

          Found parameter
              Input: 0
              Value: -217.84989487007476

          CBSD 1 / 6
          CBSD 2 / 6
          CBSD 3 / 6
          CBSD 4 / 6
          CBSD 5 / 6
          CBSD 6 / 6

          Found parameter
              Input: 1
              Value: -185.58218492985793


      Results for APs:
          50th percentile: 0
          95th percentile: 0
          Standard Deviation: 0.0
          Minimum: 0
          Maximum: 0

      Results for UEs:
          50th percentile: 0
          95th percentile: 0
          Standard Deviation: 0.7071067811865476
          Minimum: 0
          Maximum: 1

      Final results:
          Distance: 0
          Interference: -151.99414909249862
          AP Distance: 0
          UE Distance: 0
          AP Interference: -151.27297906968795
          UE Interference: -151.99414909249862

      """