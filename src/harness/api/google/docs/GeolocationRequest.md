# GeolocationRequest

The request body must be formatted as JSON. The following fields are supported, and all fields are optional.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**home_mobile_country_code** | **int** | The cell tower&#39;s Mobile Country Code (MCC). | [optional] 
**home_mobile_network_code** | **int** | The cell tower&#39;s Mobile Network Code. This is the MNC for GSM and WCDMA; CDMA uses the System ID (SID). | [optional] 
**radio_type** | **str** | The mobile radio type. Supported values are lte, gsm, cdma, and wcdma. While this field is optional, it should be included if a value is available, for more accurate results. | [optional] 
**carrier** | **str** | The carrier name. | [optional] 
**consider_ip** | **str** | Specifies whether to fall back to IP geolocation if wifi and cell tower signals are not available. Defaults to true. Set considerIp to false to disable fall back. | [optional] 
**cell_towers** | [**[CellTower]**](CellTower.md) | The request body&#39;s cellTowers array contains zero or more cell tower objects. | [optional] 
**wifi_access_points** | [**[WiFiAccessPoint]**](WiFiAccessPoint.md) | An array of two or more WiFi access point objects. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


