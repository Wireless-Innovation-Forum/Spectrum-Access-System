# src.harness.api.google.google_client.PlacesAPIApi

All URIs are relative to *https://www.googleapis.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**autocomplete**](PlacesAPIApi.md#autocomplete) | **GET** /maps/api/place/autocomplete/json | 
[**find_place_from_text**](PlacesAPIApi.md#find_place_from_text) | **GET** /maps/api/place/findplacefromtext/json | 
[**nearby_search**](PlacesAPIApi.md#nearby_search) | **GET** /maps/api/place/nearbysearch/json | 
[**place_details**](PlacesAPIApi.md#place_details) | **GET** /maps/api/place/details/json | 
[**place_photo**](PlacesAPIApi.md#place_photo) | **GET** /maps/api/place/photo | 
[**query_autocomplete**](PlacesAPIApi.md#query_autocomplete) | **GET** /maps/api/place/queryautocomplete/json | 
[**text_search**](PlacesAPIApi.md#text_search) | **GET** /maps/api/place/textsearch/json | 


# **autocomplete**
> PlacesAutocompleteResponse autocomplete(input)



The Place Autocomplete service is a web service that returns place predictions in response to an HTTP request. The request specifies a textual search string and optional geographic bounds. The service can be used to provide autocomplete functionality for text-based geographic searches, by returning places such as businesses, addresses and points of interest as a user types. <div class=\"note\">Note: You can use Place Autocomplete even without a map. If you do show a map, it must be a Google map. When you display predictions from the Place Autocomplete service without a map, you must include the ['Powered by Google'](https://developers.google.com/maps/documentation/places/web-service/policies#logo_requirementshttps://developers.google.com/maps/documentation/places/web-service/policies#logo_requirements) logo.</div>  The Place Autocomplete service can match on full words and substrings, resolving place names, addresses, and plus codes. Applications can therefore send queries as the user types, to provide on-the-fly place predictions.  The returned predictions are designed to be presented to the user to aid them in selecting the desired place. You can send a [Place Details](https://developers.google.com/maps/documentation/places/web-service/details#PlaceDetailsRequests) request for more information about any of the places which are returned. 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import places_api_api
from src.harness.api.google.google_client.model.places_autocomplete_response import PlacesAutocompleteResponse
from pprint import pprint
# Defining the host is optional and defaults to https://www.googleapis.com
# See configuration.py for a list of all supported configuration parameters.
configuration = src.harness.api.google.google_client.Configuration(
    host = "https://www.googleapis.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: ApiKeyAuth
configuration.api_key['ApiKeyAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['ApiKeyAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with src.harness.api.google.google_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = places_api_api.PlacesAPIApi(api_client)
    input = "input_example" # str | The text string on which to search. The Place Autocomplete service will return candidate matches based on this string and order results based on their perceived relevance. 
    sessiontoken = "sessiontoken_example" # str | A random string which identifies an autocomplete [session](https://developers.google.com/maps/documentation/places/web-service/details#session_tokens) for billing purposes.  The session begins when the user starts typing a query, and concludes when they select a place and a call to Place Details is made. Each session can have multiple queries, followed by one place selection. The API key(s) used for each request within a session must belong to the same Google Cloud Console project. Once a session has concluded, the token is no longer valid; your app must generate a fresh token for each session. If the `sessiontoken` parameter is omitted, or if you reuse a session token, the session is charged as if no session token was provided (each request is billed separately).  We recommend the following guidelines:  - Use session tokens for all autocomplete sessions. - Generate a fresh token for each session. Using a version 4 UUID is recommended. - Ensure that the API key(s) used for all Place Autocomplete and Place Details requests within a session belong to the same Cloud Console project. - Be sure to pass a unique session token for each new session. Using the same token for more than one session will result in each request being billed individually.  (optional)
    components = "country:us|country:pr" # str | A grouping of places to which you would like to restrict your results. Currently, you can use components to filter by up to 5 countries. Countries must be passed as a two character, ISO 3166-1 Alpha-2 compatible country code. For example: `components=country:fr` would restrict your results to places within France. Multiple countries must be passed as multiple `country:XX` filters, with the pipe character `|` as a separator. For example: `components=country:us|country:pr|country:vi|country:gu|country:mp` would restrict your results to places within the United States and its unincorporated organized territories. <div class=\"note\"><strong>Note:</strong> If you receive unexpected results with a country code, verify that you are using a code which includes the countries, dependent territories, and special areas of geographical interest you intend.  You can find code information at <a href=\"https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes\" target=\"blank\" class=\"external\">Wikipedia: List of ISO 3166 country codes</a> or the <a href=\"https://www.iso.org/obp/ui/#search\" target=\"blank\" class=\"external\">ISO Online Browsing Platform</a>.</div>  (optional)
    strictbounds = True # bool | Returns only those places that are strictly within the region defined by `location` and `radius`. This is a restriction, rather than a bias, meaning that results outside this region will not be returned even if they match the user input.  (optional)
    offset = 3 # float | The position, in the input term, of the last character that the service uses to match predictions. For example, if the input is `Google` and the offset is 3, the service will match on `Goo`. The string determined by the offset is matched against the first word in the input term only. For example, if the input term is `Google abc` and the offset is 3, the service will attempt to match against `Goo abc`. If no offset is supplied, the service will use the whole term. The offset should generally be set to the position of the text caret.  (optional)
    origin = "40,-110" # str | The origin point from which to calculate straight-line distance to the destination (returned as `distance_meters`). If this value is omitted, straight-line distance will not be returned. Must be specified as `latitude,longitude`.  (optional)
    location = "40,-110" # str | The point around which to retrieve place information. This must be specified as `latitude,longitude`.   <div class=\"note\">When using the Text Search API, the `location` parameter may be overriden if the `query` contains an explicit location such as `Market in Barcelona`.</div>  (optional)
    radius = 1000 # float | Defines the distance (in meters) within which to return place results. You may bias results to a specified circle by passing a `location` and a `radius` parameter. Doing so instructs the Places service to _prefer_ showing results within that circle; results outside of the defined area may still be displayed.  The radius will automatically be clamped to a maximum value depending on the type of search and other parameters.  * Autocomplete: 50,000 meters * Nearby Search:    * with `keyword` or `name`: 50,000 meters   * without `keyword` or `name`     * `rankby=prominence` (default): 50,000 meters     * `rankby=distance`: A few kilometers depending on density of area * Query Autocomplete: 50,000 meters * Text Search: 50,000 meters  (optional)
    types = "geocode" # str | You may restrict results from a Place Autocomplete request to be of a certain type by passing a types parameter. The parameter specifies a type or a type collection, as listed in the supported types below. If nothing is specified, all types are returned. In general only a single type is allowed. The exception is that you can safely mix the geocode and establishment types, but note that this will have the same effect as specifying no types. The supported types are: - `geocode` instructs the Place Autocomplete service to return only geocoding results, rather than business results. Generally, you use this request to disambiguate results where the location specified may be indeterminate. - `address` instructs the Place Autocomplete service to return only geocoding results with a precise address. Generally, you use this request when you know the user will be looking for a fully specified address. - `establishment` instructs the Place Autocomplete service to return only business results. - `(regions)` type collection instructs the Places service to return any result matching the following types:   - `locality`   - `sublocality`   - `postal_code`   - `country`   - `administrative_area_level_1`   - `administrative_area_level_2` - `(cities)` type collection instructs the Places service to return results that match `locality` or `administrative_area_level_3`.  (optional)
    language = "en" # str | The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If `language` is not supplied, the API attempts to use the preferred language as specified in the `Accept-Language` header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. (optional) if omitted the server will use the default value of "en"

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.autocomplete(input)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->autocomplete: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.autocomplete(input, sessiontoken=sessiontoken, components=components, strictbounds=strictbounds, offset=offset, origin=origin, location=location, radius=radius, types=types, language=language)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->autocomplete: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **input** | **str**| The text string on which to search. The Place Autocomplete service will return candidate matches based on this string and order results based on their perceived relevance.  |
 **sessiontoken** | **str**| A random string which identifies an autocomplete [session](https://developers.google.com/maps/documentation/places/web-service/details#session_tokens) for billing purposes.  The session begins when the user starts typing a query, and concludes when they select a place and a call to Place Details is made. Each session can have multiple queries, followed by one place selection. The API key(s) used for each request within a session must belong to the same Google Cloud Console project. Once a session has concluded, the token is no longer valid; your app must generate a fresh token for each session. If the &#x60;sessiontoken&#x60; parameter is omitted, or if you reuse a session token, the session is charged as if no session token was provided (each request is billed separately).  We recommend the following guidelines:  - Use session tokens for all autocomplete sessions. - Generate a fresh token for each session. Using a version 4 UUID is recommended. - Ensure that the API key(s) used for all Place Autocomplete and Place Details requests within a session belong to the same Cloud Console project. - Be sure to pass a unique session token for each new session. Using the same token for more than one session will result in each request being billed individually.  | [optional]
 **components** | **str**| A grouping of places to which you would like to restrict your results. Currently, you can use components to filter by up to 5 countries. Countries must be passed as a two character, ISO 3166-1 Alpha-2 compatible country code. For example: &#x60;components&#x3D;country:fr&#x60; would restrict your results to places within France. Multiple countries must be passed as multiple &#x60;country:XX&#x60; filters, with the pipe character &#x60;|&#x60; as a separator. For example: &#x60;components&#x3D;country:us|country:pr|country:vi|country:gu|country:mp&#x60; would restrict your results to places within the United States and its unincorporated organized territories. &lt;div class&#x3D;\&quot;note\&quot;&gt;&lt;strong&gt;Note:&lt;/strong&gt; If you receive unexpected results with a country code, verify that you are using a code which includes the countries, dependent territories, and special areas of geographical interest you intend.  You can find code information at &lt;a href&#x3D;\&quot;https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes\&quot; target&#x3D;\&quot;blank\&quot; class&#x3D;\&quot;external\&quot;&gt;Wikipedia: List of ISO 3166 country codes&lt;/a&gt; or the &lt;a href&#x3D;\&quot;https://www.iso.org/obp/ui/#search\&quot; target&#x3D;\&quot;blank\&quot; class&#x3D;\&quot;external\&quot;&gt;ISO Online Browsing Platform&lt;/a&gt;.&lt;/div&gt;  | [optional]
 **strictbounds** | **bool**| Returns only those places that are strictly within the region defined by &#x60;location&#x60; and &#x60;radius&#x60;. This is a restriction, rather than a bias, meaning that results outside this region will not be returned even if they match the user input.  | [optional]
 **offset** | **float**| The position, in the input term, of the last character that the service uses to match predictions. For example, if the input is &#x60;Google&#x60; and the offset is 3, the service will match on &#x60;Goo&#x60;. The string determined by the offset is matched against the first word in the input term only. For example, if the input term is &#x60;Google abc&#x60; and the offset is 3, the service will attempt to match against &#x60;Goo abc&#x60;. If no offset is supplied, the service will use the whole term. The offset should generally be set to the position of the text caret.  | [optional]
 **origin** | **str**| The origin point from which to calculate straight-line distance to the destination (returned as &#x60;distance_meters&#x60;). If this value is omitted, straight-line distance will not be returned. Must be specified as &#x60;latitude,longitude&#x60;.  | [optional]
 **location** | **str**| The point around which to retrieve place information. This must be specified as &#x60;latitude,longitude&#x60;.   &lt;div class&#x3D;\&quot;note\&quot;&gt;When using the Text Search API, the &#x60;location&#x60; parameter may be overriden if the &#x60;query&#x60; contains an explicit location such as &#x60;Market in Barcelona&#x60;.&lt;/div&gt;  | [optional]
 **radius** | **float**| Defines the distance (in meters) within which to return place results. You may bias results to a specified circle by passing a &#x60;location&#x60; and a &#x60;radius&#x60; parameter. Doing so instructs the Places service to _prefer_ showing results within that circle; results outside of the defined area may still be displayed.  The radius will automatically be clamped to a maximum value depending on the type of search and other parameters.  * Autocomplete: 50,000 meters * Nearby Search:    * with &#x60;keyword&#x60; or &#x60;name&#x60;: 50,000 meters   * without &#x60;keyword&#x60; or &#x60;name&#x60;     * &#x60;rankby&#x3D;prominence&#x60; (default): 50,000 meters     * &#x60;rankby&#x3D;distance&#x60;: A few kilometers depending on density of area * Query Autocomplete: 50,000 meters * Text Search: 50,000 meters  | [optional]
 **types** | **str**| You may restrict results from a Place Autocomplete request to be of a certain type by passing a types parameter. The parameter specifies a type or a type collection, as listed in the supported types below. If nothing is specified, all types are returned. In general only a single type is allowed. The exception is that you can safely mix the geocode and establishment types, but note that this will have the same effect as specifying no types. The supported types are: - &#x60;geocode&#x60; instructs the Place Autocomplete service to return only geocoding results, rather than business results. Generally, you use this request to disambiguate results where the location specified may be indeterminate. - &#x60;address&#x60; instructs the Place Autocomplete service to return only geocoding results with a precise address. Generally, you use this request when you know the user will be looking for a fully specified address. - &#x60;establishment&#x60; instructs the Place Autocomplete service to return only business results. - &#x60;(regions)&#x60; type collection instructs the Places service to return any result matching the following types:   - &#x60;locality&#x60;   - &#x60;sublocality&#x60;   - &#x60;postal_code&#x60;   - &#x60;country&#x60;   - &#x60;administrative_area_level_1&#x60;   - &#x60;administrative_area_level_2&#x60; - &#x60;(cities)&#x60; type collection instructs the Places service to return results that match &#x60;locality&#x60; or &#x60;administrative_area_level_3&#x60;.  | [optional]
 **language** | **str**| The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If &#x60;language&#x60; is not supplied, the API attempts to use the preferred language as specified in the &#x60;Accept-Language&#x60; header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. | [optional] if omitted the server will use the default value of "en"

### Return type

[**PlacesAutocompleteResponse**](PlacesAutocompleteResponse.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **find_place_from_text**
> PlacesFindPlaceFromTextResponse find_place_from_text(input, inputtype)



A Find Place request takes a text input and returns a place. The input can be any kind of Places text data, such as a name, address, or phone number. The request must be a string. A Find Place request using non-string data such as a lat/lng coordinate or plus code generates an error. <div class=\"note\">Note: If you omit the fields parameter from a Find Place request, only the place_id for the result will be returned.</div> 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import places_api_api
from src.harness.api.google.google_client.model.places_find_place_from_text_response import PlacesFindPlaceFromTextResponse
from pprint import pprint
# Defining the host is optional and defaults to https://www.googleapis.com
# See configuration.py for a list of all supported configuration parameters.
configuration = src.harness.api.google.google_client.Configuration(
    host = "https://www.googleapis.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: ApiKeyAuth
configuration.api_key['ApiKeyAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['ApiKeyAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with src.harness.api.google.google_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = places_api_api.PlacesAPIApi(api_client)
    input = "Museum of Contemporary Art Australia" # str | Text input that identifies the search target, such as a name, address, or phone number. The input must be a string. Non-string input such as a lat/lng coordinate or plus code generates an error. 
    inputtype = "textquery" # str | The type of input. This can be one of either `textquery` or `phonenumber`. Phone numbers must be in international format (prefixed by a plus sign (\"+\"), followed by the country code, then the phone number itself). See [E.164 ITU recommendation](https://en.wikipedia.org/wiki/E.164) for more information. 
    fields = ["formatted_address"] # [str] | Use the fields parameter to specify a comma-separated list of place data types to return. For example: `fields=formatted_address,name,geometry`. Use a forward slash when specifying compound values. For example: `opening_hours/open_now`.  Fields are divided into three billing categories: Basic, Contact, and Atmosphere. Basic fields are billed at base rate, and incur no additional charges. Contact and Atmosphere fields are billed at a higher rate. See the [pricing sheet](https://cloud.google.com/maps-platform/pricing/sheet/) for more information. Attributions, `html_attributions`, are always returned with every call, regardless of whether the field has been requested.  **Basic**  The Basic category includes the following fields: `address_component`, `adr_address`, `business_status`, `formatted_address`, `geometry`, `icon`, `icon_mask_base_uri`, `icon_background_color`, `name`, `permanently_closed` ([deprecated](https://developers.google.com/maps/deprecations)), `photo`, `place_id`, `plus_code`, `type`, `url`, `utc_offset`, `vicinity`.  **Contact**  The Contact category includes the following fields: `formatted_phone_number`, `international_phone_number`, `opening_hours`, `website`  **Atmosphere**  The Atmosphere category includes the following fields: `price_level`, `rating`, `review`, `user_ratings_total`.  <div class=\"caution\">Caution: Place Search requests and Place Details requests do not return the same fields. Place Search requests return a subset of the fields that are returned by Place Details requests. If the field you want is not returned by Place Search, you can use Place Search to get a place_id, then use that Place ID to make a Place Details request.</div>  (optional)
    locationbias = "ipbias" # str | Prefer results in a specified area, by specifying either a radius plus lat/lng, or two lat/lng pairs representing the points of a rectangle. If this parameter is not specified, the API uses IP address biasing by default. - IP bias: Instructs the API to use IP address biasing. Pass the string `ipbias` (this option has no additional parameters). - Point: A single lat/lng coordinate. Use the following format: `point:lat,lng`. - Circular: A string specifying radius in meters, plus lat/lng in decimal degrees. Use the following format: `circle:radius@lat,lng`. - Rectangular: A string specifying two lat/lng pairs in decimal degrees, representing the south/west and north/east points of a rectangle. Use the following format:`rectangle:south,west|north,east`. Note that east/west values are wrapped to the range -180, 180, and north/south values are clamped to the range -90, 90.  (optional)
    language = "en" # str | The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If `language` is not supplied, the API attempts to use the preferred language as specified in the `Accept-Language` header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. (optional) if omitted the server will use the default value of "en"

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.find_place_from_text(input, inputtype)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->find_place_from_text: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.find_place_from_text(input, inputtype, fields=fields, locationbias=locationbias, language=language)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->find_place_from_text: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **input** | **str**| Text input that identifies the search target, such as a name, address, or phone number. The input must be a string. Non-string input such as a lat/lng coordinate or plus code generates an error.  |
 **inputtype** | **str**| The type of input. This can be one of either &#x60;textquery&#x60; or &#x60;phonenumber&#x60;. Phone numbers must be in international format (prefixed by a plus sign (\&quot;+\&quot;), followed by the country code, then the phone number itself). See [E.164 ITU recommendation](https://en.wikipedia.org/wiki/E.164) for more information.  |
 **fields** | **[str]**| Use the fields parameter to specify a comma-separated list of place data types to return. For example: &#x60;fields&#x3D;formatted_address,name,geometry&#x60;. Use a forward slash when specifying compound values. For example: &#x60;opening_hours/open_now&#x60;.  Fields are divided into three billing categories: Basic, Contact, and Atmosphere. Basic fields are billed at base rate, and incur no additional charges. Contact and Atmosphere fields are billed at a higher rate. See the [pricing sheet](https://cloud.google.com/maps-platform/pricing/sheet/) for more information. Attributions, &#x60;html_attributions&#x60;, are always returned with every call, regardless of whether the field has been requested.  **Basic**  The Basic category includes the following fields: &#x60;address_component&#x60;, &#x60;adr_address&#x60;, &#x60;business_status&#x60;, &#x60;formatted_address&#x60;, &#x60;geometry&#x60;, &#x60;icon&#x60;, &#x60;icon_mask_base_uri&#x60;, &#x60;icon_background_color&#x60;, &#x60;name&#x60;, &#x60;permanently_closed&#x60; ([deprecated](https://developers.google.com/maps/deprecations)), &#x60;photo&#x60;, &#x60;place_id&#x60;, &#x60;plus_code&#x60;, &#x60;type&#x60;, &#x60;url&#x60;, &#x60;utc_offset&#x60;, &#x60;vicinity&#x60;.  **Contact**  The Contact category includes the following fields: &#x60;formatted_phone_number&#x60;, &#x60;international_phone_number&#x60;, &#x60;opening_hours&#x60;, &#x60;website&#x60;  **Atmosphere**  The Atmosphere category includes the following fields: &#x60;price_level&#x60;, &#x60;rating&#x60;, &#x60;review&#x60;, &#x60;user_ratings_total&#x60;.  &lt;div class&#x3D;\&quot;caution\&quot;&gt;Caution: Place Search requests and Place Details requests do not return the same fields. Place Search requests return a subset of the fields that are returned by Place Details requests. If the field you want is not returned by Place Search, you can use Place Search to get a place_id, then use that Place ID to make a Place Details request.&lt;/div&gt;  | [optional]
 **locationbias** | **str**| Prefer results in a specified area, by specifying either a radius plus lat/lng, or two lat/lng pairs representing the points of a rectangle. If this parameter is not specified, the API uses IP address biasing by default. - IP bias: Instructs the API to use IP address biasing. Pass the string &#x60;ipbias&#x60; (this option has no additional parameters). - Point: A single lat/lng coordinate. Use the following format: &#x60;point:lat,lng&#x60;. - Circular: A string specifying radius in meters, plus lat/lng in decimal degrees. Use the following format: &#x60;circle:radius@lat,lng&#x60;. - Rectangular: A string specifying two lat/lng pairs in decimal degrees, representing the south/west and north/east points of a rectangle. Use the following format:&#x60;rectangle:south,west|north,east&#x60;. Note that east/west values are wrapped to the range -180, 180, and north/south values are clamped to the range -90, 90.  | [optional]
 **language** | **str**| The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If &#x60;language&#x60; is not supplied, the API attempts to use the preferred language as specified in the &#x60;Accept-Language&#x60; header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. | [optional] if omitted the server will use the default value of "en"

### Return type

[**PlacesFindPlaceFromTextResponse**](PlacesFindPlaceFromTextResponse.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **nearby_search**
> PlacesNearbySearchResponse nearby_search(location)



A Nearby Search lets you search for places within a specified area. You can refine your search request by supplying keywords or specifying the type of place you are searching for.

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import places_api_api
from src.harness.api.google.google_client.model.places_nearby_search_response import PlacesNearbySearchResponse
from pprint import pprint
# Defining the host is optional and defaults to https://www.googleapis.com
# See configuration.py for a list of all supported configuration parameters.
configuration = src.harness.api.google.google_client.Configuration(
    host = "https://www.googleapis.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: ApiKeyAuth
configuration.api_key['ApiKeyAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['ApiKeyAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with src.harness.api.google.google_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = places_api_api.PlacesAPIApi(api_client)
    location = "40,-110" # str | The point around which to retrieve place information. This must be specified as `latitude,longitude`. 
    keyword = "keyword_example" # str | A term to be matched against all content that Google has indexed for this place, including but not limited to name and type, as well as customer reviews and other third-party content. Note that explicitly including location information using this parameter may conflict with the location, radius, and rankby parameters, causing unexpected results.  (optional)
    maxprice = "0" # str | Restricts results to only those places within the specified range. Valid values range between 0 (most affordable) to 4 (most expensive), inclusive. The exact amount indicated by a specific value will vary from region to region.  (optional)
    minprice = "0" # str | Restricts results to only those places within the specified range. Valid values range between 0 (most affordable) to 4 (most expensive), inclusive. The exact amount indicated by a specific value will vary from region to region.  (optional)
    name = "name_example" # str | *Not Recommended* A term to be matched against all content that Google has indexed for this place. Equivalent to `keyword`. The `name` field is no longer restricted to place names. Values in this field are combined with values in the keyword field and passed as part of the same search string. We recommend using only the `keyword` parameter for all search terms.  (optional)
    opennow = True # bool | Returns only those places that are open for business at the time the query is sent. Places that do not specify opening hours in the Google Places database will not be returned if you include this parameter in your query.  (optional)
    pagetoken = "pagetoken_example" # str | Returns up to 20 results from a previously run search. Setting a `pagetoken` parameter will execute a search with the same parameters used previously — all parameters other than pagetoken will be ignored.  (optional)
    rankby = "prominence" # str | Specifies the order in which results are listed. Possible values are: - `prominence` (default). This option sorts results based on their importance. Ranking will favor prominent places within the set radius over nearby places that match but that are less prominent. Prominence can be affected by a place's ranking in Google's index, global popularity, and other factors. When prominence is specified, the `radius` parameter is required. - `distance`. This option biases search results in ascending order by their distance from the specified location. When `distance` is specified, one or more of `keyword`, `name`, or `type` is required.  (optional)
    radius = 1000 # float | Defines the distance (in meters) within which to return place results. You may bias results to a specified circle by passing a `location` and a `radius` parameter. Doing so instructs the Places service to _prefer_ showing results within that circle; results outside of the defined area may still be displayed.  The radius will automatically be clamped to a maximum value depending on the type of search and other parameters.  * Autocomplete: 50,000 meters * Nearby Search:    * with `keyword` or `name`: 50,000 meters   * without `keyword` or `name`     * `rankby=prominence` (default): 50,000 meters     * `rankby=distance`: A few kilometers depending on density of area * Query Autocomplete: 50,000 meters * Text Search: 50,000 meters  (optional)
    type = "type_example" # str | Restricts the results to places matching the specified type. Only one type may be specified. If more than one type is provided, all types following the first entry are ignored.  * `type=hospital|pharmacy|doctor` becomes `type=hospital` * `type=hospital,pharmacy,doctor` is ignored entirely  See the list of [supported types](https://developers.google.com/maps/documentation/places/web-service/supported_types). <div class=\"note\">Note: Adding both `keyword` and `type` with the same value (`keyword=cafe&type=cafe` or `keyword=parking&type=parking`) can yield `ZERO_RESULTS`.</div>  (optional)
    language = "en" # str | The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If `language` is not supplied, the API attempts to use the preferred language as specified in the `Accept-Language` header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. (optional) if omitted the server will use the default value of "en"

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.nearby_search(location)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->nearby_search: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.nearby_search(location, keyword=keyword, maxprice=maxprice, minprice=minprice, name=name, opennow=opennow, pagetoken=pagetoken, rankby=rankby, radius=radius, type=type, language=language)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->nearby_search: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **location** | **str**| The point around which to retrieve place information. This must be specified as &#x60;latitude,longitude&#x60;.  |
 **keyword** | **str**| A term to be matched against all content that Google has indexed for this place, including but not limited to name and type, as well as customer reviews and other third-party content. Note that explicitly including location information using this parameter may conflict with the location, radius, and rankby parameters, causing unexpected results.  | [optional]
 **maxprice** | **str**| Restricts results to only those places within the specified range. Valid values range between 0 (most affordable) to 4 (most expensive), inclusive. The exact amount indicated by a specific value will vary from region to region.  | [optional]
 **minprice** | **str**| Restricts results to only those places within the specified range. Valid values range between 0 (most affordable) to 4 (most expensive), inclusive. The exact amount indicated by a specific value will vary from region to region.  | [optional]
 **name** | **str**| *Not Recommended* A term to be matched against all content that Google has indexed for this place. Equivalent to &#x60;keyword&#x60;. The &#x60;name&#x60; field is no longer restricted to place names. Values in this field are combined with values in the keyword field and passed as part of the same search string. We recommend using only the &#x60;keyword&#x60; parameter for all search terms.  | [optional]
 **opennow** | **bool**| Returns only those places that are open for business at the time the query is sent. Places that do not specify opening hours in the Google Places database will not be returned if you include this parameter in your query.  | [optional]
 **pagetoken** | **str**| Returns up to 20 results from a previously run search. Setting a &#x60;pagetoken&#x60; parameter will execute a search with the same parameters used previously — all parameters other than pagetoken will be ignored.  | [optional]
 **rankby** | **str**| Specifies the order in which results are listed. Possible values are: - &#x60;prominence&#x60; (default). This option sorts results based on their importance. Ranking will favor prominent places within the set radius over nearby places that match but that are less prominent. Prominence can be affected by a place&#39;s ranking in Google&#39;s index, global popularity, and other factors. When prominence is specified, the &#x60;radius&#x60; parameter is required. - &#x60;distance&#x60;. This option biases search results in ascending order by their distance from the specified location. When &#x60;distance&#x60; is specified, one or more of &#x60;keyword&#x60;, &#x60;name&#x60;, or &#x60;type&#x60; is required.  | [optional]
 **radius** | **float**| Defines the distance (in meters) within which to return place results. You may bias results to a specified circle by passing a &#x60;location&#x60; and a &#x60;radius&#x60; parameter. Doing so instructs the Places service to _prefer_ showing results within that circle; results outside of the defined area may still be displayed.  The radius will automatically be clamped to a maximum value depending on the type of search and other parameters.  * Autocomplete: 50,000 meters * Nearby Search:    * with &#x60;keyword&#x60; or &#x60;name&#x60;: 50,000 meters   * without &#x60;keyword&#x60; or &#x60;name&#x60;     * &#x60;rankby&#x3D;prominence&#x60; (default): 50,000 meters     * &#x60;rankby&#x3D;distance&#x60;: A few kilometers depending on density of area * Query Autocomplete: 50,000 meters * Text Search: 50,000 meters  | [optional]
 **type** | **str**| Restricts the results to places matching the specified type. Only one type may be specified. If more than one type is provided, all types following the first entry are ignored.  * &#x60;type&#x3D;hospital|pharmacy|doctor&#x60; becomes &#x60;type&#x3D;hospital&#x60; * &#x60;type&#x3D;hospital,pharmacy,doctor&#x60; is ignored entirely  See the list of [supported types](https://developers.google.com/maps/documentation/places/web-service/supported_types). &lt;div class&#x3D;\&quot;note\&quot;&gt;Note: Adding both &#x60;keyword&#x60; and &#x60;type&#x60; with the same value (&#x60;keyword&#x3D;cafe&amp;type&#x3D;cafe&#x60; or &#x60;keyword&#x3D;parking&amp;type&#x3D;parking&#x60;) can yield &#x60;ZERO_RESULTS&#x60;.&lt;/div&gt;  | [optional]
 **language** | **str**| The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If &#x60;language&#x60; is not supplied, the API attempts to use the preferred language as specified in the &#x60;Accept-Language&#x60; header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. | [optional] if omitted the server will use the default value of "en"

### Return type

[**PlacesNearbySearchResponse**](PlacesNearbySearchResponse.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **place_details**
> PlacesDetailsResponse place_details(place_id)



The Places API is a service that returns information about places using HTTP requests. Places are defined within this API as establishments, geographic locations, or prominent points of interest.

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import places_api_api
from src.harness.api.google.google_client.model.places_details_response import PlacesDetailsResponse
from pprint import pprint
# Defining the host is optional and defaults to https://www.googleapis.com
# See configuration.py for a list of all supported configuration parameters.
configuration = src.harness.api.google.google_client.Configuration(
    host = "https://www.googleapis.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: ApiKeyAuth
configuration.api_key['ApiKeyAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['ApiKeyAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with src.harness.api.google.google_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = places_api_api.PlacesAPIApi(api_client)
    place_id = "ChIJN1t_tDeuEmsRUsoyG83frY4" # str | A textual identifier that uniquely identifies a place, returned from a [Place Search](https://developers.google.com/maps/documentation/places/web-service/search). For more information about place IDs, see the [place ID overview](https://developers.google.com/maps/documentation/places/web-service/place-id). 
    fields = ["formatted_address"] # [str] | Use the fields parameter to specify a comma-separated list of place data types to return. For example: `fields=formatted_address,name,geometry`. Use a forward slash when specifying compound values. For example: `opening_hours/open_now`.  Fields are divided into three billing categories: Basic, Contact, and Atmosphere. Basic fields are billed at base rate, and incur no additional charges. Contact and Atmosphere fields are billed at a higher rate. See the [pricing sheet](https://cloud.google.com/maps-platform/pricing/sheet/) for more information. Attributions, `html_attributions`, are always returned with every call, regardless of whether the field has been requested.  **Basic**  The Basic category includes the following fields: `address_component`, `adr_address`, `business_status`, `formatted_address`, `geometry`, `icon`, `icon_mask_base_uri`, `icon_background_color`, `name`, `permanently_closed` ([deprecated](https://developers.google.com/maps/deprecations)), `photo`, `place_id`, `plus_code`, `type`, `url`, `utc_offset`, `vicinity`.  **Contact**  The Contact category includes the following fields: `formatted_phone_number`, `international_phone_number`, `opening_hours`, `website`  **Atmosphere**  The Atmosphere category includes the following fields: `price_level`, `rating`, `review`, `user_ratings_total`.  <div class=\"caution\">Caution: Place Search requests and Place Details requests do not return the same fields. Place Search requests return a subset of the fields that are returned by Place Details requests. If the field you want is not returned by Place Search, you can use Place Search to get a place_id, then use that Place ID to make a Place Details request.</div>  (optional)
    sessiontoken = "sessiontoken_example" # str | A random string which identifies an autocomplete [session](https://developers.google.com/maps/documentation/places/web-service/details#session_tokens) for billing purposes.  The session begins when the user starts typing a query, and concludes when they select a place and a call to Place Details is made. Each session can have multiple queries, followed by one place selection. The API key(s) used for each request within a session must belong to the same Google Cloud Console project. Once a session has concluded, the token is no longer valid; your app must generate a fresh token for each session. If the `sessiontoken` parameter is omitted, or if you reuse a session token, the session is charged as if no session token was provided (each request is billed separately).  We recommend the following guidelines:  - Use session tokens for all autocomplete sessions. - Generate a fresh token for each session. Using a version 4 UUID is recommended. - Ensure that the API key(s) used for all Place Autocomplete and Place Details requests within a session belong to the same Cloud Console project. - Be sure to pass a unique session token for each new session. Using the same token for more than one session will result in each request being billed individually.  (optional)
    language = "en" # str | The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If `language` is not supplied, the API attempts to use the preferred language as specified in the `Accept-Language` header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. (optional) if omitted the server will use the default value of "en"
    region = "en" # str | The region code, specified as a [ccTLD (\"top-level domain\")](https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains#Country_code_top-level_domains) two-character value. Most ccTLD codes are identical to ISO 3166-1 codes, with some notable exceptions. For example, the United Kingdom's ccTLD is \"uk\" (.co.uk) while its ISO 3166-1 code is \"gb\" (technically for the entity of \"The United Kingdom of Great Britain and Northern Ireland\"). (optional) if omitted the server will use the default value of "en"

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.place_details(place_id)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->place_details: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.place_details(place_id, fields=fields, sessiontoken=sessiontoken, language=language, region=region)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->place_details: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **place_id** | **str**| A textual identifier that uniquely identifies a place, returned from a [Place Search](https://developers.google.com/maps/documentation/places/web-service/search). For more information about place IDs, see the [place ID overview](https://developers.google.com/maps/documentation/places/web-service/place-id).  |
 **fields** | **[str]**| Use the fields parameter to specify a comma-separated list of place data types to return. For example: &#x60;fields&#x3D;formatted_address,name,geometry&#x60;. Use a forward slash when specifying compound values. For example: &#x60;opening_hours/open_now&#x60;.  Fields are divided into three billing categories: Basic, Contact, and Atmosphere. Basic fields are billed at base rate, and incur no additional charges. Contact and Atmosphere fields are billed at a higher rate. See the [pricing sheet](https://cloud.google.com/maps-platform/pricing/sheet/) for more information. Attributions, &#x60;html_attributions&#x60;, are always returned with every call, regardless of whether the field has been requested.  **Basic**  The Basic category includes the following fields: &#x60;address_component&#x60;, &#x60;adr_address&#x60;, &#x60;business_status&#x60;, &#x60;formatted_address&#x60;, &#x60;geometry&#x60;, &#x60;icon&#x60;, &#x60;icon_mask_base_uri&#x60;, &#x60;icon_background_color&#x60;, &#x60;name&#x60;, &#x60;permanently_closed&#x60; ([deprecated](https://developers.google.com/maps/deprecations)), &#x60;photo&#x60;, &#x60;place_id&#x60;, &#x60;plus_code&#x60;, &#x60;type&#x60;, &#x60;url&#x60;, &#x60;utc_offset&#x60;, &#x60;vicinity&#x60;.  **Contact**  The Contact category includes the following fields: &#x60;formatted_phone_number&#x60;, &#x60;international_phone_number&#x60;, &#x60;opening_hours&#x60;, &#x60;website&#x60;  **Atmosphere**  The Atmosphere category includes the following fields: &#x60;price_level&#x60;, &#x60;rating&#x60;, &#x60;review&#x60;, &#x60;user_ratings_total&#x60;.  &lt;div class&#x3D;\&quot;caution\&quot;&gt;Caution: Place Search requests and Place Details requests do not return the same fields. Place Search requests return a subset of the fields that are returned by Place Details requests. If the field you want is not returned by Place Search, you can use Place Search to get a place_id, then use that Place ID to make a Place Details request.&lt;/div&gt;  | [optional]
 **sessiontoken** | **str**| A random string which identifies an autocomplete [session](https://developers.google.com/maps/documentation/places/web-service/details#session_tokens) for billing purposes.  The session begins when the user starts typing a query, and concludes when they select a place and a call to Place Details is made. Each session can have multiple queries, followed by one place selection. The API key(s) used for each request within a session must belong to the same Google Cloud Console project. Once a session has concluded, the token is no longer valid; your app must generate a fresh token for each session. If the &#x60;sessiontoken&#x60; parameter is omitted, or if you reuse a session token, the session is charged as if no session token was provided (each request is billed separately).  We recommend the following guidelines:  - Use session tokens for all autocomplete sessions. - Generate a fresh token for each session. Using a version 4 UUID is recommended. - Ensure that the API key(s) used for all Place Autocomplete and Place Details requests within a session belong to the same Cloud Console project. - Be sure to pass a unique session token for each new session. Using the same token for more than one session will result in each request being billed individually.  | [optional]
 **language** | **str**| The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If &#x60;language&#x60; is not supplied, the API attempts to use the preferred language as specified in the &#x60;Accept-Language&#x60; header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. | [optional] if omitted the server will use the default value of "en"
 **region** | **str**| The region code, specified as a [ccTLD (\&quot;top-level domain\&quot;)](https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains#Country_code_top-level_domains) two-character value. Most ccTLD codes are identical to ISO 3166-1 codes, with some notable exceptions. For example, the United Kingdom&#39;s ccTLD is \&quot;uk\&quot; (.co.uk) while its ISO 3166-1 code is \&quot;gb\&quot; (technically for the entity of \&quot;The United Kingdom of Great Britain and Northern Ireland\&quot;). | [optional] if omitted the server will use the default value of "en"

### Return type

[**PlacesDetailsResponse**](PlacesDetailsResponse.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **place_photo**
> file_type place_photo(photo_reference)



The Place Photo service, part of the Places API, is a read- only API that allows you to add high quality photographic content to your application. The Place Photo service gives you access to the millions of photos stored in the Places database. When you get place information using a Place Details request, photo references will be returned for relevant photographic content. Find Place, Nearby Search, and Text Search requests also return a single photo reference per place, when relevant. Using the Photo service you can then access the referenced photos and resize the image to the optimal size for your application.  Photos returned by the Photo service are sourced from a variety of locations, including business owners and user contributed photos. In most cases, these photos can be used without attribution, or will have the required attribution included as a part of the image. However, if the returned photo element includes a value in the html_attributions field, you will have to include the additional attribution in your application wherever you display the image. 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import places_api_api
from pprint import pprint
# Defining the host is optional and defaults to https://www.googleapis.com
# See configuration.py for a list of all supported configuration parameters.
configuration = src.harness.api.google.google_client.Configuration(
    host = "https://www.googleapis.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: ApiKeyAuth
configuration.api_key['ApiKeyAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['ApiKeyAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with src.harness.api.google.google_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = places_api_api.PlacesAPIApi(api_client)
    photo_reference = "photo_reference_example" # str | A string identifier that uniquely identifies a photo. Photo references are returned from either a Place Search or Place Details request. 
    maxheight = 3.14 # float | Specifies the maximum desired height, in pixels, of the image. If the image is smaller than the values specified, the original image will be returned. If the image is larger in either dimension, it will be scaled to match the smaller of the two dimensions, restricted to its original aspect ratio. Both the `maxheight` and `maxwidth` properties accept an integer between `1` and `1600`.  (optional)
    maxwidth = 3.14 # float | Specifies the maximum desired width, in pixels, of the image. If the image is smaller than the values specified, the original image will be returned. If the image is larger in either dimension, it will be scaled to match the smaller of the two dimensions, restricted to its original aspect ratio. Both the `maxheight` and `maxwidth` properties accept an integer between `1` and `1600`.  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.place_photo(photo_reference)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->place_photo: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.place_photo(photo_reference, maxheight=maxheight, maxwidth=maxwidth)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->place_photo: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **photo_reference** | **str**| A string identifier that uniquely identifies a photo. Photo references are returned from either a Place Search or Place Details request.  |
 **maxheight** | **float**| Specifies the maximum desired height, in pixels, of the image. If the image is smaller than the values specified, the original image will be returned. If the image is larger in either dimension, it will be scaled to match the smaller of the two dimensions, restricted to its original aspect ratio. Both the &#x60;maxheight&#x60; and &#x60;maxwidth&#x60; properties accept an integer between &#x60;1&#x60; and &#x60;1600&#x60;.  | [optional]
 **maxwidth** | **float**| Specifies the maximum desired width, in pixels, of the image. If the image is smaller than the values specified, the original image will be returned. If the image is larger in either dimension, it will be scaled to match the smaller of the two dimensions, restricted to its original aspect ratio. Both the &#x60;maxheight&#x60; and &#x60;maxwidth&#x60; properties accept an integer between &#x60;1&#x60; and &#x60;1600&#x60;.  | [optional]

### Return type

**file_type**

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: image/*


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **query_autocomplete**
> PlacesQueryAutocompleteResponse query_autocomplete(input)



The Query Autocomplete service can be used to provide a query prediction for text-based geographic searches, by returning suggested queries as you type.  The Query Autocomplete service allows you to add on-the-fly geographic query predictions to your application. Instead of searching for a specific location, a user can type in a categorical search, such as \"pizza near New York\" and the service responds with a list of suggested queries matching the string. As the Query Autocomplete service can match on both full words and substrings, applications can send queries as the user types to provide on-the-fly predictions. 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import places_api_api
from src.harness.api.google.google_client.model.places_query_autocomplete_response import PlacesQueryAutocompleteResponse
from pprint import pprint
# Defining the host is optional and defaults to https://www.googleapis.com
# See configuration.py for a list of all supported configuration parameters.
configuration = src.harness.api.google.google_client.Configuration(
    host = "https://www.googleapis.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: ApiKeyAuth
configuration.api_key['ApiKeyAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['ApiKeyAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with src.harness.api.google.google_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = places_api_api.PlacesAPIApi(api_client)
    input = "input_example" # str | The text string on which to search. The Place Autocomplete service will return candidate matches based on this string and order results based on their perceived relevance. 
    offset = 3 # float | The position, in the input term, of the last character that the service uses to match predictions. For example, if the input is `Google` and the offset is 3, the service will match on `Goo`. The string determined by the offset is matched against the first word in the input term only. For example, if the input term is `Google abc` and the offset is 3, the service will attempt to match against `Goo abc`. If no offset is supplied, the service will use the whole term. The offset should generally be set to the position of the text caret.  (optional)
    location = "40,-110" # str | The point around which to retrieve place information. This must be specified as `latitude,longitude`.   <div class=\"note\">The <code>location</code> parameter may be overriden if the <code>query</code> contains an explicit location such as <code>Market in Barcelona</code>. Using quotes around the query may also influence the weight given to the <code>location</code> and <code>radius</code>.</div>  (optional)
    radius = 1000 # float | Defines the distance (in meters) within which to return place results. You may bias results to a specified circle by passing a `location` and a `radius` parameter. Doing so instructs the Places service to _prefer_ showing results within that circle; results outside of the defined area may still be displayed.  The radius will automatically be clamped to a maximum value depending on the type of search and other parameters.  * Autocomplete: 50,000 meters * Nearby Search:    * with `keyword` or `name`: 50,000 meters   * without `keyword` or `name`     * `rankby=prominence` (default): 50,000 meters     * `rankby=distance`: A few kilometers depending on density of area * Query Autocomplete: 50,000 meters * Text Search: 50,000 meters  (optional)
    language = "en" # str | The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If `language` is not supplied, the API attempts to use the preferred language as specified in the `Accept-Language` header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. (optional) if omitted the server will use the default value of "en"

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.query_autocomplete(input)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->query_autocomplete: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.query_autocomplete(input, offset=offset, location=location, radius=radius, language=language)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->query_autocomplete: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **input** | **str**| The text string on which to search. The Place Autocomplete service will return candidate matches based on this string and order results based on their perceived relevance.  |
 **offset** | **float**| The position, in the input term, of the last character that the service uses to match predictions. For example, if the input is &#x60;Google&#x60; and the offset is 3, the service will match on &#x60;Goo&#x60;. The string determined by the offset is matched against the first word in the input term only. For example, if the input term is &#x60;Google abc&#x60; and the offset is 3, the service will attempt to match against &#x60;Goo abc&#x60;. If no offset is supplied, the service will use the whole term. The offset should generally be set to the position of the text caret.  | [optional]
 **location** | **str**| The point around which to retrieve place information. This must be specified as &#x60;latitude,longitude&#x60;.   &lt;div class&#x3D;\&quot;note\&quot;&gt;The &lt;code&gt;location&lt;/code&gt; parameter may be overriden if the &lt;code&gt;query&lt;/code&gt; contains an explicit location such as &lt;code&gt;Market in Barcelona&lt;/code&gt;. Using quotes around the query may also influence the weight given to the &lt;code&gt;location&lt;/code&gt; and &lt;code&gt;radius&lt;/code&gt;.&lt;/div&gt;  | [optional]
 **radius** | **float**| Defines the distance (in meters) within which to return place results. You may bias results to a specified circle by passing a &#x60;location&#x60; and a &#x60;radius&#x60; parameter. Doing so instructs the Places service to _prefer_ showing results within that circle; results outside of the defined area may still be displayed.  The radius will automatically be clamped to a maximum value depending on the type of search and other parameters.  * Autocomplete: 50,000 meters * Nearby Search:    * with &#x60;keyword&#x60; or &#x60;name&#x60;: 50,000 meters   * without &#x60;keyword&#x60; or &#x60;name&#x60;     * &#x60;rankby&#x3D;prominence&#x60; (default): 50,000 meters     * &#x60;rankby&#x3D;distance&#x60;: A few kilometers depending on density of area * Query Autocomplete: 50,000 meters * Text Search: 50,000 meters  | [optional]
 **language** | **str**| The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If &#x60;language&#x60; is not supplied, the API attempts to use the preferred language as specified in the &#x60;Accept-Language&#x60; header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. | [optional] if omitted the server will use the default value of "en"

### Return type

[**PlacesQueryAutocompleteResponse**](PlacesQueryAutocompleteResponse.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **text_search**
> PlacesTextSearchResponse text_search(query)



The Google Places API Text Search Service is a web service that returns information about a set of places based on a string — for example \"pizza in New York\" or \"shoe stores near Ottawa\" or \"123 Main Street\". The service responds with a list of places matching the text string and any location bias that has been set.  The service is especially useful for making [ambiguous address](https://developers.google.com/maps/documentation/geocoding/best-practices) queries in an automated system, and non-address components of the string may match businesses as well as addresses. Examples of ambiguous address queries are incomplete addresses, poorly formatted addresses, or a request that includes non-address components such as business names.  The search response will include a list of places. You can send a Place Details request for more information about any of the places in the response. 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import places_api_api
from src.harness.api.google.google_client.model.places_text_search_response import PlacesTextSearchResponse
from pprint import pprint
# Defining the host is optional and defaults to https://www.googleapis.com
# See configuration.py for a list of all supported configuration parameters.
configuration = src.harness.api.google.google_client.Configuration(
    host = "https://www.googleapis.com"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure API key authorization: ApiKeyAuth
configuration.api_key['ApiKeyAuth'] = 'YOUR_API_KEY'

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['ApiKeyAuth'] = 'Bearer'

# Enter a context with an instance of the API client
with src.harness.api.google.google_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = places_api_api.PlacesAPIApi(api_client)
    query = "restaurants in Sydney" # str | The text string on which to search, for example: \"restaurant\" or \"123 Main Street\". The Google Places service will return candidate matches based on this string and order the results based on their perceived relevance. 
    location = "40,-110" # str | The point around which to retrieve place information. This must be specified as `latitude,longitude`.   <div class=\"note\">The <code>location</code> parameter may be overriden if the <code>query</code> contains an explicit location such as <code>Market in Barcelona</code>. Using quotes around the query may also influence the weight given to the <code>location</code> and <code>radius</code>.</div>  (optional)
    maxprice = "0" # str | Restricts results to only those places within the specified range. Valid values range between 0 (most affordable) to 4 (most expensive), inclusive. The exact amount indicated by a specific value will vary from region to region.  (optional)
    minprice = "0" # str | Restricts results to only those places within the specified range. Valid values range between 0 (most affordable) to 4 (most expensive), inclusive. The exact amount indicated by a specific value will vary from region to region.  (optional)
    opennow = True # bool | Returns only those places that are open for business at the time the query is sent. Places that do not specify opening hours in the Google Places database will not be returned if you include this parameter in your query.  (optional)
    pagetoken = "pagetoken_example" # str | Returns up to 20 results from a previously run search. Setting a `pagetoken` parameter will execute a search with the same parameters used previously — all parameters other than pagetoken will be ignored.  (optional)
    radius = 1000 # float | Defines the distance (in meters) within which to return place results. You may bias results to a specified circle by passing a `location` and a `radius` parameter. Doing so instructs the Places service to _prefer_ showing results within that circle; results outside of the defined area may still be displayed.  The radius will automatically be clamped to a maximum value depending on the type of search and other parameters.  * Autocomplete: 50,000 meters * Nearby Search:    * with `keyword` or `name`: 50,000 meters   * without `keyword` or `name`     * `rankby=prominence` (default): 50,000 meters     * `rankby=distance`: A few kilometers depending on density of area * Query Autocomplete: 50,000 meters * Text Search: 50,000 meters  (optional)
    type = "type_example" # str | Restricts the results to places matching the specified type. Only one type may be specified. If more than one type is provided, all types following the first entry are ignored.  * `type=hospital|pharmacy|doctor` becomes `type=hospital` * `type=hospital,pharmacy,doctor` is ignored entirely  See the list of [supported types](https://developers.google.com/maps/documentation/places/web-service/supported_types). <div class=\"note\">Note: Adding both `keyword` and `type` with the same value (`keyword=cafe&type=cafe` or `keyword=parking&type=parking`) can yield `ZERO_RESULTS`.</div>  (optional)
    language = "en" # str | The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If `language` is not supplied, the API attempts to use the preferred language as specified in the `Accept-Language` header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. (optional) if omitted the server will use the default value of "en"
    region = "en" # str | The region code, specified as a [ccTLD (\"top-level domain\")](https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains#Country_code_top-level_domains) two-character value. Most ccTLD codes are identical to ISO 3166-1 codes, with some notable exceptions. For example, the United Kingdom's ccTLD is \"uk\" (.co.uk) while its ISO 3166-1 code is \"gb\" (technically for the entity of \"The United Kingdom of Great Britain and Northern Ireland\"). (optional) if omitted the server will use the default value of "en"

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.text_search(query)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->text_search: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.text_search(query, location=location, maxprice=maxprice, minprice=minprice, opennow=opennow, pagetoken=pagetoken, radius=radius, type=type, language=language, region=region)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling PlacesAPIApi->text_search: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **query** | **str**| The text string on which to search, for example: \&quot;restaurant\&quot; or \&quot;123 Main Street\&quot;. The Google Places service will return candidate matches based on this string and order the results based on their perceived relevance.  |
 **location** | **str**| The point around which to retrieve place information. This must be specified as &#x60;latitude,longitude&#x60;.   &lt;div class&#x3D;\&quot;note\&quot;&gt;The &lt;code&gt;location&lt;/code&gt; parameter may be overriden if the &lt;code&gt;query&lt;/code&gt; contains an explicit location such as &lt;code&gt;Market in Barcelona&lt;/code&gt;. Using quotes around the query may also influence the weight given to the &lt;code&gt;location&lt;/code&gt; and &lt;code&gt;radius&lt;/code&gt;.&lt;/div&gt;  | [optional]
 **maxprice** | **str**| Restricts results to only those places within the specified range. Valid values range between 0 (most affordable) to 4 (most expensive), inclusive. The exact amount indicated by a specific value will vary from region to region.  | [optional]
 **minprice** | **str**| Restricts results to only those places within the specified range. Valid values range between 0 (most affordable) to 4 (most expensive), inclusive. The exact amount indicated by a specific value will vary from region to region.  | [optional]
 **opennow** | **bool**| Returns only those places that are open for business at the time the query is sent. Places that do not specify opening hours in the Google Places database will not be returned if you include this parameter in your query.  | [optional]
 **pagetoken** | **str**| Returns up to 20 results from a previously run search. Setting a &#x60;pagetoken&#x60; parameter will execute a search with the same parameters used previously — all parameters other than pagetoken will be ignored.  | [optional]
 **radius** | **float**| Defines the distance (in meters) within which to return place results. You may bias results to a specified circle by passing a &#x60;location&#x60; and a &#x60;radius&#x60; parameter. Doing so instructs the Places service to _prefer_ showing results within that circle; results outside of the defined area may still be displayed.  The radius will automatically be clamped to a maximum value depending on the type of search and other parameters.  * Autocomplete: 50,000 meters * Nearby Search:    * with &#x60;keyword&#x60; or &#x60;name&#x60;: 50,000 meters   * without &#x60;keyword&#x60; or &#x60;name&#x60;     * &#x60;rankby&#x3D;prominence&#x60; (default): 50,000 meters     * &#x60;rankby&#x3D;distance&#x60;: A few kilometers depending on density of area * Query Autocomplete: 50,000 meters * Text Search: 50,000 meters  | [optional]
 **type** | **str**| Restricts the results to places matching the specified type. Only one type may be specified. If more than one type is provided, all types following the first entry are ignored.  * &#x60;type&#x3D;hospital|pharmacy|doctor&#x60; becomes &#x60;type&#x3D;hospital&#x60; * &#x60;type&#x3D;hospital,pharmacy,doctor&#x60; is ignored entirely  See the list of [supported types](https://developers.google.com/maps/documentation/places/web-service/supported_types). &lt;div class&#x3D;\&quot;note\&quot;&gt;Note: Adding both &#x60;keyword&#x60; and &#x60;type&#x60; with the same value (&#x60;keyword&#x3D;cafe&amp;type&#x3D;cafe&#x60; or &#x60;keyword&#x3D;parking&amp;type&#x3D;parking&#x60;) can yield &#x60;ZERO_RESULTS&#x60;.&lt;/div&gt;  | [optional]
 **language** | **str**| The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If &#x60;language&#x60; is not supplied, the API attempts to use the preferred language as specified in the &#x60;Accept-Language&#x60; header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. | [optional] if omitted the server will use the default value of "en"
 **region** | **str**| The region code, specified as a [ccTLD (\&quot;top-level domain\&quot;)](https://en.wikipedia.org/wiki/List_of_Internet_top-level_domains#Country_code_top-level_domains) two-character value. Most ccTLD codes are identical to ISO 3166-1 codes, with some notable exceptions. For example, the United Kingdom&#39;s ccTLD is \&quot;uk\&quot; (.co.uk) while its ISO 3166-1 code is \&quot;gb\&quot; (technically for the entity of \&quot;The United Kingdom of Great Britain and Northern Ireland\&quot;). | [optional] if omitted the server will use the default value of "en"

### Return type

[**PlacesTextSearchResponse**](PlacesTextSearchResponse.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

