Feature: CBSD positioning

  Scenario Template: Population data is retrieved
    Given a circular area with a radius of 150 km
    And center coordinates <coordinates>
    Then the population in the area should be <expected_population>

    Examples: McKinney (rural)
      | coordinates         | expected_population |
      | 33.21611, -96.65666 | 6,431,995           |

    Examples: Moorestown (urban)
      | coordinates         | expected_population |
      | 39.97999, -74.90138 | 21,164,114          |

  Scenario Template: The number of APs for simulation is calculated
    Given simulation population of 7,095,966
    And a <region_type> location
    When the number of APs for simulation is calculated
    Then the number of category A APs should be <expected_category_a_number>
    Then the number of category B APs should be <expected_category_b_number>

    Examples:
      | region_type | expected_category_a_number | expected_category_b_number |
      | dense urban | 2271                       | 142                        |
      | rural       | 18923                      | 170                        |
      | suburban    | 4258                       | 284                        |
      | urban       | 2271                       | 142                        |

  Scenario: Cbsds are created with a random distribution in the zone
    Given a category A neighborhood distance of 150 km
    And a category B neighborhood distance of 300 km
    And random seed 5
    When CBSDs for the Monte Carlo simulation are created
    Then all category A points should be within 150 km of the center point
    Then all category B points should be within 300 km of the center point
    And the furthest category A distance should be close to 150 km
    And the furthest category B distance should be close to 300 km
    And the closest category A distance should be close to 0 km
    And the closest category B distance should be close to 0 km
    And the highest category A bearing should be close to 360 degrees
    And the highest category B bearing should be close to 360 degrees
    And the lowest category A bearing should be close to 0 degrees
    And the lowest category B bearing should be close to 0 degrees
    And no points should have exactly the same latitude, longitude, or bearing

  Scenario Template: The number of UEs is created
    Given a <region_type> location
    When UE CBSDs for the Monte Carlo simulation are created
    Then there should be <expected_ue_per_ap> times as many as if AP grants were created

    Examples:
      | region_type | expected_ue_per_ap |
      | rural       | 3                  |
      | suburban    | 20                 |
      | urban       | 50                 |
