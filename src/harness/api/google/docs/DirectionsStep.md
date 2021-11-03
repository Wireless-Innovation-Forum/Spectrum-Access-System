# DirectionsStep

Each element in the steps array defines a single step of the calculated directions. A step is the most atomic unit of a direction's route, containing a single step describing a specific, single instruction on the journey. E.g. \"Turn left at W. 4th St.\" The step not only describes the instruction but also contains distance and duration information relating to how this step relates to the following step. For example, a step denoted as \"Merge onto I-80 West\" may contain a duration of \"37 miles\" and \"40 minutes,\" indicating that the next step is 37 miles/40 minutes from this step.  When using the Directions API to search for transit directions, the steps array will include additional transit details in the form of a transit_details array. If the directions include multiple modes of transportation, detailed directions will be provided for walking or driving steps in an inner steps array. For example, a walking step will include directions from the start and end locations: \"Walk to Innes Ave & Fitch St\". That step will include detailed walking directions for that route in the inner steps array, such as: \"Head north-west\", \"Turn left onto Arelious Walker\", and \"Turn left onto Innes Ave\". 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**duration** | [**TextValueObject**](TextValueObject.md) |  | 
**end_location** | [**LatLngLiteral**](LatLngLiteral.md) |  | 
**html_instructions** | **str** | Contains formatted instructions for this step, presented as an HTML text string. This content is meant to be read as-is. Do not programmatically parse this display-only content. | 
**polyline** | [**DirectionsPolyline**](DirectionsPolyline.md) |  | 
**start_location** | [**LatLngLiteral**](LatLngLiteral.md) |  | 
**travel_mode** | [**TravelMode**](TravelMode.md) |  | 
**distance** | [**TextValueObject**](TextValueObject.md) |  | [optional] 
**maneuver** | **str** | Contains the action to take for the current step (turn left, merge, straight, etc.). Values are subject to change, and new values may be introduced without prior notice. | [optional] 
**transit_details** | [**DirectionsTransitDetails**](DirectionsTransitDetails.md) |  | [optional] 
**steps** | **bool, date, datetime, dict, float, int, list, str, none_type** | Contains detailed directions for walking or driving steps in transit directions. Substeps are only available when travel_mode is set to \&quot;transit\&quot;. The inner steps array is of the same type as steps. | [optional] 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


