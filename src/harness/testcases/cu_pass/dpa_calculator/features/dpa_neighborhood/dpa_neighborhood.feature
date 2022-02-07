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
    - Simulation population confirmed using https://www.freemaptools.com/find-population.htm


  Scenario Template: A quick run is performed with UEs
    Given random seed 0
    And 2 category A UEs
    And 1 category B UEs
    And 2 monte carlo iterations
    And UE runs are included
    When the neighborhood radius is calculated
    Then the resulting category <cbsd_category> <cbsd_type> distance should be <expected_distance>
    And the resulting category <cbsd_category> <cbsd_type> interference should be <expected_interference>

    Examples:
      | cbsd_type | cbsd_category | expected_distance | expected_interference |
      | AP        | A             | 0                 | -151.48616716614754   |
      | AP        | B             | 0                 | -160.19041297883996   |
      | UE        | A             | 0                 | -215.82320664154682   |
      | UE        | B             | 0                 | -200.2170839780984    |


  Scenario Template: A quick run is performed without UEs
    Given random seed 0
    And 2 category A UEs
    And 1 category B UEs
    And 2 monte carlo iterations
    When the neighborhood radius is calculated
    Then the resulting category <cbsd_category> <cbsd_type> distance should be <expected_distance>
    And the resulting category <cbsd_category> <cbsd_type> interference should be <expected_interference>
    And the resulting UE distance should not exist
    And the resulting UE interference should not exist

    Examples:
      | cbsd_type | cbsd_category | expected_distance | expected_interference |
      | AP        | A             | 0                 | -151.48616716614754   |
      | AP        | B             | 0                 | -160.19041297883996   |


  Scenario: Only one iteration is performed, so standard deviation cannot be calculated
    Given random seed 0
    And 2 category A UEs
    And 1 monte carlo iterations
    When the neighborhood radius is calculated
    Then it should run without error


  Scenario Template: Zero APs are simulated
    Given random seed 0
    And 0 category A UEs
    And 0 category B UEs
    And 1 monte carlo iterations
    When the neighborhood radius is calculated
    Then the resulting category <cbsd_category> <cbsd_type> distance should be <expected_distance>
    And the resulting category <cbsd_category> <cbsd_type> interference should be <expected_interference>

    Examples:
      | cbsd_type | cbsd_category | expected_distance | expected_interference |
      | AP        | A             | 0                 | -infinity             |
      | AP        | B             | 0                 | -infinity             |


  Scenario Template: No interference outside of exclusion zone
    Given random seed 0
    And 1 category A UEs
    And 1 category B UEs
    And 1 monte carlo iterations
    And a category A simulation distance of 1 km
    And a category B simulation distance of 1 km
    When the neighborhood radius is calculated
    Then the resulting category <cbsd_category> <cbsd_type> interference should be <expected_interference>

    Examples:
      | cbsd_type | cbsd_category | expected_interference |
      | AP        | A             | -infinity             |
      | AP        | B             | -infinity             |


  @slow
  Scenario Template: The DPA neighborhood is calculated
    Given random seed 0
    And an antenna at <dpa_name>
    And a category A simulation distance of <category_a_radius> km
    And a category B simulation distance of <category_b_radius> km
    And <number_of_iterations> monte carlo iterations
    When the neighborhood radius is calculated
    Then the resulting category A AP distance should be <expected_distance_category_a>
    And the resulting category B AP distance should be <expected_distance_category_b>
    And the resulting category A AP interference should be <expected_interference_category_a>
    And the resulting category B AP interference should be <expected_interference_category_b>

    Examples:
      | dpa_name   | category_a_radius | category_b_radius | number_of_iterations | expected_distance_category_a | expected_distance_category_b | expected_interference_category_a | expected_interference_category_b |
      | Moorestown | 160               | 400               | 1                    | 112                          | 304                          | -157.71421804594996              | -157.77927922588643              |
