Feature: Quick Run
  Background:
    Given random seed 0
    And 2 category A UEs
    And 1 category B UEs
    And 2 monte carlo iterations

  Scenario Template: A quick run is performed with UEs
    Given UE runs are included
    When the neighborhood radius is calculated
    Then the resulting category <cbsd_category> <cbsd_type> distance should be <expected_distance>
    And the resulting category <cbsd_category> <cbsd_type> interference should be <expected_interference>

    Examples:
      | cbsd_type | cbsd_category | expected_distance | expected_interference |
      | AP        | A             | 0                 | -147.04742785877025   |
      | AP        | B             | 0                 | -150.1978609892087    |
      | UE        | A             | 0                 | -184.9533031783413    |
      | UE        | B             | 0                 | -160.45015587659296   |


  Scenario Template: A quick run is performed without UEs
    When the neighborhood radius is calculated
    Then the resulting category <cbsd_category> <cbsd_type> distance should be <expected_distance>
    And the resulting category <cbsd_category> <cbsd_type> interference should be <expected_interference>
    And the resulting UE distance should not exist
    And the resulting UE interference should not exist

    Examples:
      | cbsd_type | cbsd_category | expected_distance | expected_interference |
      | AP        | A             | 0                 | -223.46822566634117   |
      | AP        | B             | 0                 | -147.6771136871935   |

  Scenario Template: The neighborhood category is configurable
    Given neighborhood categories <neighborhood_categories>
    When the neighborhood radius is calculated
    Then the resulting category <cbsd_category> <cbsd_type> distance <expected_distance>
    And the resulting category <cbsd_category> <cbsd_type> interference <expected_interference>

    Examples:
      | neighborhood_categories | cbsd_type | cbsd_category | expected_distance | expected_interference         |
      | [A]                     | AP        | A             | should be 0       | should be -223.46822566634117 |
      | [A]                     | AP        | B             | should not exist  | should not exist              |
      | [B]                     | AP        | A             | should not exist  | should not exist              |
      | [B]                     | AP        | B             | should be 0       | should be -147.6771136871935  |
      | [A,B]                   | AP        | A             | should be 0       | should be -223.46822566634117 |
      | [A,B]                   | AP        | B             | should be 0       | should be -147.6771136871935  |

  Scenario Template: The interference threshold is configurable
    Given interference threshold <interference_threshold> dBm
    When the neighborhood radius is calculated
    Then the local output log should contain "<expected_log_portion>"
    And the resulting category <cbsd_category> <cbsd_type> interference should be <expected_interference>

    Examples:
      | interference_threshold | expected_log_portion     | cbsd_category | cbsd_type | expected_interference |
      | -130                   | Threshold used: -129 dBm | A             | AP        | -141.48616716614754   |
      | 0                      | Threshold used: 1 dBm    | A             | AP        | -141.48616716614754   |
