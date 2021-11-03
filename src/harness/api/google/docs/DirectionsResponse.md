# DirectionsResponse


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**routes** | [**[DirectionsRoute]**](DirectionsRoute.md) | Contains an array of routes from the origin to the destination. Routes consist of nested Legs and Steps. | 
**status** | [**DirectionsStatus**](DirectionsStatus.md) |  | 
**geocoded_waypoints** | [**[DirectionsGeocodedWaypoint]**](DirectionsGeocodedWaypoint.md) | Contains an array with details about the geocoding of origin, destination and waypoints. Elements in the geocoded_waypoints array correspond, by their zero-based position, to the origin, the waypoints in the order they are specified, and the destination.  These details will not be present for waypoints specified as textual latitude/longitude values if the service returns no results. This is because such waypoints are only reverse geocoded to obtain their representative address after a route has been found. An empty JSON object will occupy the corresponding places in the geocoded_waypoints array.  | [optional] 
**available_travel_modes** | [**[TravelMode]**](TravelMode.md) | Contains an array of available travel modes. This field is returned when a request specifies a travel mode and gets no results. The array contains the available travel modes in the countries of the given set of waypoints. This field is not returned if one or more of the waypoints are &#39;via waypoints&#39;. | [optional] 
**error_message** | **str** | When the service returns a status code other than &#x60;OK&#x60;, there may be an additional &#x60;error_message&#x60; field within the response object. This field contains more detailed information about thereasons behind the given status code. This field is not always returned, and its content is subject to change.  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


