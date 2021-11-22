Feature: DPA Parameters

  Definitions
    - CBSD_A...: Citizens Broadband radio Service Device, category A
    - CBSD_B...: Citizens Broadband radio Service Device, category B
    - EIRP.....: Effective isotropic radiated power
    - INR......: Interference to noise ratio
    - IPC......: Interference protection criteria
    - R_C_DPA_A: Radius of Co-channel frequency range Dynamic Protection Area for category A devices
    - RA.......: Radio astronomy

  Notes
    - CBSD max power
      - CBSD_As have a max EIRP 30 dBm/10 MHz
      - CBSD_Bs have a max EIRP 47 dBm/10 MHz
        - https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=930112
    - RA facilities have an IPC of -247
    - Loss calculations based on formulas in R2-SGN-04
      - https://winnf.memberclicks.net/assets/CBRS/WINNF-TS-0112.pdf
    - Simulation population calculated from https://www.freemaptools.com/find-population.htm

  @integration
  Scenario: Population data is retrieved
    Given a circular area with a radius of 150 km and center coordinates 33.21611, -96.65666
    And census population data
    Then the population in the area should be 7,095,966

  Scenario: The number of APs for simulation is calculated
    Given simulation population of 7,095,966
    Then the number of APs for simulation is 25,538

  Scenario: Geographic points are randomly positioned in a circular area
    Given a seed of 0
    And a circular area with a radius of 150 km and center coordinates 33.21611, -96.65666
    When 30,000 points are randomly generated
    Then all distributed points should be within the radius of the center point
    And the furthest distance should be close to 150 km
    And the closest distance should be close to 0 km
    And the highest bearing should be close to 360 degrees
    And the lowest bearing should be close to 0 degrees
    And no points should have exactly the same latitude, longitude, or bearing

  Scenario: A monte carlo simulation is run
    Given a function whose results return the next element of [1,2,3,4,5] each time it runs
    When a monte carlo simulation of the function is run
    Then the result should be 3

  Scenario Outline: Aggregate interference is calculated
    Given an antenna at McKinney
    And an exclusion zone distance of 150 km
    And 100 APs
    When a monte carlo simulation of <number_of_iterations> iterations for the aggregate interference is run
    Then the result should be <expected_results>

    Examples:
      | number_of_iterations | expected_results |
      | 1                    | -62.72253        |
      | 2                    | -60.49853        |

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

  @integration
  Scenario: The DPA neighborhood is calculated for category A CBSDs
    Given an antenna at McKinney
    And an INR of -144
    When the neighborhood radius is calculated
    Then the result should be 1
