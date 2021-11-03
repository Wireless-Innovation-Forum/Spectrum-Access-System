# DistanceMatrixResponse


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**origin_addresses** | **[str]** | An array of addresses as returned by the API from your original request. These are formatted by the geocoder and localized according to the language parameter passed with the request. This content is meant to be read as-is. Do not programatically parse the formatted addresses. | 
**destination_addresses** | **[str]** | An array of addresses as returned by the API from your original request. As with &#x60;origin_addresses&#x60;, these are localized if appropriate. This content is meant to be read as-is. Do not programatically parse the formatted addresses. | 
**rows** | [**[DistanceMatrixRow]**](DistanceMatrixRow.md) | An array of elements, which in turn each contain a &#x60;status&#x60;, &#x60;duration&#x60;, and &#x60;distance&#x60; element. | 
**status** | [**DistanceMatrixStatus**](DistanceMatrixStatus.md) |  | 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


