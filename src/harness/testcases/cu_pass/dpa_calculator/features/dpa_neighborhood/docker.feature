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
    Then "<expected_log_portion>" should be in the output log

    Examples:
      | dpa_name  | expected_log_portion |
      | Hat Creek | DPA Name: HATCREEK   |
      | McKinney  | DPA Name: MCKINNEY   |

  Scenario Template: The number of iterations is configurable by the command line
    Given <number_of_iterations> monte carlo iterations
    When the main docker command is run
    Then "<expected_log_portion>" should be in the output log

    Examples:
      | number_of_iterations  | expected_log_portion    |
      | 1                     | Number of iterations: 1 |
      | 2                     | Number of iterations: 2 |

  Scenario Template: The neighborhood category is configurable by the command line
    Given neighborhood categories <neighborhood_categories>
    When the main docker command is run
    Then the results <category_a_should> include category A results
    And the results <category_b_should> include category B results

    Examples:
      | neighborhood_categories | category_a_should     | category_b_should   |
      | [A]                     | should                | should not          |
      | [B]                     | should not            | should              |
      | []                      | should                | should              |

  Scenario Template: The simulation area is configurable by the command line
    Given a category <cbsd_category> simulation distance of <category_a_radius> km
    When the main docker command is run
    Then "<expected_log_portion>" should be in the output log

    Examples:
      | cbsd_category | category_a_radius | expected_log_portion                 |
      | A             | 2                 | Simulation area radius, category A: 2 kilometers |
      | A             | 3                 | Simulation area radius, category A: 3 kilometers |
      | B             | 2                 | Simulation area radius, category B: 2 kilometers |
      | B             | 3                 | Simulation area radius, category B: 3 kilometers |

  Scenario Template: The number of category B UEs per AP is configurable by the command line
    Given <number_of_ues_per_ap> UEs per category <cbsd_category> AP
    When the main docker command is run
    Then "<expected_log_portion>" should be in the output log

    Examples:
      | number_of_ues_per_ap | cbsd_category | expected_log_portion                                                |
      | 2                    | A             | CBSD Category: CbsdCategories.A\n.*\n.*\n\s+Number of UEs per AP: 2 |
      | 3                    | A             | CBSD Category: CbsdCategories.A\n.*\n.*\n\s+Number of UEs per AP: 3 |
      | 2                    | B             | CBSD Category: CbsdCategories.B\n.*\n.*\n\s+Number of UEs per AP: 2 |
      | 3                    | B             | CBSD Category: CbsdCategories.B\n.*\n.*\n\s+Number of UEs per AP: 3 |

  Scenario: The interference threshold is configurable by the command line
    Given interference threshold -131 dBm
    When the main docker command is run
    Then "Threshold used: -130 dBm" should be in the output log

  Scenario: The DPA defined interference threshold is used as a default
    When the main docker command is run
    Then "Threshold used: -176 dBm" should be in the output log

  Scenario: Running UEs can be enabled by the command line
    Given UE runs are included
    When the main docker command is run
    Then the results should include UE results

  Scenario Template: The beamwidth is configurable by the command line
    Given a beamwidth of <beamwidth>
    When the main docker command is run
    Then "<expected_log_portion>" should be in the output log

    Examples:
      | beamwidth | expected_log_portion   |
      | 1         | Beamwidth: 1.0 degrees |

  Scenario: Running UEs is disabled by default when run by the command line
    When the main docker command is run
    Then the results should not include UE results

  Scenario: Logs are still written if exception is encountered
    Given an exception will be encountered during calculation
    When the main docker command is run
    Then the log file uploaded to S3 should be uploaded

  Scenario: S3 bucket does not exist
    Given "s3_bucket" as an s3 bucket name
    And the bucket does not already exist
    When the main docker command is run
    Then an error message should say ""s3_bucket" does not exist."
