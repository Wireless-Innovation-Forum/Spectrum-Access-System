# PlacePhoto

A photo of a Place. The photo can be accesed via the [Place Photo](https://developers.google.com/places/web-service/photos) API using an url in the following pattern:  ``` https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference=photo_reference&key=YOUR_API_KEY ```  See [Place Photos](https://developers.google.com/places/web-service/photos) for more information. 

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**height** | **float** | The height of the photo. | 
**width** | **float** | The width of the photo. | 
**html_attributions** | **[str]** | The HTML attributions for the photo. | 
**photo_reference** | **str** | A string used to identify the photo when you perform a Photo request. | 
**any string name** | **bool, date, datetime, dict, float, int, list, str, none_type** | any string name can be used but the value must be the correct type | [optional]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


