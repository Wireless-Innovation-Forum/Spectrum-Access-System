# worldpop_client.TasksApi

All URIs are relative to *https://api.worldpop.org/v1*

Method | HTTP request | Description
------------- | ------------- | -------------
[**tasks_task_id_get**](TasksApi.md#tasks_task_id_get) | **GET** /tasks/{taskId} | 


# **tasks_task_id_get**
> TasksResponse tasks_task_id_get(task_id)



### Example


```python
import time
import worldpop_client
from worldpop_client.api import tasks_api
from worldpop_client.model.tasks_response import TasksResponse
from pprint import pprint
# Defining the host is optional and defaults to https://api.worldpop.org/v1
# See configuration.py for a list of all supported configuration parameters.
configuration = worldpop_client.Configuration(
    host = "https://api.worldpop.org/v1"
)


# Enter a context with an instance of the API client
with worldpop_client.ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = tasks_api.TasksApi(api_client)
    task_id = "taskId_example" # str | 

    # example passing only required values which don't have defaults set
    try:
        api_response = api_instance.tasks_task_id_get(task_id)
        pprint(api_response)
    except worldpop_client.ApiException as e:
        print("Exception when calling TasksApi->tasks_task_id_get: %s\n" % e)
```


### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **task_id** | **str**|  |

### Return type

[**TasksResponse**](TasksResponse.md)

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

