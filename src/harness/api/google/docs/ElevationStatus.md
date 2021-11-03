# ElevationStatus

Status codes returned by service. - `OK` indicating the API request was successful. - `DATA_NOT_AVAILABLE` indicating that there's no available data for the input locations.  - `INVALID_REQUEST` indicating the API request was malformed. - `OVER_DAILY_LIMIT` indicating any of the following:   - The API key is missing or invalid.   - Billing has not been enabled on your account.   - A self-imposed usage cap has been exceeded.   - The provided method of payment is no longer valid (for example, a credit card has expired). - `OVER_QUERY_LIMIT` indicating the requestor has exceeded quota. - `REQUEST_DENIED` indicating the API did not complete the request. - `UNKNOWN_ERROR` indicating an unknown error. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | Status codes returned by service. - &#x60;OK&#x60; indicating the API request was successful. - &#x60;DATA_NOT_AVAILABLE&#x60; indicating that there&#39;s no available data for the input locations.  - &#x60;INVALID_REQUEST&#x60; indicating the API request was malformed. - &#x60;OVER_DAILY_LIMIT&#x60; indicating any of the following:   - The API key is missing or invalid.   - Billing has not been enabled on your account.   - A self-imposed usage cap has been exceeded.   - The provided method of payment is no longer valid (for example, a credit card has expired). - &#x60;OVER_QUERY_LIMIT&#x60; indicating the requestor has exceeded quota. - &#x60;REQUEST_DENIED&#x60; indicating the API did not complete the request. - &#x60;UNKNOWN_ERROR&#x60; indicating an unknown error.  |  must be one of ["OK", "DATA_NOT_AVAILABLE", "INVALID_REQUEST", "OVER_DAILY_LIMIT", "OVER_QUERY_LIMIT", "REQUEST_DENIED", "UNKNOWN_ERROR", ]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


