# SnappedPoint


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**location** | [**LatitudeLongitudeLiteral**](LatitudeLongitudeLiteral.md) |  | 
**place_id** | **str** | A unique identifier for a place. All place IDs returned by the Roads API correspond to road segments. | 
**original_index** | **float** | An integer that indicates the corresponding value in the original request. Each value in the request should map to a snapped value in the response. However, if you&#39;ve set interpolate&#x3D;true, then it&#39;s possible that the response will contain more coordinates than the request. Interpolated values will not have an &#x60;originalIndex&#x60;. These values are indexed from &#x60;0&#x60;, so a point with an originalIndex of &#x60;4&#x60; will be the snapped value of the 5th latitude/longitude passed to the path parameter. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


