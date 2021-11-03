# DirectionsLeg


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**end_address** | **str** | Contains the human-readable address (typically a street address) from reverse geocoding the &#x60;end_location&#x60; of this leg. This content is meant to be read as-is. Do not programmatically parse the formatted address. | 
**end_location** | [**LatLngLiteral**](LatLngLiteral.md) |  | 
**start_address** | **str** | Contains the human-readable address (typically a street address) resulting from reverse geocoding the &#x60;start_location&#x60; of this leg. This content is meant to be read as-is. Do not programmatically parse the formatted address. | 
**start_location** | [**LatLngLiteral**](LatLngLiteral.md) |  | 
**steps** | [**[DirectionsStep]**](DirectionsStep.md) | An array of steps denoting information about each separate step of the leg of the journey. | 
**traffic_speed_entry** | [**[DirectionsTrafficSpeedEntry]**](DirectionsTrafficSpeedEntry.md) | Information about traffic speed along the leg. | 
**via_waypoint** | [**[DirectionsViaWaypoint]**](DirectionsViaWaypoint.md) | The locations of via waypoints along this leg. | 
**arrival_time** | [**TimeZoneTextValueObject**](TimeZoneTextValueObject.md) |  | [optional] 
**departure_time** | [**TimeZoneTextValueObject**](TimeZoneTextValueObject.md) |  | [optional] 
**distance** | [**TextValueObject**](TextValueObject.md) |  | [optional] 
**duration** | [**TextValueObject**](TextValueObject.md) |  | [optional] 
**duration_in_traffic** | [**TextValueObject**](TextValueObject.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


