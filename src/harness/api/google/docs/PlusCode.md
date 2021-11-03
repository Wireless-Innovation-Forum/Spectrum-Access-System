# PlusCode

An encoded location reference, derived from latitude and longitude coordinates, that represents an area, 1/8000th of a degree by 1/8000th of a degree (about 14m x 14m at the equator) or smaller. Plus codes can be used as a replacement for street addresses in places where they do not exist (where buildings are not numbered or streets are not named).

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**global_code** | **str** | The &#x60;global_code&#x60; is a 4 character area code and 6 character or longer local code (&#x60;849VCWC8+R9&#x60;). | 
**compound_code** | **str** | The &#x60;compound_code&#x60; is a 6 character or longer local code with an explicit location (&#x60;CWC8+R9, Mountain View, CA, USA&#x60;). Some APIs may return an empty string if the &#x60;compound_code&#x60; is not available. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


