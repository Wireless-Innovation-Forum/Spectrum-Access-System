# import json
# import os
# from pathlib import Path
# from statistics import mean
#
# from geopy import Point
# from geopy.distance import geodesic
#
# SCRIPT_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
# DATA_FILENAME = 'path_elevation_data.json'
# DATA_FILEPATH = Path(SCRIPT_DIRECTORY, DATA_FILENAME)
#
#
# def get_expected_terrain_model():
#     """
#     Data retrieved from Google's Elevation API
#     """
#     json_response = json.load(DATA_FILEPATH)
#     results = json_response['results']
#     elevation_points = [item['elevation'] for item in results]
#     number_of_elevation_points = len(elevation_points)
#
#     step_sizes = []
#     for index, item in enumerate(results[1:]):
#         current_location = item['location']
#         previous_location = results[index]
#         current_coordinates = Point(latitude=current_location['lat'], longitude=current_location['lng'])
#         previous_coordinates = Point(latitude=previous_location['lat'], longitude=previous_location['lng'])
#
#         distance = geodesic(current_coordinates, previous_coordinates).meters
#         step_sizes.append(distance)
#
#     step_size_in_meters = mean(step_sizes)
#
#     return [number_of_elevation_points - 1, step_size_in_meters] + elevation_points
