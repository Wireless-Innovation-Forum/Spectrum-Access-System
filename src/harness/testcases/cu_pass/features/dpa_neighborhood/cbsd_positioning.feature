Feature: CBSD positioning

  Scenario Template: Population data is retrieved
    Given a circular area with a radius of 150 km
    And center coordinates <coordinates>
    And census population data
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
    Then the result should be <expected_result>

    Examples:
      | region_type | expected_result |
      | rural       | 47306           |
      | suburban    | 7096            |
      | urban       | 2838            |

  Scenario: Cbsds are created with a random distribution on the zone circumference
    Given a circular area with a radius of 150 km
    And random seed 5
    When CBSDs for the Monte Carlo simulation are created
    Then all distributed points should be within the radius of the center point
    And the furthest distance should be close to 150 km
    And the closest distance should be close to 0 km
    And the highest bearing should be close to 360 degrees
    And the lowest bearing should be close to 0 degrees
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
