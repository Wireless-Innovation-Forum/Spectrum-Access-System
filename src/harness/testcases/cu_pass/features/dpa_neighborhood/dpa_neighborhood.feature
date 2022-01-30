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


  Scenario: A quick run is performed
    Given random seed 0
    And 2 category A UEs
    And 1 category B UEs
    And 2 monte carlo iterations
    When the neighborhood radius is calculated
    Then the resulting distance should be 128
    And the resulting interference should be -159.60616073654418


  Scenario: Only one iteration is performed, so standard deviation cannot be calculated
    Given random seed 0
    And 2 category A UEs
    And 1 monte carlo iterations
    When the neighborhood radius is calculated
    Then it should run without error


  Scenario: Zero APs are simulated
    Given random seed 0
    And 0 category A UEs
    And 0 category B UEs
    And 1 monte carlo iterations
    When the neighborhood radius is calculated
    Then the resulting distance should be 0
    Then the resulting interference should be -infinity


  Scenario: No interference outside of exclusion zone
    Given random seed 0
    And 1 category A UEs
    And 1 category B UEs
    And 1 monte carlo iterations
    And a category A simulation distance of 1 km
    And a category B simulation distance of 1 km
    When the neighborhood radius is calculated
    Then the resulting interference should be -infinity


#  @slow
#  Scenario Template: The DPA neighborhood is calculated; Hat Creek 100km 1000 iterations
#    Given an antenna at <dpa_name>
#    And a simulation area radius of <simulation_area_radius>
#    And <number_of_iterations> monte carlo iterations
#    When the neighborhood radius is calculated
#    Then the resulting distance should be <expected_distance>
#    Then the resulting interference should be <expected_interference>
#
#    Examples:
#      | dpa_name  | simulation_area_radius | number_of_iterations | expected_distance | expected_interference | runtime         | access_point_distance | user_equipment_distance | notes |
##      | Hat Creek | 200                    | 1000                 | -1                | -1                    |  |                     |                       |  |
##      | Hat Creek | 200                    | 100                  | 91                | -1                    | 15:27:29.710758 | 90                    | 91                      |  |
##      | Hat Creek | 100                    | 1000                 | 90                | -1                    | 10:15:09.057322 | 90                    | 90                      |  |
##      | Hat Creek | 100                    | 100                  | 90                | -1                    | 1:02:07.166180  | 90                    | 90                      |  |
##      | Hat Creek | 200                    | 3                    | 89                | -1                    | 1:06:35.718954  | 89                    | 88                      |  |
##      | Hat Creek | 150                    | 3                    | 88                | -1                    | 0:09:06.980410  | 48                    | 88                      |  |
##      | McKinney  | 200                    | 3                    | 25                | -1                    | 1:51:58.489413  | 21                    | 25                      |    |
