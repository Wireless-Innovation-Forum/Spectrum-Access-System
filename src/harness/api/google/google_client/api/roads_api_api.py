"""
    Google Maps Platform

    API Specification for Google Maps Platform  # noqa: E501

    The version of the OpenAPI document: 1.17.2
    Generated by: https://openapi-generator.tech
"""


import re  # noqa: F401
import sys  # noqa: F401

from src.harness.api.google.google_client.api_client import ApiClient, Endpoint as _Endpoint
from src.harness.api.google.google_client.model_utils import (  # noqa: F401
    check_allowed_values,
    check_validations,
    date,
    datetime,
    file_type,
    none_type,
    validate_and_convert_types
)
from src.harness.api.google.google_client.model.lat_lng_array_string import LatLngArrayString
from src.harness.api.google.google_client.model.nearest_roads_error_response import NearestRoadsErrorResponse
from src.harness.api.google.google_client.model.nearest_roads_response import NearestRoadsResponse
from src.harness.api.google.google_client.model.snap_to_roads_response import SnapToRoadsResponse


class RoadsAPIApi(object):
    """NOTE: This class is auto generated by OpenAPI Generator
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    def __init__(self, api_client=None):
        if api_client is None:
            api_client = ApiClient()
        self.api_client = api_client
        self.nearest_roads_endpoint = _Endpoint(
            settings={
                'response_type': (NearestRoadsResponse,),
                'auth': [
                    'ApiKeyAuth'
                ],
                'endpoint_path': '/v1/nearestRoads',
                'operation_id': 'nearest_roads',
                'http_method': 'GET',
                'servers': [
                    {
                        'url': "https://roads.googleapis.com",
                        'description': "No description provided",
                    },
                ]
            },
            params_map={
                'all': [
                    'points',
                ],
                'required': [
                    'points',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'points':
                        (LatLngArrayString,),
                },
                'attribute_map': {
                    'points': 'points',
                },
                'location_map': {
                    'points': 'query',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json'
                ],
                'content_type': [],
            },
            api_client=api_client
        )
        self.snap_to_roads_endpoint = _Endpoint(
            settings={
                'response_type': (SnapToRoadsResponse,),
                'auth': [
                    'ApiKeyAuth'
                ],
                'endpoint_path': '/v1/snapToRoads',
                'operation_id': 'snap_to_roads',
                'http_method': 'GET',
                'servers': [
                    {
                        'url': "https://roads.googleapis.com",
                        'description': "No description provided",
                    },
                ]
            },
            params_map={
                'all': [
                    'path',
                    'interpolate',
                ],
                'required': [
                    'path',
                ],
                'nullable': [
                ],
                'enum': [
                ],
                'validation': [
                ]
            },
            root_map={
                'validations': {
                },
                'allowed_values': {
                },
                'openapi_types': {
                    'path':
                        (LatLngArrayString,),
                    'interpolate':
                        (bool,),
                },
                'attribute_map': {
                    'path': 'path',
                    'interpolate': 'interpolate',
                },
                'location_map': {
                    'path': 'query',
                    'interpolate': 'query',
                },
                'collection_format_map': {
                }
            },
            headers_map={
                'accept': [
                    'application/json'
                ],
                'content_type': [],
            },
            api_client=api_client
        )

    def nearest_roads(
        self,
        points,
        **kwargs
    ):
        """nearest_roads  # noqa: E501

        This service returns individual road segments for a given set of GPS coordinates. This services takes up to 100 GPS points and returns the closest road segment for each point. The points passed do not need to be part of a continuous path.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.nearest_roads(points, async_req=True)
        >>> result = thread.get()

        Args:
            points (LatLngArrayString): The path to be snapped. The path parameter accepts a list of latitude/longitude pairs. Latitude and longitude values should be separated by commas. Coordinates should be separated by the pipe character: \"|\". For example: `path=60.170880,24.942795|60.170879,24.942796|60.170877,24.942796`. <div class=\"note\">Note: The snapping algorithm works best for points that are not too far apart. If you observe odd snapping behavior, try creating paths that have points closer together. To ensure the best snap-to-road quality, you should aim to provide paths on which consecutive pairs of points are within 300m of each other. This will also help in handling any isolated, long jumps between consecutive points caused by GPS signal loss, or noise.</div> 

        Keyword Args:
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            async_req (bool): execute request asynchronously

        Returns:
            NearestRoadsResponse
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['points'] = \
            points
        return self.nearest_roads_endpoint.call_with_http_info(**kwargs)

    def snap_to_roads(
        self,
        path,
        **kwargs
    ):
        """snap_to_roads  # noqa: E501

        This service returns the best-fit road geometry for a given set of GPS coordinates. This service takes up to 100 GPS points collected along a route, and returns a similar set of data with the points snapped to the most likely roads the vehicle was traveling along. Optionally, you can request that the points be interpolated, resulting in a path that smoothly follows the geometry of the road.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        >>> thread = api.snap_to_roads(path, async_req=True)
        >>> result = thread.get()

        Args:
            path (LatLngArrayString): The path to be snapped. The path parameter accepts a list of latitude/longitude pairs. Latitude and longitude values should be separated by commas. Coordinates should be separated by the pipe character: \"|\". For example: `path=60.170880,24.942795|60.170879,24.942796|60.170877,24.942796`. <div class=\"note\">Note: The snapping algorithm works best for points that are not too far apart. If you observe odd snapping behavior, try creating paths that have points closer together. To ensure the best snap-to-road quality, you should aim to provide paths on which consecutive pairs of points are within 300m of each other. This will also help in handling any isolated, long jumps between consecutive points caused by GPS signal loss, or noise.</div> 

        Keyword Args:
            interpolate (bool): Whether to interpolate a path to include all points forming the full road-geometry. When true, additional interpolated points will also be returned, resulting in a path that smoothly follows the geometry of the road, even around corners and through tunnels. Interpolated paths will most likely contain more points than the original path. Defaults to `false`. . [optional]
            _return_http_data_only (bool): response data without head status
                code and headers. Default is True.
            _preload_content (bool): if False, the urllib3.HTTPResponse object
                will be returned without reading/decoding response data.
                Default is True.
            _request_timeout (int/float/tuple): timeout setting for this request. If
                one number provided, it will be total request timeout. It can also
                be a pair (tuple) of (connection, read) timeouts.
                Default is None.
            _check_input_type (bool): specifies if type checking
                should be done one the data sent to the server.
                Default is True.
            _check_return_type (bool): specifies if type checking
                should be done one the data received from the server.
                Default is True.
            _host_index (int/None): specifies the index of the server
                that we want to use.
                Default is read from the configuration.
            async_req (bool): execute request asynchronously

        Returns:
            SnapToRoadsResponse
                If the method is called asynchronously, returns the request
                thread.
        """
        kwargs['async_req'] = kwargs.get(
            'async_req', False
        )
        kwargs['_return_http_data_only'] = kwargs.get(
            '_return_http_data_only', True
        )
        kwargs['_preload_content'] = kwargs.get(
            '_preload_content', True
        )
        kwargs['_request_timeout'] = kwargs.get(
            '_request_timeout', None
        )
        kwargs['_check_input_type'] = kwargs.get(
            '_check_input_type', True
        )
        kwargs['_check_return_type'] = kwargs.get(
            '_check_return_type', True
        )
        kwargs['_host_index'] = kwargs.get('_host_index')
        kwargs['path'] = \
            path
        return self.snap_to_roads_endpoint.call_with_http_info(**kwargs)

