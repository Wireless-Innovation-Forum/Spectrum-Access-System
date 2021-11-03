# src.harness.api.google.google_client.GeolocationAPIApi

All URIs are relative to *https://www.googleapis.com*

Method | HTTP request | Description
------------- | ------------- | -------------
[**geolocate**](GeolocationAPIApi.md#geolocate) | **POST** /geolocation/v1/geolocate | 


# **geolocate**
> GeolocationResponse geolocate()



Geolocation API returns a location and accuracy radius based on information about cell towers and WiFi nodes that the mobile client can detect. This document describes the protocol used to send this data to the server and to return a response to the client.  Communication is done over HTTPS using POST. Both request and response are formatted as JSON, and the content type of both is `application/json`.  You must specify a key in your request, included as the value of a`key` parameter. A `key` is your application's  API key. This key identifies your application for purposes of quota management. Learn how to [get a key](https://developers.google.com/maps/documentation/geolocation/get-api-key).

### Example

* Api Key Authentication (ApiKeyAuth):

```python
import time
import src.harness.api.google.google_client
from src.harness.api.google.google_client.api import geolocation_api_api
from src.harness.api.google.google_client.model.error_response import ErrorResponse
from src.harness.api.google.google_client.model.geolocation_request import GeolocationRequest
from src.harness.api.google.google_client.model.geolocation_response import GeolocationResponse
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
    api_instance = geolocation_api_api.GeolocationAPIApi(api_client)
    geolocation_request = GeolocationRequest(
        home_mobile_country_code=1,
        home_mobile_network_code=1,
        radio_type="radio_type_example",
        carrier="carrier_example",
        consider_ip="consider_ip_example",
        cell_towers=[
            CellTower(
                cell_id=1,
                location_area_code=1,
                mobile_country_code=1,
                mobile_network_code=1,
                age=1,
                signal_strength=3.14,
                timing_advance=3.14,
            ),
        ],
        wifi_access_points=[
            WiFiAccessPoint(
                mac_address="mac_address_example",
                signal_strength=1,
                signal_to_noise_ratio=1,
                age=1,
                channel=1,
            ),
        ],
    ) # GeolocationRequest | The request body must be formatted as JSON. (optional)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.geolocate(geolocation_request=geolocation_request)
        pprint(api_response)
    except src.harness.api.google.google_client.ApiException as e:
        print("Exception when calling GeolocationAPIApi->geolocate: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **geolocation_request** | [**GeolocationRequest**](GeolocationRequest.md)| The request body must be formatted as JSON. | [optional]

### Return type

[**GeolocationResponse**](GeolocationResponse.md)

### Authorization

[ApiKeyAuth](../README.md#ApiKeyAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |
**400** | 400 BAD REQUEST |  -  |
**404** | 404 NOT FOUND |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

