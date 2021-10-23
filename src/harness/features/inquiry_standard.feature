Feature: a CBSD inquiry
  Scenario: Response has no available channel
    Given CBSD has obtained a cbsdId = C inside a GWPZ
    And there is no available channel in the frequency range sent in the inquiredSpectrum parameter
    And CPAS has been triggered to simulate coordination and synchronization tasks
    And Frequency range in the inquiredSpectrum parameter is set to FR
    When DP Test Harness sends a spectrumInquiryRequest message to SAS UU
    Then SAS response includes cbsdId = C.
    And availableChannel has zero elements
    And responseCode = 0
