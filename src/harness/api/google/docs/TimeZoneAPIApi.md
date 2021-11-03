# src.harness.api.google.google_client.TimeZoneAPIApi

All URIs are relative to *https://www.googleapis.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**timezone**](TimeZoneAPIApi.md#timezone) | **GET** /maps/api/timezone/json | 


# **timezone**
> TimeZoneResponse timezone(location, timestamp)



The Time Zone API provides a simple interface to request the time zone for locations on the surface of the earth, as well as the time offset from UTC for each of those locations. You request the time zone information for a specific latitude/longitude pair and date. The API returns the name of that time zone, the time offset from UTC, and the daylight savings offset. 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import time_zone_api_api
from src.harness.api.google.google_client.model.time_zone_response import TimeZoneResponse
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
    api_instance = time_zone_api_api.TimeZoneAPIApi(api_client)
    location = "39.6034810,-119.6822510" # str | A comma-separated latitude,longitude tuple, `location=39.6034810,-119.6822510`, representing the location to look up. 
    timestamp = 1331161200 # float | The desired time as seconds since midnight, January 1, 1970 UTC. The Time Zone API uses the `timestamp` to determine whether or not Daylight Savings should be applied, based on the time zone of the `location`.   Note that the API does not take historical time zones into account. That is, if you specify a past timestamp, the API does not take into account the possibility that the location was previously in a different time zone. 
    language = "en" # str | The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If `language` is not supplied, the API attempts to use the preferred language as specified in the `Accept-Language` header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. (optional) if omitted the server will use the default value of "en"

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.timezone(location, timestamp)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling TimeZoneAPIApi->timezone: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.timezone(location, timestamp, language=language)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling TimeZoneAPIApi->timezone: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **location** | **str**| A comma-separated latitude,longitude tuple, &#x60;location&#x3D;39.6034810,-119.6822510&#x60;, representing the location to look up.  |
 **timestamp** | **float**| The desired time as seconds since midnight, January 1, 1970 UTC. The Time Zone API uses the &#x60;timestamp&#x60; to determine whether or not Daylight Savings should be applied, based on the time zone of the &#x60;location&#x60;.   Note that the API does not take historical time zones into account. That is, if you specify a past timestamp, the API does not take into account the possibility that the location was previously in a different time zone.  |
 **language** | **str**| The language in which to return results.  * See the [list of supported languages](https://developers.google.com/maps/faq#languagesupport). Google often updates the supported languages, so this list may not be exhaustive. * If &#x60;language&#x60; is not supplied, the API attempts to use the preferred language as specified in the &#x60;Accept-Language&#x60; header. * The API does its best to provide a street address that is readable for both the user and locals. To achieve that goal, it returns street addresses in the local language, transliterated to a script readable by the user if necessary, observing the preferred language. All other addresses are returned in the preferred language. Address components are all returned in the same language, which is chosen from the first component. * If a name is not available in the preferred language, the API uses the closest match. * The preferred language has a small influence on the set of results that the API chooses to return, and the order in which they are returned. The geocoder interprets abbreviations differently depending on language, such as the abbreviations for street types, or synonyms that may be valid in one language but not in another. For example, _utca_ and _tér_ are synonyms for street in Hungarian. | [optional] if omitted the server will use the default value of "en"

### Return type

[**TimeZoneResponse**](TimeZoneResponse.md)

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

