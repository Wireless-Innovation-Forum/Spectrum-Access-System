# worldpop_client.ServicesApi

All URIs are relative to *https://api.worldpop.org/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**services_stats_get**](ServicesApi.md#services_stats_get) | **GET** /services/stats | 


# **services_stats_get**
> StatsResponse services_stats_get(dataset, year, geojson)



### Example


```python
import time
import worldpop_client
from worldpop_client.api import services_api
from worldpop_client.model.stats_response import StatsResponse
from worldpop_client.model.geo_json import GeoJson
from pprint import pprint
# Defining the host is optional and defaults to https://api.worldpop.org/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = worldpop_client.Configuration(
    host = "https://api.worldpop.org/v1"
)


# Enter a context with an instance of the API client
with worldpop_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = services_api.ServicesApi(api_client)
    dataset = "wpgpop" # str | 
    year = 2010 # int | 
    geojson = GeoJson(
        type="FeatureCollection",
        features=[
            GeoJsonFeatures(
                type="Feature",
                geometry=GeometryObject(
                    type="Polygon",
                    coordinates=[
                        [
                            3.14,
                        ],
                    ],
                ),
            ),
        ],
    ) # GeoJson | 
    key = "key_example" # str |  (optional)

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.services_stats_get(dataset, year, geojson)
        pprint(api_response)
    except worldpop_client.ApiException as e:
        print("Exception when calling ServicesApi->services_stats_get: %s\n" % e)

    # example passing only required values which don't have defaults set
    # and optional values
    try:
        api_response = api_instance.services_stats_get(dataset, year, geojson, key=key)
        pprint(api_response)
    except worldpop_client.ApiException as e:
        print("Exception when calling ServicesApi->services_stats_get: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **dataset** | **str**|  |
 **year** | **int**|  |
 **geojson** | **GeoJson**|  |
 **key** | **str**|  | [optional]

### Return type

[**StatsResponse**](StatsResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json


### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | 200 OK |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

