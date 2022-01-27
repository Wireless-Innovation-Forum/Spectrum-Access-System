Feature: Interference contributions
  Scenario Template: Interference contribution EIRPs are calculated
    Given a <region_type> location
    When interference components are calculated for each <cbsd_type> CBSD
    Then the category <cbsd_category> <indoor_outdoor> antenna EIRPs should be <expected_power> dBm

    Examples:
      | cbsd_type | cbsd_category | indoor_outdoor | region_type | expected_power |
      | AP        | A             | outdoor        | dense urban | 27.8           |
      | AP        | A             | outdoor        | rural       | 23             |
      | AP        | A             | outdoor        | suburban    | 26             |
      | AP        | A             | outdoor        | urban       | 27.8           |
      | AP        | A             | indoor         | dense urban | 23.8           |
      | AP        | A             | indoor         | rural       | 19             |
      | AP        | A             | indoor         | suburban    | 22             |
      | AP        | A             | indoor         | urban       | 23.8           |
      | UE        | A             |                | dense urban | 21.8           |
      | UE        | A             |                | rural       | 17             |
      | UE        | A             |                | suburban    | 20             |
      | UE        | A             |                | urban       | 21.8           |


  Scenario: Receiver insertion losses
    When interference components are calculated for each CBSD
    Then all receiver insertion losses should be 2 dB

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
    And all losses are equal if and only if <expected_clutter_loss_range> is not a range

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
    Then the building attenuation losses follow the distribution 100%: 15

  Scenario: CBSD distances are calculated
    Given a CBSD 100 km away from the DPA
    When interference components are calculated for each CBSD
    Then the distance from the antenna should be 100

  Scenario: Gain pattern antenna gains are calculated
    Given random seed 3
    And azimuth range [60, 120]
    And beamwidth 30
    And a uniform gain pattern
    When interference components are calculated for each CBSD
    Then the receive antenna gains should be [1.2017051500608984, 3.055456434642929, 2.263308776656403, 2.754758825387543, 4.275124084226826]
    And the receive antenna azimuths should be [60.0, 75.0, 90.0, 105.0, 120.0]

  Scenario: Standard receive antenna gains are calculated
    Given azimuth range [60, 120]
    And beamwidth 30
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
