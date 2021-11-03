# DirectionsRoute

Routes consist of nested `legs` and `steps`.

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**legs** | [**[DirectionsLeg]**](DirectionsLeg.md) | An array which contains information about a leg of the route, between two locations within the given route. A separate leg will be present for each waypoint or destination specified. (A route with no waypoints will contain exactly one leg within the legs array.) Each leg consists of a series of steps. | 
**bounds** | [**Bounds**](Bounds.md) |  | 
**copyrights** | **str** | Contains an array of warnings to be displayed when showing these directions. You must handle and display these warnings yourself. | 
**summary** | **str** | Contains a short textual description for the route, suitable for naming and disambiguating the route from alternatives. | 
**waypoint_order** | **[int]** | An array indicating the order of any waypoints in the calculated route. This waypoints may be reordered if the request was passed optimize:true within its waypoints parameter. | 
**warnings** | **[str]** | Contains an array of warnings to be displayed when showing these directions. You must handle and display these warnings yourself. | 
**overview_polyline** | [**DirectionsPolyline**](DirectionsPolyline.md) |  | 
**fare** | [**Fare**](Fare.md) |  | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


