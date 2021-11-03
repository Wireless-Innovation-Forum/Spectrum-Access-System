Feature: DPA Parameters

  Definitions
    - CBSD_A...: Citizens Broadband radio Service Device, category A
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

  Scenario: The Category A Neighborhood is calculated
    Given CBSD_A_1 is 81 kilometeres away from Hat Creek
    Then R_C_DPA_A_HatCreek is 50 kilometers
