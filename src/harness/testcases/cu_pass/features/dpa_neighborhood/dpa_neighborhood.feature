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
      | [3,2,1,0]    | -1     | 4               |

  Scenario Template: A monte carlo simulation is run
    Given functions whose results return the next element of <function_results> each time it runs
    When a monte carlo simulation of the function is run for the 95 percentile
    Then the simulation results should be <expected_simulation_results>

    Examples:
      | function_results            | expected_simulation_results |
      | [[1,2,3,4,5]]               | [4]                         |
      | [[1,2,3,4,5], [10,9,8,7,6]] | [4, 9]                      |

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
#    McKinney census population number of UEs is 223,182
#    Moorestown census population number of UEs is 571,850

    Given an antenna at <dpa_name>
    And <organization_interference> interference
    And population by <population_type>
    And number of APs using <number_of_aps_type> analysis
    And <number_of_iterations> monte carlo iterations
    When the neighborhood radius is calculated
    Then the result should be <expected_result>

    Examples:
      | dpa_name  | organization_interference | population_type | number_of_aps_type | number_of_iterations | expected_result | runtime         | access_point_distance | user_equipment_distance | notes |
      | Hat Creek | NTIA                      | census radius   | shipborne          | 3                    |               |                 |                       |                         |     |

#      | McKinney   | NTIA                      | region type     | shipborne          | 1                    | 75              |                 |                       |                         |     |

#      | McKinney   | NTIA                      | census radius   | shipborne          | 1                    | 101              | 2:17:52.193526 | 90                     | 101                    |     |
#      | McKinney   | NTIA                      | census radius   | shipborne          | 3                    | 102              | 5:40:21.731362 | 87                     | 102                     |    |

#      | McKinney   | NTIA                      | region type     | shipborne          | 3                    | 130              | 0:23:25.460508  | 113                   | 130                     | no receiver gain |
#      | McKinney   | NTIA                      | census radius   | shipborne          | 3                    | 247              | 6:43:18.520841  | 230                   | 247                     | no receiver gain |

#      | Moorestown | NTIA                      | region type     | shipborne          | 3                    | 109              | 1:39:39.110491  | 62                    | 109                     | no receiver gain |
#      | Moorestown | NTIA                      | census radius   | shipborne          | 3                    | 173            | 8:27:01.674526    | 93                    | 173                      | no receiver gain |

#      | McKinney   | NTIA                      | region type     | shipborne          | 100                  | 139            | 5:59:26.229337    | 125                   | 139                     | no receiver gain |
