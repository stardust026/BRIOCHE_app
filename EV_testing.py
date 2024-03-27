import requests
import pandas as pd
# import osmnx as ox
# import networkx as nx
# import numpy as np
from globalDefinition import (API_KEY)
from SOC import (
    getStateOfCharge
)
from Elevation import elevation_difference
from geopy.distance import geodesic
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import math
import sys
# import os

def getTripCoordinate(origin, destination,profile='mapbox/driving-traffic'):
    # origin = [-123.11571438985469,49.28079175525552]
    # destination = [-119.49666492648971,49.88929762638151]
    coordinates = ";".join([f"{lon},{lat}" for lon, lat in [origin, destination]])
    url = f'https://api.mapbox.com/directions/v5/{profile}/{coordinates}?&steps=true&geometries=geojson&waypoints_per_route=true&overview=simplified&access_token={API_KEY}'
    # params = {"annotation":"speed"} 
    response = requests.get(url)
    
    if response.status_code == 200:
        if response.json()['code'] != "Ok":
            return False
        data = response.json()

        coordinate = data['routes'][0]['geometry']['coordinates']
        coordinate.insert(0,origin)
        coordinate.append(destination)
       
        #print(data['waypoints'])
        #print(data['routes'])
        return coordinate
        
    else:
        print("response failed (Get Distance), status code:", response.status_code)
        return False

def getTripDistance(tripCoordinate,profile='mapbox/driving-traffic',):
    data = tripCoordinate
    max_request_size = 20
    sublists = [data[i:i+max_request_size] for i in range(0, len(data), max_request_size)]
    for i in range(len(sublists) - 1):
        sublists[i + 1] = [sublists[i][-1]] + sublists[i + 1]
        
    duration_distance_pairs = []
    elevation_pairs = []

    swapped_coordinates = [(coord[1], coord[0]) for coord in data]
    elevation_pairs= elevation_difference(swapped_coordinates)
    
    for sublist in sublists:
        coordinates_str = '; '.join([f'{item[0]}, {item[1]}' for item in sublist])

        url = f'https://api.mapbox.com/directions/v5/{profile}/{coordinates_str}?&access_token={API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            leg_data = data['routes'][0]['legs']
            for leg in leg_data:
                duration_distance_pairs.append((leg['duration'], leg['distance']))
        else:
            print("Response failed (Get Distance), status code:", response.status_code)
            return None
    

    combined_list = []
    if elevation_pairs is None:
        elevation_pairs = [0] * len(duration_distance_pairs)
    for (duration, distance), elevation in zip(duration_distance_pairs, elevation_pairs):
        combined_list.append((duration, distance, elevation))
    # Return the aggregated result
    return combined_list
    

def getChargePair(tripdistance, current_battery_level):
    data_pair = tripdistance
    total_duration = 0
    total_distance = 0
    charge_list = [(current_battery_level,total_duration,total_distance)]
    privous_charge = current_battery_level
    previous_speed = 0
    for data in data_pair:
        duration = data[0]
        if duration is None:
            duration = 0.0
        total_duration +=duration
        distance = data[1]
        total_distance +=distance
        elevation = data[2]
        if duration == 0 or distance ==0:
            charge_list.append((privous_charge,total_duration,total_distance))
        else:
            road_grade=math.degrees(math.atan(elevation/distance))
            # road_grade = 0
            velocity = distance/duration
            # max_acceleration = (100*1000/3600-0)/4.4
            max_acceleration = 3
            if velocity>previous_speed:
                if (velocity-previous_speed)>10*1000/3600:
                    acceleration = max_acceleration
                else:
                    acceleration = (max_acceleration/10)*(velocity-previous_speed)
                acceleration_time = (velocity-previous_speed)/acceleration
                charge = min(100,privous_charge-(getStateOfCharge(acceleration,velocity,road_grade)*acceleration_time + getStateOfCharge(0,velocity,road_grade)*(duration-acceleration_time))*100)
            elif previous_speed>velocity:
                deceleration = -(0.005*math.pow(previous_speed,2)+0.154*previous_speed+0.493)
                #print('deceleration:',deceleration)
                deceleration_time = (velocity-previous_speed)/deceleration
                charge = min(100,privous_charge-(getStateOfCharge(deceleration,velocity,road_grade)*deceleration_time + getStateOfCharge(0,velocity,road_grade)*(duration-deceleration_time))*100)
            else:
                acceleration = 0
                charge = min(100,privous_charge-(getStateOfCharge(0,velocity,road_grade)*duration)*100)
            charge_list.append((charge,total_duration,total_distance))
            privous_charge = charge
            previous_speed =velocity
    print("total_duration: ", total_duration, "total_distance:", total_distance)
    return charge_list

def get_destination_coordinates(start_latitude, start_longitude, distance, battery_level):
    
    combined_list = []
    for i in range(0, 360, 30):
        for k in range(distance, 50, -75):
            dest_point = geodesic(kilometers=k).destination((start_latitude, start_longitude), i)
            dest_latitude = dest_point.latitude
            dest_longitude = dest_point.longitude
            coordinates = getTripCoordinate([start_longitude,start_latitude],[dest_longitude, dest_latitude])
            if coordinates != False:
                break
        if coordinates == False:
            continue
        tripdistance =  getTripDistance(coordinates)
        charge = getChargePair(tripdistance, battery_level)
        combined_list.extend([coord[0], coord[1], float(charge[0]),float(charge[1]),float(charge[2])] for coord, charge in zip(coordinates, charge))
    return combined_list

def generate_waypoints(start_latitude,start_longitude, battery):
    distance = 500
    current_battery_level = battery
    combined_list = get_destination_coordinates(start_latitude, start_longitude, distance,current_battery_level)
    # combined_list =[]
    # for i in range(len(destination)):
    #     coordinates = getTripCoordinate([start_longitude,start_latitude],destination[i])
    #     if coordinates == False:
    #       continue 
    #     tripdistance =  getTripDistance(coordinates)
    #     charge = getChargePair(tripdistance, current_battery_level)
    #     combined_list.extend([coord[0], coord[1], float(charge[0]),float(charge[1]),float(charge[2])] for coord, charge in zip(coordinates, charge))

    # create columns
    columns = ['Longitude', 'Latitude', 'Battery_Level', 'Total Duration', 'Total Distance']

    # create a data frame
    df = pd.DataFrame(combined_list, columns=columns)
    return df

