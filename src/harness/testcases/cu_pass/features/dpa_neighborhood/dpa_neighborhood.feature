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
          CBSD 1 / 6
          CBSD 2 / 6
          CBSD 3 / 6
          CBSD 4 / 6
          CBSD 5 / 6
          CBSD 6 / 6

      Monte Carlo iteration 2
          CBSD 1 / 2
          CBSD 2 / 2
          CBSD 1 / 6
          CBSD 2 / 6
          CBSD 3 / 6
          CBSD 4 / 6
          CBSD 5 / 6
          CBSD 6 / 6

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


#  @slow
#  Scenario: The DPA neighborhood is calculated with 50 percentil
##    Census number of APs for McKinney: 185,730
##    Region type rural number of APs: 653,558
##    72 km with 1 iteration with population census data
##    87 km with 1 iteration with population census data and no double building loss from winnforum itm
##    [500 * 4] km with 4 iterations with population census data and only eirp in interference
##    473 km with 1 iterations with population census data and only eirp and propagation loss
##    314 km with 1 iterations with population region type data and only eirp and propagation loss
##    167 km with 1 iterations with population region type data and only eirp and propagation loss and building loss
##    121 km with 1 iterations with population region type data and only eirp and propagation loss and building loss and insertion losses
##    113 km with 1 iterations with population region type data and only eirp and propagation loss and building loss and insertion losses and clutter loss
##    284 km with 1 iterations with population census data and only eirp and propagation loss and building loss and clutter loss
##    131 km with 10 iterations with population region type data and only eirp and propagation loss and building loss and clutter loss
##      (2:17:17.486305)

  @slow
  Scenario Template: The DPA neighborhood is calculated
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
      | McKinney | census radius   | 500                   | 3                     |               | |                     |                       | dBm   |
#      | Hat Creek | census radius   | 500                   | 3                     | 598           |  |                     |                       | dBm   |
      | Hat Creek | census radius   | 500                   | 3                     |                 |                 |                       |                         | dBW     |

#      | McKinney   | region type    | 1                    | 75              |                 |                       |                         |     |

#      | McKinney   | census radius  | 1                    | 101              | 2:17:52.193526 | 90                     | 101                    |     |
#      | McKinney   | census radius  | 200                    | 3                    | 102              | 5:40:21.731362 | 87                     | 102                     |    |

#      | McKinney   | region type    | 3                    | 130              | 0:23:25.460508  | 113                   | 130                     | no receiver gain |
#      | McKinney   | census radius  | 3                    | 247              | 6:43:18.520841  | 230                   | 247                     | no receiver gain |

#      | Moorestown | region type    | 3                    | 109              | 1:39:39.110491  | 62                    | 109                     | no receiver gain |
#      | Moorestown | census radius  | 3                    | 173            | 8:27:01.674526    | 93                    | 173                      | no receiver gain |

#      | McKinney   | region type    | 100                  | 139            | 5:59:26.229337    | 125                   | 139                     | no receiver gain |
