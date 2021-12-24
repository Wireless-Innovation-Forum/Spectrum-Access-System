Feature: Docker run
  Scenario Template: Output files are individually optional
    Given random seed 0
    And <s3_log_name> as an s3 object name for the s3 log file
    And <s3_results_name> as an s3 object name for the s3 results file
    And <local_log_filepath> as a local filepath for the local log file
    And <local_results_filepath> as a local filepath for the local results file
    When the main docker command is run
    Then the log file uploaded to S3 <s3_log_exists> exist
    Then the results file uploaded to S3 <s3_results_exist> exist
    And the local log file <local_log_exists> exist
    And the local results file <local_results_exist> exist

    Examples:
      | s3_log_name | s3_results_name | local_log_filepath   | local_results_filepath    | s3_log_exists | s3_results_exist | local_log_exists | local_results_exist |
      | out_s3.log  | results_s3.json | output/out_local.log | output/results_local.json | should        | should           | should           | should              |
      | None        | results_s3.json | output/out_local.log | output/results_local.json | should not    | should           | should           | should              |
      | out_s3.log  | None            | output/out_local.log | output/results_local.json | should        | should not       | should           | should              |
      | out_s3.log  | results_s3.json | None                 | output/results_local.json | should        | should           | should not       | should              |
      | out_s3.log  | results_s3.json | output/out_local.log | None                      | should        | should           | should           | should not          |


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

  Scenario: Logs are still written if exception is encountered
    Given an exception will be encountered during calculation
    When the main docker command is run
    Then the log file uploaded to S3 should be
      """
      Test logs

      """

  Scenario: S3 bucket does not exist
    Given "s3_bucket" as an s3 bucket name
    And the bucket does not already exist
    When the main docker command is run
    Then an error message should say ""s3_bucket" does not exist."
