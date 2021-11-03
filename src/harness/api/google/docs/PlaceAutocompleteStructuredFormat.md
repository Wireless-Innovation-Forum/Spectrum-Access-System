# PlaceAutocompleteStructuredFormat


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**main_text** | **str** | Contains the main text of a prediction, usually the name of the place. | 
**main_text_matched_substrings** | [**[PlaceAutocompleteMatchedSubstring]**](PlaceAutocompleteMatchedSubstring.md) | Contains an array with &#x60;offset&#x60; value and &#x60;length&#x60;. These describe the location of the entered term in the prediction result text, so that the term can be highlighted if desired. | 
**secondary_text** | **str** | Contains the secondary text of a prediction, usually the location of the place. | 
**secondary_text_matched_substrings** | [**[PlaceAutocompleteMatchedSubstring]**](PlaceAutocompleteMatchedSubstring.md) | Contains an array with &#x60;offset&#x60; value and &#x60;length&#x60;. These describe the location of the entered term in the prediction result text, so that the term can be highlighted if desired. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


