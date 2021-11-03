# TimeZoneResponse


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | [**TimeZoneStatus**](TimeZoneStatus.md) |  | 
**dst_offset** | **float** | The offset for daylight-savings time in seconds. This will be zero if the time zone is not in Daylight Savings Time during the specified &#x60;timestamp&#x60;. | [optional] 
**raw_offset** | **float** | The offset from UTC (in seconds) for the given location. This does not take into effect daylight savings. | [optional] 
**time_zone_id** | **str** | a string containing the ID of the time zone, such as \&quot;America/Los_Angeles\&quot; or \&quot;Australia/Sydney\&quot;. These IDs are defined by [Unicode Common Locale Data Repository (CLDR) project](http://cldr.unicode.org/), and currently available in file timezone.xml. When a timezone has several IDs, the canonical one is returned. In xml responses, this is the first alias of each timezone. For example, \&quot;Asia/Calcutta\&quot; is returned, not \&quot;Asia/Kolkata\&quot;. | [optional] 
**time_zone_name** | **str** | The long form name of the time zone. This field will be localized if the language parameter is set. eg. &#x60;Pacific Daylight Time&#x60; or &#x60;Australian Eastern Daylight Time&#x60;. | [optional] 
**error_message** | **str** | Detailed information about the reasons behind the given status code. Included if status other than &#x60;Ok&#x60;. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


