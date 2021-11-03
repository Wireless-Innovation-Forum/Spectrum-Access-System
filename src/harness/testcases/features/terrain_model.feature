Feature: Terrain model

  Scenario: Coordinates are calculated after moving some distance
    Given Mike starts at location 35.68096477080332, 139.76720809936523
    When Mike moves 1.0 kilometers with bearing 90.0 degrees
    Then Mike is at location 35.68096426403677, 139.77825471732095

  Scenario: A Terrain profile in ITS format is generated
    Given Coordinates 40.81734, -121.46933 and 40.096901173373254, -121.46933
    Then the terrain model should be []
