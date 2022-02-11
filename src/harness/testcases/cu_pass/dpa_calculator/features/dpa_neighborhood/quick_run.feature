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
      | AP        | A             | 0                 | -157.09596620840563   |
      | AP        | B             | 0                 | -160.1922893328677   |
      | UE        | A             | 0                 | -195.09115850222102   |
      | UE        | B             | 0                 | -170.44050654358452    |


  Scenario Template: A quick run is performed without UEs
    When the neighborhood radius is calculated
    Then the resulting category <cbsd_category> <cbsd_type> distance should be <expected_distance>
    And the resulting category <cbsd_category> <cbsd_type> interference should be <expected_interference>
    And the resulting UE distance should not exist
    And the resulting UE interference should not exist

    Examples:
      | cbsd_type | cbsd_category | expected_distance | expected_interference |
      | AP        | A             | 0                 | -151.48616716614754   |
      | AP        | B             | 0                 | -160.19041297883996   |

  Scenario Template: The neighbohood category is configurable
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
