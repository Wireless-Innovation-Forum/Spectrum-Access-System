# CellTower

Attributes used to describe a cell tower. The following optional fields are not currently used, but may be included if values are available: `age`, `signalStrength`, `timingAdvance`.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**cell_id** | **int** | Unique identifier of the cell. On GSM, this is the Cell ID (CID); CDMA networks use the Base Station ID (BID). WCDMA networks use the UTRAN/GERAN Cell Identity (UC-Id), which is a 32-bit value concatenating the Radio Network Controller (RNC) and Cell ID. Specifying only the 16-bit Cell ID value in WCDMA networks may return inaccurate results. | 
**location_area_code** | **int** | The Location Area Code (LAC) for GSM and WCDMA networks. The Network ID (NID) for CDMA networks. | 
**mobile_country_code** | **int** | The cell tower&#39;s Mobile Country Code (MCC). | 
**mobile_network_code** | **int** | The cell tower&#39;s Mobile Network Code. This is the MNC for GSM and WCDMA; CDMA uses the System ID (SID). | 
**age** | **int** | The number of milliseconds since this cell was primary. If age is 0, the cellId represents a current measurement. | [optional] 
**signal_strength** | **float** | Radio signal strength measured in dBm. | [optional] 
**timing_advance** | **float** | The timing advance value. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


