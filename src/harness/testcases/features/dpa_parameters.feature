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

  Scenario: The number of APs for simulation is calculated
    Given the radar at McKinney
    And simulation population of 6,384,440 with a 150 km radius
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

  Scenario: A CBSD_A is outside of the neighborhood
    Given CBSD_A_1 is 150.0 kilometers away from McKinney
    Then the propagation loss is high enough to make the interference negligible

  Scenario: A Monte Carlo simulation is run
    Given an antenna at McKinney
    And an exclusion zone distance of 150 km
    When a monte carlo simulation of 1,000 iterations of the aggregate interference is run
    Then the probability of exceeding -144 INR is 95%
