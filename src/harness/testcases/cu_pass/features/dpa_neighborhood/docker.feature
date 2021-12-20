Feature: Docker run
  Scenario: Logs are written to s3
    When the main docker command is run
    Then the file uploaded to S3 should be
      """
      content
      """
