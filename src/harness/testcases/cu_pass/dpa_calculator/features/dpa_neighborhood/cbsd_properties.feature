Feature: CBSD properties
  Scenario: Category A AP transmission powers are set
    When category A AP CBSDs for the Monte Carlo simulation are created
    Then the indoor antenna maximum EIRPs should be 100%: 26 dBm

  Scenario Template: Transmission power levels can be configured
    Given random seed 0
    And a <indoor_outdoor> category <cbsd_category> <cbsdy_type> eirp distribution of <distribution>
    When category <cbsd_category> <cbsdy_type> CBSDs for the Monte Carlo simulation are created
    Then the <indoor_outdoor> antenna maximum EIRPs should be <distribution> dBm

    Examples: Uniform Distribution
      | indoor_outdoor | cbsd_category | cbsdy_type | distribution                   |
      | indoor         | A             | AP         | 100%: 26                       |

    Examples: Normal Distribution
      | indoor_outdoor | cbsd_category | cbsdy_type | distribution                   |
      | indoor         | A             | AP         | 100%: PDF [5-26] mean 14 std 3 |

  Scenario Template: Category B AP transmission powers are set
    Given a <region_type> location
    When category B AP CBSDs for the Monte Carlo simulation are created
    Then the outdoor antenna maximum EIRPs should be <expected_power> dBm

    Examples:
      | region_type | expected_power |
      | dense urban | 100%: 40-47    |
      | rural       | 100%: 47       |
      | suburban    | 100%: 47       |
      | urban       | 100%: 40-47    |

  Scenario: UE transmission powers are set
    When UE CBSDs for the Monte Carlo simulation are created
    Then the antenna maximum EIRPs should be 100%: 24 dBm

  Scenario Template: CBSDs are created with indoor percentage based on region type
    Given a <region_type> location
    When category <cbsd_category> CBSDs for the Monte Carlo simulation are created
    Then <expected_indoor_percentage> of the grants should be indoors

    Examples:
      | cbsd_category | region_type | expected_indoor_percentage |
      | A             | dense urban | 1                          |
      | A             | rural       | 1                          |
      | A             | suburban    | 1                          |
      | A             | urban       | 1                          |
      | B             | dense urban | 0                          |
      | B             | rural       | 0                          |
      | B             | suburban    | 0                          |
      | B             | urban       | 0                          |

  Scenario Template: CBSDs antenna heights are set
    Given a <region_type> location
    When category <cbsd_category> <cbsd_type> CBSDs for the Monte Carlo simulation are created
    Then the <indoor_outdoor> antenna heights should fall in distribution <height_distribution>
    And antenna heights should be in 0.5 meter increments

    Examples:
      | cbsd_category | indoor_outdoor | cbsd_type | region_type | height_distribution                           |
      | A             | indoor         | AP        | dense urban | 50%: 3-15, 25%: 18-30, 25%: 33-60             |
      | A             | indoor         | AP        | rural       | 80%: 3, 20%: 6                                |
      | A             | indoor         | AP        | suburban    | 70%: 3, 30%: 6-12                             |
      | A             | indoor         | AP        | urban       | 50%: 3, 50%: 6-18                             |
      | A             | indoor         | UE        | dense urban | 50%: 1.5-13.5, 25%: 16.5-28.5, 25%: 31.5-58.5 |
      | A             | indoor         | UE        | rural       | 80%: 1.5, 20%: 4.5                            |
      | A             | indoor         | UE        | suburban    | 70%: 1.5, 30%: 4.5-10.5                       |
      | A             | indoor         | UE        | urban       | 50%: 1.5, 50%: 4.5-16.5                       |
      | B             | outdoor        | AP        | dense urban | 100%: 6-30                                    |
      | B             | outdoor        | AP        | rural       | 100%: 6-100                                   |
      | B             | outdoor        | AP        | suburban    | 100%: 6-100                                   |
      | B             | outdoor        | AP        | urban       | 100%: 6-30                                    |
      | B             | outdoor        | UE        | dense urban | 100%: 1.5                                     |
      | B             | outdoor        | UE        | rural       | 100%: 1.5                                     |
      | B             | outdoor        | UE        | suburban    | 100%: 1.5                                     |
      | B             | outdoor        | UE        | urban       | 100%: 1.5                                     |

  Scenario Outline: AP gains are set
    When <cbsd_type> CBSDs for the Monte Carlo simulation are created
    Then the antenna gains should be <expected_gain> meters

    Examples:
      | cbsd_type | expected_gain |
      | AP        | 6             |
      | UE        | 0             |
