Feature: Docker run
  Scenario Template: Output files are individually optional
    Given random seed 0
    And <s3_object_directory> as an s3 object directory name for s3 output
    And <local_log_directory> as a local directory for local output
    When the main docker command is run
    Then the log file uploaded to S3 <s3_log_exists> exist at <s3_object_directory>/__RUNTIME__/log.log
    Then the results file uploaded to S3 <s3_results_exist> exist at <s3_object_directory>/__RUNTIME__/result.json
    And the local log file <local_log_exists> exist at <local_log_directory>/__RUNTIME__/log.log
    And the local results file <local_results_exist> exist at <local_log_directory>/__RUNTIME__/result.json

    Examples:
      | s3_object_directory | local_log_directory   | s3_log_exists | s3_results_exist | local_log_exists | local_results_exist |
      | output_s3           | output_local          | should        | should           | should           | should              |
      | None                | output_local          | should not    | should not       | should           | should              |
      | output_s3           | None                  | should        | should           | should not       | should not          |


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
