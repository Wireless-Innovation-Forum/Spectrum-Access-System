# PlaceReview

A review of the place submitted by a user.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**author_name** | **str** | The name of the user who submitted the review. Anonymous reviews are attributed to \&quot;A Google user\&quot;. | 
**rating** | **float** | The user&#39;s overall rating for this place. This is a whole number, ranging from 1 to 5. | 
**relative_time_description** | **str** | The time that the review was submitted in text, relative to the current time. | 
**time** | **float** | The time that the review was submitted, measured in the number of seconds since since midnight, January 1, 1970 UTC. | 
**author_url** | **str** | The URL to the user&#39;s Google Maps Local Guides profile, if available. | [optional] 
**profile_photo_url** | **str** | The URL to the user&#39;s profile photo, if available. | [optional] 
**language** | **str** | An IETF language code indicating the language used in the user&#39;s review. This field contains the main language tag only, and not the secondary tag indicating country or region. For example, all the English reviews are tagged as &#39;en&#39;, and not &#39;en-AU&#39; or &#39;en-UK&#39; and so on. | [optional] 
**text** | **str** | The user&#39;s review. When reviewing a location with Google Places, text reviews are considered optional. Therefore, this field may be empty. Note that this field may include simple HTML markup. For example, the entity reference &#x60;&amp;amp;&#x60; may represent an ampersand character. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


