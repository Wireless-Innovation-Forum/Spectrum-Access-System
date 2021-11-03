Feature: DPA Parameters

  Definitions
    - CBSD_A...: Citizens Broadband radio Service Device, category A
    - CBSD_B...: Citizens Broadband radio Service Device, category B
    - EIRP.....: Effective isotropic radiated power
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

  Scenario: A CBSD_A is outside of the neighborhood
    Given CBSD_A_1 is 150.0 kilometers away from McKinney
    Then the propagation loss is high enough to make the interference negligible

  Scenario: The Category A Neighborhood for RA facilities is calculated
#    Given CBSD_A_1 is 81 kilometeres away from Hat Creek
#    Then R_C_DPA_A_HatCreek is 50 kilometers
