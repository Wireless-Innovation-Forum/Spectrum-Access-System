# PlaceAutocompletePrediction


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**description** | **str** | Contains the human-readable name for the returned result. For &#x60;establishment&#x60; results, this is usually the business name. This content is meant to be read as-is. Do not programmatically parse the formatted address. | 
**matched_substrings** | [**[PlaceAutocompleteMatchedSubstring]**](PlaceAutocompleteMatchedSubstring.md) | A list of substrings that describe the location of the entered term in the prediction result text, so that the term can be highlighted if desired. | 
**structured_formatting** | [**PlaceAutocompleteStructuredFormat**](PlaceAutocompleteStructuredFormat.md) |  | 
**terms** | [**[PlaceAutocompleteTerm]**](PlaceAutocompleteTerm.md) | Contains an array of terms identifying each section of the returned description (a section of the description is generally terminated with a comma). Each entry in the array has a &#x60;value&#x60; field, containing the text of the term, and an &#x60;offset&#x60; field, defining the start position of this term in the description, measured in Unicode characters. | 
**place_id** | **str** | A textual identifier that uniquely identifies a place. To retrieve information about the place, pass this identifier in the placeId field of a Places API request. For more information about place IDs, see the [Place IDs](https://developers.google.com/maps/documentation/places/web-service/place-id) overview. | [optional] 
**reference** | **str** | (Deprecated) See place_id. | [optional] 
**types** | **[str]** | Contains an array of types that apply to this place. For example: &#x60;[ \&quot;political\&quot;, \&quot;locality\&quot; ]&#x60; or &#x60;[ \&quot;establishment\&quot;, \&quot;geocode\&quot;, \&quot;beauty_salon\&quot; ]&#x60;. The array can contain multiple values. Learn more about [Place types](https://developers.google.com/maps/documentation/places/web-service/supported_types).  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


