Feature: DPA Neighborhood

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

  Scenario Outline: A binary search algorithm correctly finds inputs, assuming the function results lessen as the input grows
    Given a function whose output is the element of array <result_array> at the given index
    And a target of <target>
    When the algorithm is run
    Then the resulting input should be <expected_input>
    And the resulting return value should be <expected_value>

    Examples: Finds number while expanding
      | result_array | target | expected_input | expected_value |
      | [0]          | 0      | 0              | 0              |
      | [1,0]        | 0      | 1              | 0              |

    Examples: Finds number after expanding
      | result_array | target | expected_input | expected_value |
      | [3,2,1,0]    | 1      | 2              | 1              |

    Examples: Target does not exist but is in range
      | result_array | target | expected_input | expected_value |
      | [3,2,2,0]    | 1      | 3              | 0              |

    Examples: Target is greater than what you would get with the minimum input
      | result_array | target | expected_input | expected_value |
      | [0]          | 1      | 0              | 0              |

    Examples: Target is less than what you would get with the maximum input
      | result_array | target | expected_input | expected_value |
      | [3,2,1,0]    | -1     | 3              | 0              |

  Scenario Template: A monte carlo simulation is run
    Given functions whose results return the next element of <function_results> each time it runs
    When a monte carlo simulation of the function is run for the 95 percentile
    Then the simulation results should be <expected_simulation_results>

    Examples:
      | function_results            | expected_simulation_results |
      | [[1,2,3,4,5]]               | [4]                         |
      | [[1,2,3,4,5], [10,9,8,7,6]] | [4, 9]                      |

  Scenario: Logging is captured
    Given random seed 0
    And 2 APs
    And 2 monte carlo iterations
    When the neighborhood radius is calculated
    Then the output log should be
      """
      Monte Carlo iteration 1
          CBSD 1 / 2
          CBSD 2 / 2

          Found parameter
              Input: 4
              Value: -195.99056997789654

          CBSD 1 / 6
          CBSD 2 / 6
          CBSD 3 / 6
          CBSD 4 / 6
          CBSD 5 / 6
          CBSD 6 / 6

          Found parameter
              Input: 0
              Value: -152.82204399324985

      Monte Carlo iteration 2
          CBSD 1 / 2
          CBSD 2 / 2

          Found parameter
              Input: 1
              Value: -256.2022715421642

          CBSD 1 / 6
          CBSD 2 / 6
          CBSD 3 / 6
          CBSD 4 / 6
          CBSD 5 / 6
          CBSD 6 / 6

          Found parameter
              Input: 0
              Value: -147.84572943335849


      Results for APs:
          50th percentile: 1
          95th percentile: 1
          Standard Deviation: 2.1213203435596424
          Minimum: 1
          Maximum: 4

      Results for UEs:
          50th percentile: 0
          95th percentile: 0
          Standard Deviation: 0.0
          Minimum: 0
          Maximum: 0

      Final results:
          Distance: 1

      """


  @slow
  Scenario Template: The DPA neighborhood is calculated; Hat Creek 200km dbw 3 iterations
#    Hat Creek census population number of APs is 102,267
#    McKinney census population number of UEs is 223,182
#    Moorestown census population number of UEs is 571,850

    Given an antenna at <dpa_name>
    And population by <population_type>
    And a simulation area radius of <simulation_area_radius>
    And <number_of_iterations> monte carlo iterations
    When the neighborhood radius is calculated
    Then the result should be <expected_result>

    Examples:
      | dpa_name  | population_type | simulation_area_radius | number_of_iterations | expected_result | runtime         | access_point_distance | user_equipment_distance | notes |
#      | Hat Creek | census radius   | 200                   | 3                     | 90              | 13:16:51.491462 | 88                    | 90                      | dBW   |
#      | McKinney   | census radius  | 200                   | 3                     | 26              | 6:14:50.559416  | 21                    | 26                      | dBW   |
#      | Hat Creek | census radius   | 500                   | 3                     | 598           |  |                     |                       | dBm   |
