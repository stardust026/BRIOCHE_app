# Imports

import folium
import pandas as pd
import numpy as np
import requests
import alphashape
from jinja2 import Template
import time
from scipy.interpolate import griddata
from EV_testing import generate_waypoints
from flask import Flask, jsonify


# Function to get charging stations within a specified radius of a given location.
def get_public_charging_stations(latitude, longitude, radius=400000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
        [out:json];
        node["amenity"="charging_station"](around:{radius},{latitude},{longitude});
        out;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()
    charging_stations = []
    for element in data['elements']:
        if 'tags' in element:
            name = element['tags'].get('name', 'Unnamed Charging Station')
            lat = element['lat']
            lon = element['lon']
            charging_stations.append({'name': name, 'lat': lat, 'lon': lon})
    return charging_stations



# Function to draw points in the map
def draw_points(map_object, list_of_points, layer_name, battery_levels):

    fg = folium.FeatureGroup(name=layer_name)
    for point, battery in zip(list_of_points,battery_levels):
        if battery > 70:
            color = 'green'
        elif battery > 35:
            color = 'yellow'
        elif battery > 0:
            color = 'red'
        else:
            color = 'grey'
        fg.add_child(
            folium.CircleMarker(
                location=point,
                radius=1,
                color=color,
                fill_color=color,
                tooltip=battery
            )
        )
    map_object.add_child(fg)

def draw_charging_stations(map_object, charging_stations):
    fg = folium.FeatureGroup(name="Charging Stations")
    for station in charging_stations:
        marker = folium.Marker(
                location=[station['lat'], station['lon']],
                # popup=station['name'],
                icon=folium.Icon(color='green',icon="charging-station",prefix="fa")
            )

        marker.add_child(folium.Popup(f"Latitude: {station['lat']}, Longitude: {station['lon']}"))
        

        fg.add_child(
            marker
        )
        
    map_object.add_child(fg)

def draw_alphashape(map_object, list_of_points, text, color, alpha = 0):
    alpha_shape = alphashape.alphashape(list_of_points, alpha)
    fg = folium.FeatureGroup(name=text)
    fg.add_child(
        folium.vector_layers.Polygon(
            locations=[(i[0], i[1]) for i in alpha_shape.exterior.coords],
            color=color,
            fill_color=color,
            weight=1
        )
    )
    map_object.add_child(fg)

def draw_starting_point(map_object, coordinate):
    marker = folium.Marker(
            location=coordinate,
            icon=folium.Icon(color='blue',icon="car",prefix="fa"))
    map_object.add_child(marker)
        


# Config
# Vancouver coordinates: 49.246292, -123.116226
# Calgary coordinates: 51.0276233, -114.087835
def return_alpha_shape(start_latitude,start_longitude, battery=100):
    # center_coordinate = [start_latitude, start_longitude]
    df = generate_waypoints(start_latitude,start_longitude, battery)
    alpha = 0.5

    # csv_name = 'EV_data.csv'
    # df = pd.read_csv(csv_name, dtype={'Battery_Level': float})

    battery_levels = df['Battery_Level'].values.tolist()

    all_points = df[['Latitude', 'Longitude']].values.tolist()
    grid_data = df[['Longitude', 'Latitude']].values.tolist()
    
    lat = float(start_latitude)
    lon = float(start_longitude)

    grid_x, grid_y = np.mgrid[lon-8:lon+8:50j, lat-5:lat+5:50j]

    # interpolate the data
    grid_z0 = griddata(grid_data, battery_levels, (grid_x, grid_y), method='linear')

    interpolation_points = []
    # create the list of interpolated data
    for i in range(50):
        for j in range(50):
            interpolation_points.append([grid_y[i, j], grid_x[i, j], grid_z0[i, j]])

    green_points = df[df['Battery_Level'] > 70.0]
    green_points = green_points[['Latitude', 'Longitude']].values.tolist()
    
    yellow_points = df[(df['Battery_Level'] > 35.0)]
    yellow_points = yellow_points[['Latitude', 'Longitude']].values.tolist()

    red_points = df[(df['Battery_Level'] > 0)]
    red_points = red_points[['Latitude', 'Longitude']].values.tolist()

    # insert the interpolated points into the list of other points
    for item in interpolation_points:
        all_points.append([item[0], item[1]])
        battery_levels.append(item[2])
        if item[2] > 0:
            red_points.append([item[0], item[1]])
        if item[2] > 35:
            yellow_points.append([item[0], item[1]])
        if item[2] > 70:
            green_points.append([item[0], item[1]])

    list = []
    if len(green_points) >= 3:
        green = alphashape.alphashape(green_points, alpha)
        list.append([(i[0], i[1]) for i in green.exterior.coords])
    else:
        list.append([])
        
    if len(yellow_points) >= 3:
        yellow = alphashape.alphashape(yellow_points, alpha)
        list.append([(i[0], i[1]) for i in yellow.exterior.coords])
    else:
        list.append([])
    if len(red_points) >= 3:
        red = alphashape.alphashape(red_points, alpha)
        list.append([(i[0], i[1]) for i in red.exterior.coords])
    else:
        list.append([])
        
    return list