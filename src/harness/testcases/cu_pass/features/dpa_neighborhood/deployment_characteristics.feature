Feature: Deployment Characteristics
    Scenario Template: Grants are created with indoor percentage based on region type
    Given a <region_type> location
    When CBSDs for the Monte Carlo simulation are created
    Then <expected_indoor_percentage> of the grants should be indoors

    Examples:
      | region_type | expected_indoor_percentage |
      | rural       | 0.99                       |
      | suburban    | 0.99                       |
      | urban       | 0.8                        |

  Scenario Template: Indoor grants are created with random heights
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

  Scenario Template: Outdoor grants are created with heights
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

  Scenario: AP transmission powers are set
    When AP CBSDs for the Monte Carlo simulation are created
    Then the indoor antenna EIRPs should be 26 dBm
    Then the outdoor antenna EIRPs should be 30 dBm

  Scenario: UE transmission powers are set
    When UE CBSDs for the Monte Carlo simulation are created
    Then the antenna EIRPs should be 24 dBm

  Scenario: Basic interference components from each CBSD is calculated
    When interference components are calculated for each CBSD
    Then EIRPs in the interference components should match those in the cbsds
    And all receiver insertion losses should be 2 dB

  Scenario: Transmitter insertion losses for APs are calculated
    When AP CBSDs for the Monte Carlo simulation are created
    And interference components are calculated for each CBSD
    Then transmitter insertion losses for indoor APs should be 0 dB
    And transmitter insertion losses for outdoor APs should be 2 dB

  Scenario: Transmitter insertion losses for UEs are calculated
    And interference components are calculated for each UE CBSD
    And transmitter insertion losses for UEs should be 0 dB

  Scenario Template: Clutter loss is randomly assigned to rural sources
    Given a <region_type> location
    When interference components are calculated for each CBSD
    Then clutter loss distribution is within <expected_clutter_loss_range>
    And not all losses are equal if and only if <expected_clutter_loss_range> is a range

    Examples: Non-rural regions have no clutter loss
      | region_type | expected_clutter_loss_range |
      | urban       | 0                           |

    Examples: Rural regions have random clutter loss
      | region_type | expected_clutter_loss_range |
      | rural       | 0-15                        |

  Scenario Template: Propagation loss is calculated
    Given a <region_type> location
    And a CBSD at a location with larger <larger_loss_model> with height <height>
    When interference components are calculated for each CBSD
    Then the propagation loss should be <expected_loss>

    Examples: ITM is larger
      | region_type | larger_loss_model | height | expected_loss     |
      | urban       | ITM               | 17     | 247.2795048399713  |

    Examples: eHata is larger
      | region_type | larger_loss_model | height | expected_loss      |
      | urban       | eHata             | 17     | 213.960500138624   |

    Examples: heights at least 18 meters always use ITM
      | region_type | larger_loss_model | height | expected_loss      |
      | urban       | eHata             | 18     | 193.3062149090018  |

    Examples: rural APs always use ITM
      | region_type | larger_loss_model | height | expected_loss      |
      | rural       | eHata             | 17     | 140.25217071792468 |

  Scenario: Building attenuation loss is included in interference calculation
    When interference components are calculated for each CBSD
    Then the building attenuation losses follow the distribution 20%: 20, 60%: 15, 20%: 10

  Scenario: CBSD distances are calculated
    Given a CBSD 100 km away from the DPA
    When interference components are calculated for each CBSD
    Then the distance from the antenna should be 100

  Scenario: Uniform receive antenna gains are calculated
    Given a dpa with azimuth range [60, 120] and beamwidth 30
    And random seed 5
    When interference components are calculated for each CBSD
    Then the receive antenna gains should be [0.8766095731965083, 0.848936567834775, 3.7816585710009916, 5.625166068881945, 1.6135574527107925]

  Scenario: Standard receive antenna gains are calculated
    Given a dpa with azimuth range [60, 120] and beamwidth 30
    And a CBSD at a location 33.19313987787715, -96.36484196127637
    When interference components are calculated for each CBSD with standard receive antenna gain
    Then the receive antenna gains should be [-16.585712131717642, -5.477964417053489, -0.3702167023893314, -1.2624689877251745, -8.154721273061018]
    And the receive antenna azimuths should be [60.0, 75.0, 90.0, 105.0, 120.0]

  Scenario Template: Total interference for a cbsd is calculated
    Given an EIRP of <eirp> dB
    And a receive antenna gain of <receive_antenna_gain> dB
    And a transmitter insertion loss of <transmitter_loss> dB
    And a receiver insertion loss of <receiver_loss> dB
    And a propagation loss of <propagation_loss> dB
    And a clutter loss of <clutter_loss> dB
    And a building loss of <building_loss> dB
    Then the total interference should be <expected_interference>

    Examples:
      | eirp | receive_antenna_gain | transmitter_loss | receiver_loss | propagation_loss | clutter_loss | building_loss | expected_interference |
      | 30   | -12                  | 2                | 2             | 130              | 10           | 10            | -136                  |
      | 31   | -12                  | 2                | 2             | 130              | 10           | 10            | -135                  |
      | 30   | -13                  | 2                | 2             | 130              | 10           | 10            | -137                  |
      | 30   | -12                  | 4                | 2             | 130              | 10           | 10            | -138                  |
      | 30   | -12                  | 2                | 5             | 130              | 10           | 10            | -139                  |
      | 30   | -12                  | 2                | 2             | 134              | 10           | 10            | -140                  |
      | 30   | -12                  | 2                | 2             | 130              | 15           | 10            | -141                  |
      | 30   | -12                  | 2                | 2             | 130              | 10           | 16            | -142                  |

  Scenario Template: Aggregate interference using the maximum azimuth is chosen
    Given CBSDs at distances [10, 5] each with gains [[1, 2], [3, 1]] at azimuths [0, 90]
    Then the returned interference with minimum distance <distance> should be the aggregate of interference from CBSDs <expected_cbsd_numbers> at azimuth <expected_azimuth>

    Examples:
      | distance | expected_cbsd_numbers | expected_azimuth |
      | 0        | [0, 1]                | 0                |
      | 6        | [0]                   | 90               |
