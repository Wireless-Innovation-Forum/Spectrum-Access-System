Feature: Docker run
  Scenario: Logs are written to s3
    Given random seed 0
    When the main docker command is run
    Then the file uploaded to S3 should be
      """
      Monte Carlo iteration 1
          CBSD 1 / 1

          Found parameter
              Input: 1
              Value: -inf

          CBSD 1 / 3
          CBSD 2 / 3
          CBSD 3 / 3

          Found parameter
              Input: 1
              Value: -228.21931595139122


      Results for APs:
          50th percentile: 1
          95th percentile: 1
          Standard Deviation: 0
          Minimum: 1
          Maximum: 1

      Results for UEs:
          50th percentile: 1
          95th percentile: 1
          Standard Deviation: 0
          Minimum: 1
          Maximum: 1

      """
