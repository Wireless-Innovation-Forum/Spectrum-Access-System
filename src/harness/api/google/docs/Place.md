# Place

Attributes describing a place. Not all attributes will be available for all place types.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address_components** | [**[AddressComponent]**](AddressComponent.md) | An array containing the separate components applicable to this address. | [optional] 
**adr_address** | **str** | A representation of the place&#39;s address in the [adr microformat](http://microformats.org/wiki/adr). | [optional] 
**business_status** | **str** | Indicates the operational status of the place, if it is a business. If no data exists, &#x60;business_status&#x60; is not returned.  | [optional] 
**formatted_address** | **str** | A string containing the human-readable address of this place.  Often this address is equivalent to the postal address. Note that some countries, such as the United Kingdom, do not allow distribution of true postal addresses due to licensing restrictions.  The formatted address is logically composed of one or more address components. For example, the address \&quot;111 8th Avenue, New York, NY\&quot; consists of the following components: \&quot;111\&quot; (the street number), \&quot;8th Avenue\&quot; (the route), \&quot;New York\&quot; (the city) and \&quot;NY\&quot; (the US state).  Do not parse the formatted address programmatically. Instead you should use the individual address components, which the API response includes in addition to the formatted address field.        | [optional] 
**formatted_phone_number** | **str** | Contains the place&#39;s phone number in its [local format](http://en.wikipedia.org/wiki/Local_conventions_for_writing_telephone_numbers). | [optional] 
**geometry** | [**Geometry**](Geometry.md) |  | [optional] 
**icon** | **str** | Contains the URL of a suggested icon which may be displayed to the user when indicating this result on a map. | [optional] 
**icon_background_color** | **str** | Contains the default HEX color code for the place&#39;s category. | [optional] 
**icon_mask_base_uri** | **str** | Contains the URL of a recommended icon, minus the &#x60;.svg&#x60; or &#x60;.png&#x60; file type extension. | [optional] 
**international_phone_number** | **str** | Contains the place&#39;s phone number in international format. International format includes the country code, and is prefixed with the plus, +, sign. For example, the international_phone_number for Google&#39;s Sydney, Australia office is &#x60;+61 2 9374 4000&#x60;. | [optional] 
**name** | **str** | Contains the human-readable name for the returned result. For &#x60;establishment&#x60; results, this is usually the canonicalized business name. | [optional] 
**opening_hours** | [**PlaceOpeningHours**](PlaceOpeningHours.md) |  | [optional] 
**permanently_closed** | **bool** | Deprecated. The field &#x60;permanently_closed&#x60; is deprecated, and should not be used. Instead, use &#x60;business_status&#x60; to get the operational status of businesses. | [optional] 
**photos** | [**[PlacePhoto]**](PlacePhoto.md) | An array of photo objects, each containing a reference to an image. A request may return up to ten photos. More information about place photos and how you can use the images in your application can be found in the [Place Photos](https://developers.google.com/maps/documentation/places/web-service/photos) documentation. | [optional] 
**place_id** | **str** | A textual identifier that uniquely identifies a place. To retrieve information about the place, pass this identifier in the &#x60;place_id&#x60; field of a Places API request. For more information about place IDs, see the [place ID overview](https://developers.google.com/maps/documentation/places/web-service/place-id). | [optional] 
**plus_code** | [**PlusCode**](PlusCode.md) |  | [optional] 
**price_level** | **float** | The price level of the place, on a scale of 0 to 4. The exact amount indicated by a specific value will vary from region to region. Price levels are interpreted as follows: - 0 Free - 1 Inexpensive - 2 Moderate - 3 Expensive - 4 Very Expensive  | [optional] 
**rating** | **float** | Contains the place&#39;s rating, from 1.0 to 5.0, based on aggregated user reviews. | [optional] 
**reference** | **str** | Deprecated | [optional] 
**reviews** | [**[PlaceReview]**](PlaceReview.md) | A JSON array of up to five reviews. If a language parameter was specified in the request, the service will bias the results to prefer reviews written in that language. | [optional] 
**scope** | **str** | Deprecated. | [optional] 
**types** | **[str]** | Contains an array of feature types describing the given result. See the list of [supported types](https://developers.google.com/maps/documentation/places/web-service/supported_types#table2). | [optional] 
**url** | **str** | Contains the URL of the official Google page for this place. This will be the Google-owned page that contains the best available information about the place. Applications must link to or embed this page on any screen that shows detailed results about the place to the user. | [optional] 
**user_ratings_total** | **float** | The total number of reviews, with or without text, for this place. | [optional] 
**utc_offset** | **float** | Contains the number of minutes this place’s current timezone is offset from UTC. For example, for places in Sydney, Australia during daylight saving time this would be 660 (+11 hours from UTC), and for places in California outside of daylight saving time this would be -480 (-8 hours from UTC). | [optional] 
**vicinity** | **str** | For establishment (&#x60;types:[\&quot;establishment\&quot;, ...])&#x60; results only, the &#x60;vicinity&#x60; field contains a simplified address for the place, including the street name, street number, and locality, but not the province/state, postal code, or country.  For all other results, the &#x60;vicinity&#x60; field contains the name of the narrowest political (&#x60;types:[\&quot;political\&quot;, ...]&#x60;) feature that is present in the address of the result.  This content is meant to be read as-is. Do not programmatically parse the formatted address.  | [optional] 
**website** | **str** | The authoritative website for this place, such as a business&#39; homepage. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


