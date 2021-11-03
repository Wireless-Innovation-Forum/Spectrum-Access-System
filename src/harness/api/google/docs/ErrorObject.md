# ErrorObject


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**code** | **float** | This is the same as the HTTP status of the response. | 
**message** | **str** | A short description of the error. | 
**errors** | [**[ErrorDetail]**](ErrorDetail.md) | A list of errors which occurred. Each error contains an identifier for the type of error and a short description. | 
**status** | **str** | A status code that indicates the error type. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


