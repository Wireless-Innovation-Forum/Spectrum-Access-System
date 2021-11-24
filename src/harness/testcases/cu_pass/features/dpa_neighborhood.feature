Feature: DPA Parameters

  Definitions
    - AP.......: Access point
    - CBSD_A...: Citizens Broadband radio Service Device, category A
    - CBSD_B...: Citizens Broadband radio Service Device, category B
    - EIRP.....: Effective isotropic radiated power
    - INR......: Interference to noise ratio
    - IPC......: Interference protection criteria
    - R_C_DPA_A: Radius of Co-channel frequency range Dynamic Protection Area for category A devices
    - RA.......: Radio astronomy
    - UE.......: User equipment

  Notes
    - CBSD max power
      - CBSD_As have a max EIRP 30 dBm/10 MHz
      - CBSD_Bs have a max EIRP 47 dBm/10 MHz
        - https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=930112
    - RA facilities have an IPC of -247
    - Loss calculations based on formulas in R2-SGN-04
      - https://winnf.memberclicks.net/assets/CBRS/WINNF-TS-0112.pdf
    - Simulation population calculated from https://www.freemaptools.com/find-population.htm

  @slow
  Scenario: Population data is retrieved
    Given a circular area with a radius of 150 km and center coordinates 33.21611, -96.65666
    And census population data
    Then the population in the area should be 7,095,966

  Scenario Template: The number of APs for simulation is calculated
    Given simulation population of 7,095,966
    And a <region_type> location
    When the number of APs for simulation is calculated
    Then the result should be <expected_result>

    Examples:
      | region_type | expected_result |
      | rural       | 54402           |
      | suburban    | 8160            |
      | urban       | 3264            |

  Scenario: Grants are created with a random distribution in a circular area
    Given a seed of 0
    And a circular area with a radius of 150 km
    When grants for the Monte Carlo simulation are created
    Then all distributed points should be within the radius of the center point
    And the furthest distance should be close to 150 km
    And the closest distance should be close to 0 km
    And the highest bearing should be close to 360 degrees
    And the lowest bearing should be close to 0 degrees
    And no points should have exactly the same latitude, longitude, or bearing

  Scenario Template: The number of UEs is created
    Given a <region_type> location
    When UE grants for the Monte Carlo simulation are created
    Then there should be <expected_ue_per_ap> times as many as if AP grants were created

    Examples:
      | region_type | expected_ue_per_ap |
      | rural       | 3                  |
      | suburban    | 20                 |
      | urban       | 50                 |


  Scenario Template: Grants are created with indoor percentage based on region type
    Given a <region_type> location
    When grants for the Monte Carlo simulation are created
    Then <expected_indoor_percentage> of the grants should be indoors

    Examples:
      | region_type | expected_indoor_percentage |
      | rural       | 0.99                       |
      | suburban    | 0.99                       |
      | urban       | 0.8                        |

  Scenario Template: Indoor grants are created with random heights
    Given a <region_type> location
    When <cbsd_type> grants for the Monte Carlo simulation are created
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
    When <cbsd_type> grants for the Monte Carlo simulation are created
    Then outdoor antenna heights should be <expected_height> meters

    Examples:
      | cbsd_type | expected_height |
      | AP        | 6               |
      | UE        | 1.5             |

  Scenario Outline: AP gains are set
    When <cbsd_type> grants for the Monte Carlo simulation are created
    Then the antenna gains should be <expected_gain> meters

    Examples:
      | cbsd_type | expected_gain |
      | AP        | 6             |
      | UE        | 0             |

  Scenario: AP transmission powers are set
    When AP grants for the Monte Carlo simulation are created
    Then the indoor antenna EIRPs should be 26 dBm
    Then the outdoor antenna EIRPs should be 30 dBm

  Scenario: UE transmission powers are set
    When UE grants for the Monte Carlo simulation are created
    Then the antenna EIRPs should be 24 dBm

  Scenario: A monte carlo simulation is run
    Given a function whose results return the next element of [1,2,3,4,5] each time it runs
    When a monte carlo simulation of the function is run
    Then the result should be 3

#  Scenario Outline: Aggregate interference is calculated
#    Given an antenna at McKinney
#    And an exclusion zone distance of 150 km
#    And 100 APs
#    When a monte carlo simulation of <number_of_iterations> iterations for the aggregate interference is run
#    Then the result should be <expected_results>
#
#    Examples:
#      | number_of_iterations | expected_results |
#      | 1                    | -62.72253        |
#      | 2                    | -60.49853        |

  Scenario Outline: A parameter finding algorithm correctly finds inputs, assuming the function results lessen as the input grows
    Given a function whose output is the element of array <result_array> at the given index
    And a target of <target>
    When the algorithm is run
    Then the result should be <expected_result>

    Examples: Finds number while expanding
      | result_array | target | expected_result |
      | [0]          | 0      | 0             |
      | [1,0]        | 0      | 1             |

    Examples: Finds number after expanding
      | result_array | target | expected_result |
      | [3,2,1,0]  | 1        | 2               |

    Examples: Target does not exist
      | result_array | target | expected_result |
      | [3,2,2,0]    | 1      | 3               |

    Examples: Target is greater than what you would get with the minimum input
      | result_array | target | expected_result |
      | [0]          | 1      | 0               |

    Examples: Target is less than what you would get with the maximum input
      | result_array | target | expected_result |
      | [3,2,1,0]    | -1     | 3               |

#  @integration
#  Scenario: The DPA neighborhood is calculated for category A CBSDs
#    Given an antenna at McKinney
#    And an INR of -144
#    When the neighborhood radius is calculated
#    Then the result should be 1
