# GeocodingGeometry

An object describing the location.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**location** | [**LatLngLiteral**](LatLngLiteral.md) |  | 
**location_type** | **str** | Stores additional data about the specified location. The following values are currently supported:  - \&quot;ROOFTOP\&quot; indicates that the returned result is a precise geocode for which we have location information accurate down to street address precision. - \&quot;RANGE_INTERPOLATED\&quot; indicates that the returned result reflects an approximation (usually on a road) interpolated between two precise points (such as intersections). Interpolated results are generally returned when rooftop geocodes are unavailable for a street address. - \&quot;GEOMETRIC_CENTER\&quot; indicates that the returned result is the geometric center of a result such as a polyline (for example, a street) or polygon (region). - \&quot;APPROXIMATE\&quot; indicates that the returned result is approximate.  | 
**viewport** | [**Bounds**](Bounds.md) |  | 
**bounds** | [**Bounds**](Bounds.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


