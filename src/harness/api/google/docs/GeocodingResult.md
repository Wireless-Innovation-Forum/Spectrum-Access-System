# GeocodingResult


## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address_components** | [**[AddressComponent]**](AddressComponent.md) | An array containing the separate components applicable to this address. | 
**formatted_address** | **str** | The human-readable address of this location. | 
**geometry** | [**GeocodingGeometry**](GeocodingGeometry.md) |  | 
**place_id** | **str** | A unique identifier that can be used with other Google APIs. For example, you can use the &#x60;place_id&#x60; in a Places API request to get details of a local business, such as phone number, opening hours, user reviews, and more. See the [place ID overview](https://developers.google.com/places/place-id). | 
**types** | **[str]** | The &#x60;types[]&#x60; array indicates the type of the returned result. This array contains a set of zero or more tags identifying the type of feature returned in the result. For example, a geocode of \&quot;Chicago\&quot; returns \&quot;locality\&quot; which indicates that \&quot;Chicago\&quot; is a city, and also returns \&quot;political\&quot; which indicates it is a political entity. | 
**plus_code** | [**PlusCode**](PlusCode.md) |  | [optional] 
**postcode_localities** | **[str]** | An array denoting all the localities contained in a postal code. This is only present when the result is a postal code that contains multiple localities. | [optional] 
**partial_match** | **bool** | Indicates that the geocoder did not return an exact match for the original request, though it was able to match part of the requested address. You may wish to examine the original request for misspellings and/or an incomplete address.  Partial matches most often occur for street addresses that do not exist within the locality you pass in the request. Partial matches may also be returned when a request matches two or more locations in the same locality.  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


