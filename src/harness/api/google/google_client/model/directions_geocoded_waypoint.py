"""
    Google Maps Platform

    API Specification for Google Maps Platform  # noqa: E501

    The version of the OpenAPI document: 1.17.2
    Generated by: https://openapi-generator.tech
"""


import re  # noqa: F401
import sys  # noqa: F401

from src.harness.api.google.google_client.model_utils import (  # noqa: F401
    ApiTypeError,
    ModelComposed,
    ModelNormal,
    ModelSimple,
    cached_property,
    change_keys_js_to_python,
    convert_js_args_to_python_args,
    date,
    datetime,
    file_type,
    none_type,
    validate_get_composed_info,
)
from ..model_utils import OpenApiModel
from src.harness.api.google.google_client.exceptions import ApiAttributeError



class DirectionsGeocodedWaypoint(ModelNormal):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.

    Attributes:
      allowed_values (dict): The key is the tuple path to the attribute
          and the for var_name this is (var_name,). The value is a dict
          with a capitalized key describing the allowed value and an allowed
          value. These dicts store the allowed enum values.
      attribute_map (dict): The key is attribute name
          and the value is json key in definition.
      discriminator_value_class_map (dict): A dict to go from the discriminator
          variable value to the discriminator class name.
      validations (dict): The key is the tuple path to the attribute
          and the for var_name this is (var_name,). The value is a dict
          that stores validations for max_length, min_length, max_items,
          min_items, exclusive_maximum, inclusive_maximum, exclusive_minimum,
          inclusive_minimum, and regex.
      additional_properties_type (tuple): A tuple of classes accepted
          as additional properties values.
    """

    allowed_values = {
        ('geocoder_status',): {
            'OK': "OK",
            'ZERO_RESULTS': "ZERO_RESULTS",
        },
        ('types',): {
            'ADMINISTRATIVE_AREA_LEVEL_1': "administrative_area_level_1",
            'ADMINISTRATIVE_AREA_LEVEL_2': "administrative_area_level_2",
            'ADMINISTRATIVE_AREA_LEVEL_3': "administrative_area_level_3",
            'ADMINISTRATIVE_AREA_LEVEL_4': "administrative_area_level_4",
            'ADMINISTRATIVE_AREA_LEVEL_5': "administrative_area_level_5",
            'AMUSEMENT_PARK': "amusement_park",
            'AIRPORT': "airport",
            'COLLOQUIAL_AREA': "colloquial_area",
            'COUNTRY': "country",
            'ESTABLISHMENT': "establishment",
            'INTERSECTION': "intersection",
            'LOCALITY': "locality",
            'NATURAL_FEATURE': "natural_feature",
            'NEIGHBORHOOD': "neighborhood",
            'PARK': "park",
            'PLUS_CODE': "plus_code",
            'POINT_OF_INTEREST': "point_of_interest",
            'POLITICAL': "political",
            'POSTAL_CODE': "postal_code",
            'PREMISE': "premise",
            'ROUTE': "route",
            'STREET_ADDRESS': "street_address",
            'SUBLOCALITY': "sublocality",
            'SUBLOCALITY_LEVEL_1': "sublocality_level_1",
            'SUBPREMISE': "subpremise",
            'TRANSIT_STATION': "transit_station",
            'TOURIST_ATTRACTION': "tourist_attraction",
        },
    }

    validations = {
    }

    @cached_property
    def additional_properties_type():
        """
        This must be a method because a model may have properties that are
        of type self, this must run after the class is loaded
        """
        return (bool, date, datetime, dict, float, int, list, str, none_type,)  # noqa: E501

    _nullable = False

    @cached_property
    def openapi_types():
        """
        This must be a method because a model may have properties that are
        of type self, this must run after the class is loaded

        Returns
            openapi_types (dict): The key is attribute name
                and the value is attribute type.
        """
        return {
            'geocoder_status': (str,),  # noqa: E501
            'partial_match': (bool, date, datetime, dict, float, int, list, str, none_type,),  # noqa: E501
            'place_id': (str,),  # noqa: E501
            'types': ([str],),  # noqa: E501
        }

    @cached_property
    def discriminator():
        return None


    attribute_map = {
        'geocoder_status': 'geocoder_status',  # noqa: E501
        'partial_match': 'partial_match',  # noqa: E501
        'place_id': 'place_id',  # noqa: E501
        'types': 'types',  # noqa: E501
    }

    read_only_vars = {
    }

    _composed_schemas = {}

    @classmethod
    @convert_js_args_to_python_args
    def _from_openapi_data(cls, *args, **kwargs):  # noqa: E501
        """DirectionsGeocodedWaypoint - a model defined in OpenAPI

        Keyword Args:
            _check_type (bool): if True, values for parameters in openapi_types
                                will be type checked and a TypeError will be
                                raised if the wrong type is input.
                                Defaults to True
            _path_to_item (tuple/list): This is a list of keys or values to
                                drill down to the model in received_data
                                when deserializing a response
            _spec_property_naming (bool): True if the variable names in the input data
                                are serialized names, as specified in the OpenAPI document.
                                False if the variable names in the input data
                                are pythonic names, e.g. snake case (default)
            _configuration (Configuration): the instance to use when
                                deserializing a file_type parameter.
                                If passed, type conversion is attempted
                                If omitted no type conversion is done.
            _visited_composed_classes (tuple): This stores a tuple of
                                classes that we have traveled through so that
                                if we see that class again we will not use its
                                discriminator again.
                                When traveling through a discriminator, the
                                composed schema that is
                                is traveled through is added to this set.
                                For example if Animal has a discriminator
                                petType and we pass in "Dog", and the class Dog
                                allOf includes Animal, we move through Animal
                                once using the discriminator, and pick Dog.
                                Then in Dog, we will make an instance of the
                                Animal class but this time we won't travel
                                through its discriminator because we passed in
                                _visited_composed_classes = (Animal,)
            geocoder_status (str): Indicates the status code resulting from the geocoding operation. This field may contain the following values.. [optional]  # noqa: E501
            partial_match (bool, date, datetime, dict, float, int, list, str, none_type): Indicates that the geocoder did not return an exact match for the original request, though it was able to match part of the requested address. You may wish to examine the original request for misspellings and/or an incomplete address.  Partial matches most often occur for street addresses that do not exist within the locality you pass in the request. Partial matches may also be returned when a request matches two or more locations in the same locality. For example, \"21 Henr St, Bristol, UK\" will return a partial match for both Henry Street and Henrietta Street. Note that if a request includes a misspelled address component, the geocoding service may suggest an alternative address. Suggestions triggered in this way will also be marked as a partial match. . [optional]  # noqa: E501
            place_id (str): A unique identifier that can be used with other Google APIs. See the [Place ID overview](https://developers.google.com/maps/documentation/places/web-service/place-id).. [optional]  # noqa: E501
            types ([str]): Indicates the address type of the geocoding result used for calculating directions.  * `administrative_area_level_1` indicates a first-order civil entity below the country level. Within the United States, these administrative levels are states. Not all nations exhibit these administrative levels. In most cases, administrative_area_level_1 short names will closely match ISO 3166-2 subdivisions and other widely circulated lists; however this is not guaranteed as our geocoding results are based on a variety of signals and location data. * `administrative_area_level_2` indicates a second-order civil entity below the country level. Within the United States, these administrative levels are counties. Not all nations exhibit these administrative levels. * `administrative_area_level_3` indicates a third-order civil entity below the country level. This type indicates a minor civil division. Not all nations exhibit these administrative levels. * `administrative_area_level_4` indicates a fourth-order civil entity below the country level. This type indicates a minor civil division. Not all nations exhibit these administrative levels. * `administrative_area_level_5` indicates a fifth-order civil entity below the country level. This type indicates a minor civil division. Not all nations exhibit these administrative levels. * `airport` indicates an airport. * `colloquial_area` indicates a commonly-used alternative name for the entity. * `country` indicates the national political entity, and is typically the highest order type returned by the Geocoder. * `intersection` indicates a major intersection, usually of two major roads. * `locality` indicates an incorporated city or town political entity. * `natural_feature` indicates a prominent natural feature. * `neighborhood` indicates a named neighborhood * `park` indicates a named park. * `plus_code` indicates an encoded location reference, derived from latitude and longitude. Plus codes can be used as a replacement for street addresses in places where they do not exist (where buildings are not numbered or streets are not named). See [https://plus.codes](https://plus.codes/) for details. * `point_of_interest` indicates a named point of interest. Typically, these \"POI\"s are prominent local entities that don't easily fit in another category, such as \"Empire State Building\" or \"Eiffel Tower\". * `political` indicates a political entity. Usually, this type indicates a polygon of some civil administration. * `postal_code` indicates a postal code as used to address postal mail within the country. * `premise` indicates a named location, usually a building or collection of buildings with a common name * `route` indicates a named route (such as \"US 101\"). * `street_address` indicates a precise street address. * `sublocality` indicates a first-order civil entity below a locality. For some locations may receive one of the additional types: sublocality_level_1 to sublocality_level_5. Each sublocality level is a civil entity. Larger numbers indicate a smaller geographic area. * `subpremise` indicates a first-order entity below a named location, usually a singular building within a collection of buildings with a common name * `transit_station` indicates a transit station.  An empty list of types indicates there are no known types for the particular address component, for example, Lieu-dit in France. . [optional]  # noqa: E501
        """

        _check_type = kwargs.pop('_check_type', True)
        _spec_property_naming = kwargs.pop('_spec_property_naming', False)
        _path_to_item = kwargs.pop('_path_to_item', ())
        _configuration = kwargs.pop('_configuration', None)
        _visited_composed_classes = kwargs.pop('_visited_composed_classes', ())

        self = super(OpenApiModel, cls).__new__(cls)

        if args:
            raise ApiTypeError(
                "Invalid positional arguments=%s passed to %s. Remove those invalid positional arguments." % (
                    args,
                    self.__class__.__name__,
                ),
                path_to_item=_path_to_item,
                valid_classes=(self.__class__,),
            )

        self._data_store = {}
        self._check_type = _check_type
        self._spec_property_naming = _spec_property_naming
        self._path_to_item = _path_to_item
        self._configuration = _configuration
        self._visited_composed_classes = _visited_composed_classes + (self.__class__,)

        for var_name, var_value in kwargs.items():
            if var_name not in self.attribute_map and \
                        self._configuration is not None and \
                        self._configuration.discard_unknown_keys and \
                        self.additional_properties_type is None:
                # discard variable.
                continue
            setattr(self, var_name, var_value)
        return self

    required_properties = set([
        '_data_store',
        '_check_type',
        '_spec_property_naming',
        '_path_to_item',
        '_configuration',
        '_visited_composed_classes',
    ])

    @convert_js_args_to_python_args
    def __init__(self, *args, **kwargs):  # noqa: E501
        """DirectionsGeocodedWaypoint - a model defined in OpenAPI

        Keyword Args:
            _check_type (bool): if True, values for parameters in openapi_types
                                will be type checked and a TypeError will be
                                raised if the wrong type is input.
                                Defaults to True
            _path_to_item (tuple/list): This is a list of keys or values to
                                drill down to the model in received_data
                                when deserializing a response
            _spec_property_naming (bool): True if the variable names in the input data
                                are serialized names, as specified in the OpenAPI document.
                                False if the variable names in the input data
                                are pythonic names, e.g. snake case (default)
            _configuration (Configuration): the instance to use when
                                deserializing a file_type parameter.
                                If passed, type conversion is attempted
                                If omitted no type conversion is done.
            _visited_composed_classes (tuple): This stores a tuple of
                                classes that we have traveled through so that
                                if we see that class again we will not use its
                                discriminator again.
                                When traveling through a discriminator, the
                                composed schema that is
                                is traveled through is added to this set.
                                For example if Animal has a discriminator
                                petType and we pass in "Dog", and the class Dog
                                allOf includes Animal, we move through Animal
                                once using the discriminator, and pick Dog.
                                Then in Dog, we will make an instance of the
                                Animal class but this time we won't travel
                                through its discriminator because we passed in
                                _visited_composed_classes = (Animal,)
            geocoder_status (str): Indicates the status code resulting from the geocoding operation. This field may contain the following values.. [optional]  # noqa: E501
            partial_match (bool, date, datetime, dict, float, int, list, str, none_type): Indicates that the geocoder did not return an exact match for the original request, though it was able to match part of the requested address. You may wish to examine the original request for misspellings and/or an incomplete address.  Partial matches most often occur for street addresses that do not exist within the locality you pass in the request. Partial matches may also be returned when a request matches two or more locations in the same locality. For example, \"21 Henr St, Bristol, UK\" will return a partial match for both Henry Street and Henrietta Street. Note that if a request includes a misspelled address component, the geocoding service may suggest an alternative address. Suggestions triggered in this way will also be marked as a partial match. . [optional]  # noqa: E501
            place_id (str): A unique identifier that can be used with other Google APIs. See the [Place ID overview](https://developers.google.com/maps/documentation/places/web-service/place-id).. [optional]  # noqa: E501
            types ([str]): Indicates the address type of the geocoding result used for calculating directions.  * `administrative_area_level_1` indicates a first-order civil entity below the country level. Within the United States, these administrative levels are states. Not all nations exhibit these administrative levels. In most cases, administrative_area_level_1 short names will closely match ISO 3166-2 subdivisions and other widely circulated lists; however this is not guaranteed as our geocoding results are based on a variety of signals and location data. * `administrative_area_level_2` indicates a second-order civil entity below the country level. Within the United States, these administrative levels are counties. Not all nations exhibit these administrative levels. * `administrative_area_level_3` indicates a third-order civil entity below the country level. This type indicates a minor civil division. Not all nations exhibit these administrative levels. * `administrative_area_level_4` indicates a fourth-order civil entity below the country level. This type indicates a minor civil division. Not all nations exhibit these administrative levels. * `administrative_area_level_5` indicates a fifth-order civil entity below the country level. This type indicates a minor civil division. Not all nations exhibit these administrative levels. * `airport` indicates an airport. * `colloquial_area` indicates a commonly-used alternative name for the entity. * `country` indicates the national political entity, and is typically the highest order type returned by the Geocoder. * `intersection` indicates a major intersection, usually of two major roads. * `locality` indicates an incorporated city or town political entity. * `natural_feature` indicates a prominent natural feature. * `neighborhood` indicates a named neighborhood * `park` indicates a named park. * `plus_code` indicates an encoded location reference, derived from latitude and longitude. Plus codes can be used as a replacement for street addresses in places where they do not exist (where buildings are not numbered or streets are not named). See [https://plus.codes](https://plus.codes/) for details. * `point_of_interest` indicates a named point of interest. Typically, these \"POI\"s are prominent local entities that don't easily fit in another category, such as \"Empire State Building\" or \"Eiffel Tower\". * `political` indicates a political entity. Usually, this type indicates a polygon of some civil administration. * `postal_code` indicates a postal code as used to address postal mail within the country. * `premise` indicates a named location, usually a building or collection of buildings with a common name * `route` indicates a named route (such as \"US 101\"). * `street_address` indicates a precise street address. * `sublocality` indicates a first-order civil entity below a locality. For some locations may receive one of the additional types: sublocality_level_1 to sublocality_level_5. Each sublocality level is a civil entity. Larger numbers indicate a smaller geographic area. * `subpremise` indicates a first-order entity below a named location, usually a singular building within a collection of buildings with a common name * `transit_station` indicates a transit station.  An empty list of types indicates there are no known types for the particular address component, for example, Lieu-dit in France. . [optional]  # noqa: E501
        """

        _check_type = kwargs.pop('_check_type', True)
        _spec_property_naming = kwargs.pop('_spec_property_naming', False)
        _path_to_item = kwargs.pop('_path_to_item', ())
        _configuration = kwargs.pop('_configuration', None)
        _visited_composed_classes = kwargs.pop('_visited_composed_classes', ())

        if args:
            raise ApiTypeError(
                "Invalid positional arguments=%s passed to %s. Remove those invalid positional arguments." % (
                    args,
                    self.__class__.__name__,
                ),
                path_to_item=_path_to_item,
                valid_classes=(self.__class__,),
            )

        self._data_store = {}
        self._check_type = _check_type
        self._spec_property_naming = _spec_property_naming
        self._path_to_item = _path_to_item
        self._configuration = _configuration
        self._visited_composed_classes = _visited_composed_classes + (self.__class__,)

        for var_name, var_value in kwargs.items():
            if var_name not in self.attribute_map and \
                        self._configuration is not None and \
                        self._configuration.discard_unknown_keys and \
                        self.additional_properties_type is None:
                # discard variable.
                continue
            setattr(self, var_name, var_value)
            if var_name in self.read_only_vars:
                raise ApiAttributeError(f"`{var_name}` is a read-only attribute. Use `from_openapi_data` to instantiate "
                                     f"class with read only attributes.")
