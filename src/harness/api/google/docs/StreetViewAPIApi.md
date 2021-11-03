# src.harness.api.google.google_client.StreetViewAPIApi

All URIs are relative to *https://www.googleapis.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**street_view**](StreetViewAPIApi.md#street_view) | **GET** /maps/api/streetview | 
[**street_view_metadata**](StreetViewAPIApi.md#street_view_metadata) | **GET** /maps/api/streetview/metadata | 


# **street_view**
> file_type street_view(size)



The Street View Static API lets you embed a static (non-interactive) Street View panorama or thumbnail into your web page, without the use of JavaScript. The viewport is defined with URL parameters sent through a standard HTTP request, and is returned as a static image. 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import street_view_api_api
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
    api_instance = street_view_api_api.StreetViewAPIApi(api_client)
    size = "size_example" # str | Specifies the output size of the image in pixels. Size is specified as `{width}x{height}` - for example, `size=600x400` returns an image 600 pixels wide, and 400 high. 
    fov = 3.14 # float | Determines the horizontal field of view of the image. The field of view is expressed in degrees, with a maximum allowed value of 120. When dealing with a fixed-size viewport, as with a Street View image of a set size, field of view in essence represents zoom, with smaller numbers indicating a higher level of zoom. Default is 90.  (optional)
    heading = 3.14 # float | Indicates the compass heading of the camera. Accepted values are from 0 to 360 (both values indicating North, with 90 indicating East, and 180 South). If no heading is specified, a value will be calculated that directs the camera towards the specified location, from the point at which the closest photograph was taken.  (optional)
    location = "40,-110" # str | The point around which to retrieve place information. The Street View Static API will snap to the panorama photographed closest to this location. When an address text string is provided, the API may use a different camera location to better display the specified location. When a lat/lng is provided, the API searches a 50 meter radius for a photograph closest to this location. Because Street View imagery is periodically refreshed, and photographs may be taken from slightly different positions each time, it's possible that your `location` may snap to a different panorama when imagery is updated.  (optional)
    pano = "pano_example" # str | A specific panorama ID. These are generally stable, though panoramas may change ID over time as imagery is refreshed.  (optional)
    pitch = 3.14 # float | Specifies the up or down angle of the camera relative to the Street View vehicle. This is often, but not always, flat horizontal. Positive values angle the camera up (with 90 degrees indicating straight up); negative values angle the camera down (with -90 indicating straight down). Default is 0.  (optional)
    radius = 3.14 # float | Sets a radius, specified in meters, in which to search for a panorama, centered on the given latitude and longitude. Valid values are non-negative integers. Default is 50 meters.  (optional)
    return_error_code = True # bool | Indicates whether the API should return a non `200 Ok` HTTP status when no image is found (`404 NOT FOUND`), or in response to an invalid request (400 BAD REQUEST). Valid values are `true` and `false`. If set to `true`, an error message is returned in place of the generic gray image. This eliminates the need to make a separate call to check for image availability.  (optional)
    signature = "signature_example" # str | A digital signature used to verify that any site generating requests using your API key is authorized to do so. Requests that do not include a digital signature might fail. For more information, see [Get a Key and Signature](https://developers.google.com/maps/documentation/streetview/get-api-key).  (optional)
    source = "default" # str | Limits Street View searches to selected sources. Valid values are: * `default` uses the default sources for Street View; searches are not limited to specific sources. * `outdoor` limits searches to outdoor collections. Indoor collections are not included in search results. Note that outdoor panoramas may not exist for the specified location. Also note that the search only returns panoramas where it's possible to determine whether they're indoors or outdoors. For example, PhotoSpheres are not returned because it's unknown whether they are indoors or outdoors.  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.street_view(size)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling StreetViewAPIApi->street_view: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.street_view(size, fov=fov, heading=heading, location=location, pano=pano, pitch=pitch, radius=radius, return_error_code=return_error_code, signature=signature, source=source)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling StreetViewAPIApi->street_view: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **size** | **str**| Specifies the output size of the image in pixels. Size is specified as &#x60;{width}x{height}&#x60; - for example, &#x60;size&#x3D;600x400&#x60; returns an image 600 pixels wide, and 400 high.  |
 **fov** | **float**| Determines the horizontal field of view of the image. The field of view is expressed in degrees, with a maximum allowed value of 120. When dealing with a fixed-size viewport, as with a Street View image of a set size, field of view in essence represents zoom, with smaller numbers indicating a higher level of zoom. Default is 90.  | [optional]
 **heading** | **float**| Indicates the compass heading of the camera. Accepted values are from 0 to 360 (both values indicating North, with 90 indicating East, and 180 South). If no heading is specified, a value will be calculated that directs the camera towards the specified location, from the point at which the closest photograph was taken.  | [optional]
 **location** | **str**| The point around which to retrieve place information. The Street View Static API will snap to the panorama photographed closest to this location. When an address text string is provided, the API may use a different camera location to better display the specified location. When a lat/lng is provided, the API searches a 50 meter radius for a photograph closest to this location. Because Street View imagery is periodically refreshed, and photographs may be taken from slightly different positions each time, it&#39;s possible that your &#x60;location&#x60; may snap to a different panorama when imagery is updated.  | [optional]
 **pano** | **str**| A specific panorama ID. These are generally stable, though panoramas may change ID over time as imagery is refreshed.  | [optional]
 **pitch** | **float**| Specifies the up or down angle of the camera relative to the Street View vehicle. This is often, but not always, flat horizontal. Positive values angle the camera up (with 90 degrees indicating straight up); negative values angle the camera down (with -90 indicating straight down). Default is 0.  | [optional]
 **radius** | **float**| Sets a radius, specified in meters, in which to search for a panorama, centered on the given latitude and longitude. Valid values are non-negative integers. Default is 50 meters.  | [optional]
 **return_error_code** | **bool**| Indicates whether the API should return a non &#x60;200 Ok&#x60; HTTP status when no image is found (&#x60;404 NOT FOUND&#x60;), or in response to an invalid request (400 BAD REQUEST). Valid values are &#x60;true&#x60; and &#x60;false&#x60;. If set to &#x60;true&#x60;, an error message is returned in place of the generic gray image. This eliminates the need to make a separate call to check for image availability.  | [optional]
 **signature** | **str**| A digital signature used to verify that any site generating requests using your API key is authorized to do so. Requests that do not include a digital signature might fail. For more information, see [Get a Key and Signature](https://developers.google.com/maps/documentation/streetview/get-api-key).  | [optional]
 **source** | **str**| Limits Street View searches to selected sources. Valid values are: * &#x60;default&#x60; uses the default sources for Street View; searches are not limited to specific sources. * &#x60;outdoor&#x60; limits searches to outdoor collections. Indoor collections are not included in search results. Note that outdoor panoramas may not exist for the specified location. Also note that the search only returns panoramas where it&#39;s possible to determine whether they&#39;re indoors or outdoors. For example, PhotoSpheres are not returned because it&#39;s unknown whether they are indoors or outdoors.  | [optional]

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

# **street_view_metadata**
> StreetViewResponse street_view_metadata()



The Street View Static API metadata requests provide data about Street View panoramas. Using the metadata, you can find out if a Street View image is available at a given location, as well as getting programmatic access to the latitude and longitude, the panorama ID, the date the photo was taken, and the copyright information for the image. Accessing this metadata allows you to customize error behavior in your application. 

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import street_view_api_api
from src.harness.api.google.google_client.model.street_view_response import StreetViewResponse
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
    api_instance = street_view_api_api.StreetViewAPIApi(api_client)
    heading = 3.14 # float | Indicates the compass heading of the camera. Accepted values are from 0 to 360 (both values indicating North, with 90 indicating East, and 180 South). If no heading is specified, a value will be calculated that directs the camera towards the specified location, from the point at which the closest photograph was taken.  (optional)
    location = "40,-110" # str | The point around which to retrieve place information. The Street View Static API will snap to the panorama photographed closest to this location. When an address text string is provided, the API may use a different camera location to better display the specified location. When a lat/lng is provided, the API searches a 50 meter radius for a photograph closest to this location. Because Street View imagery is periodically refreshed, and photographs may be taken from slightly different positions each time, it's possible that your `location` may snap to a different panorama when imagery is updated.  (optional)
    pano = "pano_example" # str | A specific panorama ID. These are generally stable, though panoramas may change ID over time as imagery is refreshed.  (optional)
    pitch = 3.14 # float | Specifies the up or down angle of the camera relative to the Street View vehicle. This is often, but not always, flat horizontal. Positive values angle the camera up (with 90 degrees indicating straight up); negative values angle the camera down (with -90 indicating straight down). Default is 0.  (optional)
    radius = 3.14 # float | Sets a radius, specified in meters, in which to search for a panorama, centered on the given latitude and longitude. Valid values are non-negative integers. Default is 50 meters.  (optional)
    return_error_code = True # bool | Indicates whether the API should return a non `200 Ok` HTTP status when no image is found (`404 NOT FOUND`), or in response to an invalid request (400 BAD REQUEST). Valid values are `true` and `false`. If set to `true`, an error message is returned in place of the generic gray image. This eliminates the need to make a separate call to check for image availability.  (optional)
    signature = "signature_example" # str | A digital signature used to verify that any site generating requests using your API key is authorized to do so. Requests that do not include a digital signature might fail. For more information, see [Get a Key and Signature](https://developers.google.com/maps/documentation/streetview/get-api-key).  (optional)
    size = "size_example" # str | Specifies the output size of the image in pixels. Size is specified as `{width}x{height}` - for example, `size=600x400` returns an image 600 pixels wide, and 400 high.  (optional)
    source = "default" # str | Limits Street View searches to selected sources. Valid values are: * `default` uses the default sources for Street View; searches are not limited to specific sources. * `outdoor` limits searches to outdoor collections. Indoor collections are not included in search results. Note that outdoor panoramas may not exist for the specified location. Also note that the search only returns panoramas where it's possible to determine whether they're indoors or outdoors. For example, PhotoSpheres are not returned because it's unknown whether they are indoors or outdoors.  (optional)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.street_view_metadata(heading=heading, location=location, pano=pano, pitch=pitch, radius=radius, return_error_code=return_error_code, signature=signature, size=size, source=source)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling StreetViewAPIApi->street_view_metadata: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **heading** | **float**| Indicates the compass heading of the camera. Accepted values are from 0 to 360 (both values indicating North, with 90 indicating East, and 180 South). If no heading is specified, a value will be calculated that directs the camera towards the specified location, from the point at which the closest photograph was taken.  | [optional]
 **location** | **str**| The point around which to retrieve place information. The Street View Static API will snap to the panorama photographed closest to this location. When an address text string is provided, the API may use a different camera location to better display the specified location. When a lat/lng is provided, the API searches a 50 meter radius for a photograph closest to this location. Because Street View imagery is periodically refreshed, and photographs may be taken from slightly different positions each time, it&#39;s possible that your &#x60;location&#x60; may snap to a different panorama when imagery is updated.  | [optional]
 **pano** | **str**| A specific panorama ID. These are generally stable, though panoramas may change ID over time as imagery is refreshed.  | [optional]
 **pitch** | **float**| Specifies the up or down angle of the camera relative to the Street View vehicle. This is often, but not always, flat horizontal. Positive values angle the camera up (with 90 degrees indicating straight up); negative values angle the camera down (with -90 indicating straight down). Default is 0.  | [optional]
 **radius** | **float**| Sets a radius, specified in meters, in which to search for a panorama, centered on the given latitude and longitude. Valid values are non-negative integers. Default is 50 meters.  | [optional]
 **return_error_code** | **bool**| Indicates whether the API should return a non &#x60;200 Ok&#x60; HTTP status when no image is found (&#x60;404 NOT FOUND&#x60;), or in response to an invalid request (400 BAD REQUEST). Valid values are &#x60;true&#x60; and &#x60;false&#x60;. If set to &#x60;true&#x60;, an error message is returned in place of the generic gray image. This eliminates the need to make a separate call to check for image availability.  | [optional]
 **signature** | **str**| A digital signature used to verify that any site generating requests using your API key is authorized to do so. Requests that do not include a digital signature might fail. For more information, see [Get a Key and Signature](https://developers.google.com/maps/documentation/streetview/get-api-key).  | [optional]
 **size** | **str**| Specifies the output size of the image in pixels. Size is specified as &#x60;{width}x{height}&#x60; - for example, &#x60;size&#x3D;600x400&#x60; returns an image 600 pixels wide, and 400 high.  | [optional]
 **source** | **str**| Limits Street View searches to selected sources. Valid values are: * &#x60;default&#x60; uses the default sources for Street View; searches are not limited to specific sources. * &#x60;outdoor&#x60; limits searches to outdoor collections. Indoor collections are not included in search results. Note that outdoor panoramas may not exist for the specified location. Also note that the search only returns panoramas where it&#39;s possible to determine whether they&#39;re indoors or outdoors. For example, PhotoSpheres are not returned because it&#39;s unknown whether they are indoors or outdoors.  | [optional]

### Return type

[**StreetViewResponse**](StreetViewResponse.md)

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

