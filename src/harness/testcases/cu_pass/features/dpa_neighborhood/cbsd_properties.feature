Feature: CBSD properties
  Scenario Template: Grants are created with indoor percentage based on region type
    Given a <region_type> location
    When CBSDs for the Monte Carlo simulation are created
    Then <expected_indoor_percentage> of the grants should be indoors

    Examples:
      | region_type | expected_indoor_percentage |
      | rural       | 0.99                       |
      | suburban    | 0.99                       |
      | urban       | 0.8                        |

  Scenario Template: Indoor CBSDs are created with random heights
    Given a <region_type> location
    When <cbsd_type> CBSDs for the Monte Carlo simulation are created
    Then the indoor antenna heights should fall in distribution <height_distribution>
    And indoor antenna heights should be in 0.5 meter increments

    Examples:
      | cbsd_type | region_type | height_distribution                           |
      | AP        | dense urban | 50%: 3-15, 25%: 18-30, 25%: 33-60             |
      | AP        | rural       | 80%: 3, 20%: 6                                |
      | AP        | suburban    | 70%: 3, 30%: 6-12                             |
      | AP        | urban       | 50%: 3, 50%: 6-18                             |
      | UE        | dense urban | 50%: 1.5-13.5, 25%: 16.5-28.5, 25%: 31.5-58.5 |
      | UE        | rural       | 80%: 1.5, 20%: 4.5                            |
      | UE        | suburban    | 70%: 1.5, 30%: 4.5-10.5                       |
      | UE        | urban       | 50%: 1.5, 50%: 4.5-16.5                       |

  Scenario Template: Outdoor CBSDs are created with heights
    When <cbsd_type> CBSDs for the Monte Carlo simulation are created
    Then outdoor antenna heights should be <expected_height> meters

    Examples:
      | cbsd_type | expected_height |
      | AP        | 6               |
      | UE        | 1.5             |

  Scenario Outline: AP gains are set
    When <cbsd_type> CBSDs for the Monte Carlo simulation are created
    Then the antenna gains should be <expected_gain> meters

    Examples:
      | cbsd_type | expected_gain |
      | AP        | 6             |
      | UE        | 0             |
