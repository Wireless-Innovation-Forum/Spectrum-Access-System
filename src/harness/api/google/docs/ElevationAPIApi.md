# src.harness.api.google.google_client.ElevationAPIApi

All URIs are relative to *https://www.googleapis.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**elevation**](ElevationAPIApi.md#elevation) | **GET** /maps/api/elevation/json | 


# **elevation**
> InlineResponse200 elevation()



The Elevation API provides a simple interface to query locations on the earth for elevation data. Additionally, you may request sampled elevation data along paths, allowing you to calculate elevation changes along routes. With the Elevation API, you can develop hiking and biking applications, positioning applications, or low resolution surveying applications.  Elevation data is available for all locations on the surface of the earth, including depth locations on the ocean floor (which return negative values). In those cases where Google does not possess exact elevation measurements at the precise location you request, the service interpolates and returns an averaged value using the four nearest locations. Elevation values are expressed relative to local mean sea level (LMSL).  Requests to the Elevation API utilize different parameters based on whether the request is for discrete locations or for an ordered path. For discrete locations, requests for elevation return data on the specific locations passed in the request; for paths, elevation requests are instead sampled along the given path. 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import elevation_api_api
from src.harness.api.google.google_client.model.inline_response200 import InlineResponse200
from src.harness.api.google.google_client.model.lat_lng_array_string import LatLngArrayString
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
    api_instance = elevation_api_api.ElevationAPIApi(api_client)
    locations = LatLngArrayString(["35,-100","40,-110"]) # LatLngArrayString | Positional requests are indicated through use of the locations parameter, indicating elevation requests for the specific locations passed as latitude/longitude values.  The locations parameter may take the following arguments:  - A single coordinate: `locations=40.714728,-73.998672` - An array of coordinates separated using the pipe ('|') character:    ```   locations=40.714728,-73.998672|-34.397,150.644   ``` - A set of encoded coordinates using the [Encoded Polyline Algorithm](https://developers.google.com/maps/documentation/utilities/polylinealgorithm):    ```   locations=enc:gfo}EtohhU   ```  Latitude and longitude coordinate strings are defined using numerals within a comma-separated text string. For example, \"40.714728,-73.998672\" is a valid locations value. Latitude and longitude values must correspond to a valid location on the face of the earth. Latitudes can take any value between -90 and 90 while longitude values can take any value between -180 and 180. If you specify an invalid latitude or longitude value, your request will be rejected as a bad request.  You may pass any number of multiple coordinates within an array or encoded polyline, while still constructing a valid URL. Note that when passing multiple coordinates, the accuracy of any returned data may be of lower resolution than when requesting data for a single coordinate.  (optional)
    path = LatLngArrayString(["35,-110","33,-110","31,-110"]) # LatLngArrayString | An array of comma separated `latitude,longitude` strings. (optional)
    samples = 10 # float | Required if path parameter is set. (optional)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.elevation(locations=locations, path=path, samples=samples)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling ElevationAPIApi->elevation: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **locations** | **LatLngArrayString**| Positional requests are indicated through use of the locations parameter, indicating elevation requests for the specific locations passed as latitude/longitude values.  The locations parameter may take the following arguments:  - A single coordinate: &#x60;locations&#x3D;40.714728,-73.998672&#x60; - An array of coordinates separated using the pipe (&#39;|&#39;) character:    &#x60;&#x60;&#x60;   locations&#x3D;40.714728,-73.998672|-34.397,150.644   &#x60;&#x60;&#x60; - A set of encoded coordinates using the [Encoded Polyline Algorithm](https://developers.google.com/maps/documentation/utilities/polylinealgorithm):    &#x60;&#x60;&#x60;   locations&#x3D;enc:gfo}EtohhU   &#x60;&#x60;&#x60;  Latitude and longitude coordinate strings are defined using numerals within a comma-separated text string. For example, \&quot;40.714728,-73.998672\&quot; is a valid locations value. Latitude and longitude values must correspond to a valid location on the face of the earth. Latitudes can take any value between -90 and 90 while longitude values can take any value between -180 and 180. If you specify an invalid latitude or longitude value, your request will be rejected as a bad request.  You may pass any number of multiple coordinates within an array or encoded polyline, while still constructing a valid URL. Note that when passing multiple coordinates, the accuracy of any returned data may be of lower resolution than when requesting data for a single coordinate.  | [optional]
 **path** | **LatLngArrayString**| An array of comma separated &#x60;latitude,longitude&#x60; strings. | [optional]
 **samples** | **float**| Required if path parameter is set. | [optional]

### Return type

[**InlineResponse200**](InlineResponse200.md)

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

