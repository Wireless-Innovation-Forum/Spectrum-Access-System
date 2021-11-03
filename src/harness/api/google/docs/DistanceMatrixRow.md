# DistanceMatrixRow


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**elements** | [**[DistanceMatrixElement]**](DistanceMatrixElement.md) | When the Distance Matrix API returns results, it places them within a JSON rows array. Even if no results are returned (such as when the origins and/or destinations don&#39;t exist), it still returns an empty array.   Rows are ordered according to the values in the origin parameter of the request. Each row corresponds to an origin, and each element within that row corresponds to a pairing of the origin with a destination value.  Each row array contains one or more element entries, which in turn contain the information about a single origin-destination pairing.  | 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


