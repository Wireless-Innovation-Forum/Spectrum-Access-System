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
    Then the population in the area should be 8,968,197

  Scenario: The number of APs for simulation is calculated
    Given simulation population of 6,384,440 with a 150 km radius
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

#  Scenario: Signal loss is calculated
#    Given CBSD_A_1 is 80.0 kilometers away from coordinates 33.21611, -96.65666
#    Then the loss should be 1
#
  Scenario: Aggregate interference is calculated
    Given an antenna at McKinney
    And an exclusion zone distance of 150 km
    And 5,000 APs
    When a monte carlo simulation of 1,000 iterations of the aggregate interference is run
    Then the max aggregate interference is -62.72253
