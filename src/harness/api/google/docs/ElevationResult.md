# ElevationResult


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**elevation** | **float** | The elevation of the location in meters. | 
**location** | [**LatLngLiteral**](LatLngLiteral.md) |  | 
**resolution** | **float** | The value indicating the maximum distance between data points from which the elevation was interpolated, in meters. This property will be missing if the resolution is not known. Note that elevation data becomes more coarse (larger resolution values) when multiple points are passed. To obtain the most accurate elevation value for a point, it should be queried independently. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


