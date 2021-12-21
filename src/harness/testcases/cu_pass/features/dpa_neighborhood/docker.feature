Feature: Docker run
  Scenario: Output logs are written
    Given random seed 0
    And out_s3.log as an s3 object name for the s3 log file
    And output/out_local.log as a local filepath for the local log file
    When the main docker command is run
    Then the log file uploaded to S3 should be
      """
      Inputs:
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

      """
    And the local log file should match the s3 log file

  Scenario: Output results are written
    Given random seed 0
    And results_s3.json as an s3 object name for the s3 results file
    And output/results_local.json as a local filepath for the local results file
    When the main docker command is run
    Then the results file uploaded to s3 should be
      """
      {"distance": 0, "distance_access_point": 0, "distance_user_equipment": 0, "interference": -Infinity, "interference_access_point": -Infinity, "interference_user_equipment": -Infinity, "runtime": null}
      """
    And the local results file should match the s3 results file

  Scenario: The s3 log file is not given

  Scenario: The s3 results file is not given

  Scenario: The local log file is not given

  Scenario: The local results file is not given

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
      | simulation_area_radius | expected_log_portion                 |
      | 2                      | Simulation area radius: 2 kilometers |
      | 3                      | Simulation area radius: 3 kilometers |

  Scenario: The local output log is configurable by the command line
    Given an output log filepath of out.log
    When the main docker command is run
    Then the file out.log should be

  Scenario: Logs are still written if exception is encountered
    Given an exception will be encountered during calculation
    When the main docker command is run
    Then the log file uploaded to S3 should be
      """
      Test logs

      """
