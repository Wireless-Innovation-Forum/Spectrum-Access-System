# DirectionsTransitDetails

Additional information that is not relevant for other modes of transportation.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**arrival_stop** | [**DirectionsTransitStop**](DirectionsTransitStop.md) |  | [optional] 
**arrival_time** | [**TimeZoneTextValueObject**](TimeZoneTextValueObject.md) |  | [optional] 
**departure_stop** | [**DirectionsTransitStop**](DirectionsTransitStop.md) |  | [optional] 
**departure_time** | [**TimeZoneTextValueObject**](TimeZoneTextValueObject.md) |  | [optional] 
**headsign** | **str** | Specifies the direction in which to travel on this line, as it is marked on the vehicle or at the departure stop. This will often be the terminus station. | [optional] 
**headway** | **int** | Specifies the expected number of seconds between departures from the same stop at this time. For example, with a &#x60;headway&#x60; value of 600, you would expect a ten minute wait if you should miss your bus. | [optional] 
**line** | [**DirectionsTransitLine**](DirectionsTransitLine.md) |  | [optional] 
**num_stops** | **int** | The number of stops from the departure to the arrival stop. This includes the arrival stop, but not the departure stop. For example, if your directions involve leaving from Stop A, passing through stops B and C, and arriving at stop D, &#x60;num_stops&#x60; will return 3. | [optional] 
**trip_short_name** | **str** | The text that appears in schedules and sign boards to identify a transit trip to passengers. The text should uniquely identify a trip within a service day. For example, \&quot;538\&quot; is the &#x60;trip_short_name&#x60; of the Amtrak train that leaves San Jose, CA at 15:10 on weekdays to Sacramento, CA. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


