# DistanceMatrixElementStatus

- `OK` indicates the response contains a valid result. - `NOT_FOUND` indicates that the origin and/or destination of this pairing could not be geocoded. - `ZERO_RESULTS` indicates no route could be found between the origin and destination. - `MAX_ROUTE_LENGTH_EXCEEDED` indicates the requested route is too long and cannot be processed. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | - &#x60;OK&#x60; indicates the response contains a valid result. - &#x60;NOT_FOUND&#x60; indicates that the origin and/or destination of this pairing could not be geocoded. - &#x60;ZERO_RESULTS&#x60; indicates no route could be found between the origin and destination. - &#x60;MAX_ROUTE_LENGTH_EXCEEDED&#x60; indicates the requested route is too long and cannot be processed.  |  must be one of ["OK", "NOT_FOUND", "ZERO_RESULTS", "MAX_ROUTE_LENGTH_EXCEEDED", ]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


