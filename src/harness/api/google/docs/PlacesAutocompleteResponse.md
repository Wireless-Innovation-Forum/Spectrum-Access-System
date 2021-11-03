# PlacesAutocompleteResponse


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**predictions** | [**[PlaceAutocompletePrediction]**](PlaceAutocompletePrediction.md) | Contains an array of predictions.  | 
**status** | [**PlacesAutocompleteStatus**](PlacesAutocompleteStatus.md) |  | 
**error_message** | **str** | When the service returns a status code other than &#x60;OK&lt;&#x60;, there may be an additional &#x60;error_message&#x60; field within the response object. This field contains more detailed information about thereasons behind the given status code. This field is not always returned, and its content is subject to change.  | [optional] 
**info_messages** | **[str]** | When the service returns additional information about the request specification, there may be an additional &#x60;info_messages&#x60; field within the response object. This field is only returned for successful requests. It may not always be returned, and its content is subject to change.  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


