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


  @slow
  Scenario Template: The DPA neighborhood is calculated; Hat Creek 100km 1000 iterations
    Given an antenna at <dpa_name>
    And population by <population_type>
    And a simulation area radius of <simulation_area_radius>
    And <number_of_iterations> monte carlo iterations
    When the neighborhood radius is calculated
    Then the result should be <expected_result>

    Examples:
      | dpa_name  | population_type | simulation_area_radius | number_of_iterations | expected_result | runtime         | access_point_distance | user_equipment_distance | notes |
#      | Hat Creek | census radius   | 200                   | 1000                  |               |  |                     |                       |  |
#      | Hat Creek | census radius   | 200                   | 100                   |               |  |                     |                       |  |
      | Hat Creek | census radius   | 100                   | 1000                  | -1               |  |                     |                       |  |
#      | Hat Creek | census radius   | 100                   | 100                   | 90              | 1:02:07.166180 | 90                    | 90                      |  |
#      | Hat Creek | census radius   | 200                   | 3                     | 89              |  |                     |                       |  |
#      | Hat Creek | census radius   | 150                   | 3                     | 88              | 0:09:06.980410  | 48                    | 88                      |  |
#      | McKinney   | census radius  | 200                   | 3                     | 25              | 1:51:58.489413  | 21                    | 25                      |    |
