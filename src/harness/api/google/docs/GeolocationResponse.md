# GeolocationResponse

A successful geolocation request will return a JSON-formatted response defining a location and radius.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**location** | [**LatLngLiteral**](LatLngLiteral.md) |  | 
**accuracy** | **float** | The accuracy of the estimated location, in meters. This represents the radius of a circle around the given &#x60;location&#x60;. If your Geolocation response shows a very high value in the &#x60;accuracy&#x60; field, the service may be geolocating based on the  request IP, instead of WiFi points or cell towers. This can happen if no cell towers or access points are valid or recognized. To confirm that this is the issue, set &#x60;considerIp&#x60; to &#x60;false&#x60; in your request. If the response is a &#x60;404&#x60;, you&#39;ve confirmed that your &#x60;wifiAccessPoints&#x60; and &#x60;cellTowers&#x60; objects could not be geolocated. | 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


