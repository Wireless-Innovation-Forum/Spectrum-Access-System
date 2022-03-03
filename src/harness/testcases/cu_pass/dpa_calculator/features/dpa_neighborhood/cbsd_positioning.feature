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
      | rural       | 18923                      | 171                        |
      | suburban    | 4258                       | 284                        |
      | urban       | 2271                       | 142                        |

  Scenario: Cbsds are created with a random distribution in the zone
    Given a category A simulation distance of 150 km
    And a category B simulation distance of 300 km
    And random seed 5
    And a lot of CBSDs
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

  @slow
  Scenario Template: The number of UEs is created
    Given a <region_type> location
    And <number_of_ues_per_ap> UEs per category <cbsd_category> AP
    When category <cbsd_category> UE CBSDs for the Monte Carlo simulation are created
    Then there should be <expected_ue_per_ap> times as many CBSDs as if category <cbsd_category> AP CBSDs were created

    Examples: Default
      | region_type | number_of_ues_per_ap | cbsd_category | expected_ue_per_ap |
      | dense urban | default              | A             | 50                 |
      | rural       | default              | A             | 3                  |
      | suburban    | default              | A             | 20                 |
      | urban       | default              | A             | 50                 |
      | dense urban | default              | B             | 200                |
      | rural       | default              | B             | 500                |
      | suburban    | default              | B             | 200                |
      | urban       | default              | B             | 200                |

    Examples: Configurable
      | region_type | number_of_ues_per_ap | cbsd_category | expected_ue_per_ap |
      | dense urban | 2                    | A             | 2                  |
      | rural       | 2                    | A             | 2                  |
      | suburban    | 2                    | A             | 2                  |
      | urban       | 2                    | A             | 2                  |
      | dense urban | 2                    | B             | 2                  |
      | rural       | 2                    | B             | 2                  |
      | suburban    | 2                    | B             | 2                  |
      | urban       | 2                    | B             | 2                  |
