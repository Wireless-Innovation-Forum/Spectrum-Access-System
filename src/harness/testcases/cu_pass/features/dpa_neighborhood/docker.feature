Feature: Docker run
  Scenario: Output is written to s3
    Given random seed 0
    When the main docker command is run
    Then the log file uploaded to S3 should be
      """
      Inputs:
          DPA Name: HATCREEK
          Number of APs: 1
          Number of iterations: 1
          Simulation area radius: 10 kilometers
          Aggregate interference calculator: AggregateInterferenceCalculatorNtia
          Population retriever: PopulationRetrieverCensus
          Number of APs calculator: NumberOfApsCalculatorShipborne

      Monte Carlo iteration 1
          CBSD 1 / 1

          Found parameter
              Input: 1
              Value: -inf

          CBSD 1 / 3
          CBSD 2 / 3
          CBSD 3 / 3

          Found parameter
              Input: 1
              Value: -228.21931595139122


      Results for APs:
          50th percentile: 1
          95th percentile: 1
          Standard Deviation: 0
          Minimum: 1
          Maximum: 1

      Results for UEs:
          50th percentile: 1
          95th percentile: 1
          Standard Deviation: 0
          Minimum: 1
          Maximum: 1

      Final results:
          Distance: 1
          Interference: -228.21931595139122
          AP Distance: 1
          UE Distance: 1
          AP Interference: -inf
          UE Interference: -228.21931595139122

      """
    And the results file uploaded to s3 should be
      """
      {"distance": 1, "distance_access_point": 1, "distance_user_equipment": 1, "interference": -228.21931595139122, "interference_access_point": -Infinity, "interference_user_equipment": -228.21931595139122, "runtime": null}
      """

  Scenario Template: DPA name is configurable by the command line
    Given DPA name <dpa_name>
    When the main docker command is run
    Then <expected_log_portion> should be in the output log

    Examples:
      | dpa_name  | expected_log_portion |
      | Hat Creek | DPA Name: HATCREEK   |
      | McKinney | DPA Name: MCKINNEY   |

  Scenario Template: The number of iterations is configurable by the command line
    Given <number_of_iterations> monte carlo iterations
    When the main docker command is run
    Then <expected_log_portion> should be in the output log

    Examples:
      | number_of_iterations  | expected_log_portion    |
      | 1                     | Number of iterations: 1 |
      | 2                     | Number of iterations: 2 |

  Scenario Template: The simulation area is configurable by the command line
    Given a simulation area radius of <simulation_area_radius>
    When the main docker command is run
    Then <expected_log_portion> should be in the output log

    Examples:
      | simulation_area_radius | expected_log_portion                |
      | 2                      | Simulation area radius: 2 kilometers |
      | 3                      | Simulation area radius: 3 kilometers |

  Scenario: Logs are still written if exception is encountered
    Given an exception will be encountered during calculation
    When the main docker command is run
    Then the log file uploaded to S3 should be
      """
      """
