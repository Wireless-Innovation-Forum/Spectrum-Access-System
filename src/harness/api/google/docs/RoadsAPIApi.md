# src.harness.api.google.google_client.RoadsAPIApi

All URIs are relative to *https://www.googleapis.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**nearest_roads**](RoadsAPIApi.md#nearest_roads) | **GET** /v1/nearestRoads | 
[**snap_to_roads**](RoadsAPIApi.md#snap_to_roads) | **GET** /v1/snapToRoads | 


# **nearest_roads**
> NearestRoadsResponse nearest_roads(points)



This service returns individual road segments for a given set of GPS coordinates. This services takes up to 100 GPS points and returns the closest road segment for each point. The points passed do not need to be part of a continuous path.

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import roads_api_api
from src.harness.api.google.google_client.model.nearest_roads_response import NearestRoadsResponse
from src.harness.api.google.google_client.model.lat_lng_array_string import LatLngArrayString
from src.harness.api.google.google_client.model.nearest_roads_error_response import NearestRoadsErrorResponse
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
    api_instance = roads_api_api.RoadsAPIApi(api_client)
    points = LatLngArrayString(["60.170880,24.942795","60.170879,24.942796","60.170877,24.942796"]) # LatLngArrayString | The path to be snapped. The path parameter accepts a list of latitude/longitude pairs. Latitude and longitude values should be separated by commas. Coordinates should be separated by the pipe character: \"|\". For example: `path=60.170880,24.942795|60.170879,24.942796|60.170877,24.942796`. <div class=\"note\">Note: The snapping algorithm works best for points that are not too far apart. If you observe odd snapping behavior, try creating paths that have points closer together. To ensure the best snap-to-road quality, you should aim to provide paths on which consecutive pairs of points are within 300m of each other. This will also help in handling any isolated, long jumps between consecutive points caused by GPS signal loss, or noise.</div> 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.nearest_roads(points)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling RoadsAPIApi->nearest_roads: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **points** | **LatLngArrayString**| The path to be snapped. The path parameter accepts a list of latitude/longitude pairs. Latitude and longitude values should be separated by commas. Coordinates should be separated by the pipe character: \&quot;|\&quot;. For example: &#x60;path&#x3D;60.170880,24.942795|60.170879,24.942796|60.170877,24.942796&#x60;. &lt;div class&#x3D;\&quot;note\&quot;&gt;Note: The snapping algorithm works best for points that are not too far apart. If you observe odd snapping behavior, try creating paths that have points closer together. To ensure the best snap-to-road quality, you should aim to provide paths on which consecutive pairs of points are within 300m of each other. This will also help in handling any isolated, long jumps between consecutive points caused by GPS signal loss, or noise.&lt;/div&gt;  |

### Return type

[**NearestRoadsResponse**](NearestRoadsResponse.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |
**400** | 400 BAD REQUEST |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **snap_to_roads**
> SnapToRoadsResponse snap_to_roads(path)



This service returns the best-fit road geometry for a given set of GPS coordinates. This service takes up to 100 GPS points collected along a route, and returns a similar set of data with the points snapped to the most likely roads the vehicle was traveling along. Optionally, you can request that the points be interpolated, resulting in a path that smoothly follows the geometry of the road.

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import roads_api_api
from src.harness.api.google.google_client.model.snap_to_roads_response import SnapToRoadsResponse
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
    api_instance = roads_api_api.RoadsAPIApi(api_client)
    path = LatLngArrayString(["60.170880,24.942795","60.170879,24.942796","60.170877,24.942796"]) # LatLngArrayString | The path to be snapped. The path parameter accepts a list of latitude/longitude pairs. Latitude and longitude values should be separated by commas. Coordinates should be separated by the pipe character: \"|\". For example: `path=60.170880,24.942795|60.170879,24.942796|60.170877,24.942796`. <div class=\"note\">Note: The snapping algorithm works best for points that are not too far apart. If you observe odd snapping behavior, try creating paths that have points closer together. To ensure the best snap-to-road quality, you should aim to provide paths on which consecutive pairs of points are within 300m of each other. This will also help in handling any isolated, long jumps between consecutive points caused by GPS signal loss, or noise.</div> 
    interpolate = True # bool | Whether to interpolate a path to include all points forming the full road-geometry. When true, additional interpolated points will also be returned, resulting in a path that smoothly follows the geometry of the road, even around corners and through tunnels. Interpolated paths will most likely contain more points than the original path. Defaults to `false`.  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.snap_to_roads(path)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling RoadsAPIApi->snap_to_roads: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.snap_to_roads(path, interpolate=interpolate)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling RoadsAPIApi->snap_to_roads: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **path** | **LatLngArrayString**| The path to be snapped. The path parameter accepts a list of latitude/longitude pairs. Latitude and longitude values should be separated by commas. Coordinates should be separated by the pipe character: \&quot;|\&quot;. For example: &#x60;path&#x3D;60.170880,24.942795|60.170879,24.942796|60.170877,24.942796&#x60;. &lt;div class&#x3D;\&quot;note\&quot;&gt;Note: The snapping algorithm works best for points that are not too far apart. If you observe odd snapping behavior, try creating paths that have points closer together. To ensure the best snap-to-road quality, you should aim to provide paths on which consecutive pairs of points are within 300m of each other. This will also help in handling any isolated, long jumps between consecutive points caused by GPS signal loss, or noise.&lt;/div&gt;  |
 **interpolate** | **bool**| Whether to interpolate a path to include all points forming the full road-geometry. When true, additional interpolated points will also be returned, resulting in a path that smoothly follows the geometry of the road, even around corners and through tunnels. Interpolated paths will most likely contain more points than the original path. Defaults to &#x60;false&#x60;.  | [optional]

### Return type

[**SnapToRoadsResponse**](SnapToRoadsResponse.md)

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

