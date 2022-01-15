Feature: CBSD properties, Category A
  Scenario: Category A AP transmission powers are set
    When Category A AP CBSDs for the Monte Carlo simulation are created
    Then the indoor antenna maximum EIRPs should be 100%: 26 dBm
    And the outdoor antenna maximum EIRPs should be 100%: 30 dBm

  Scenario: UE transmission powers are set
    When UE CBSDs for the Monte Carlo simulation are created
    Then the antenna maximum EIRPs should be 100%: 24 dBm

  Scenario Template: Category B AP transmission powers are set
    Given a <region_type> location
    When Category B AP CBSDs for the Monte Carlo simulation are created
    Then the outdoor antenna maximum EIRPs should be <expected_power> dBm

    Examples:
      | region_type | expected_power |
      | dense urban | 100%: 40-47    |
      | rural       | 100%: 47       |
      | suburban    | 100%: 47       |
      | urban       | 100%: 40-47    |

  Scenario Template: CBSDs are created with indoor percentage based on region type
    Given a <region_type> location
    When Category <cbsd_category> CBSDs for the Monte Carlo simulation are created
    Then <expected_indoor_percentage> of the grants should be indoors

    Examples:
      | cbsd_category | region_type | expected_indoor_percentage |
      | A             | dense urban | 0.8                        |
      | A             | rural       | 0.99                       |
      | A             | suburban    | 0.99                       |
      | A             | urban       | 0.8                        |
      | B             | dense urban | 0                          |
      | B             | rural       | 0                          |
      | B             | suburban    | 0                          |
      | B             | urban       | 0                          |

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
