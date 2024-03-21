import requests
import pandas as pd
import osmnx as ox
import networkx as nx
import numpy as np
from globalDefinition import (API_KEY,BATTERY_CAPACITY,MASS,LENGTH,WIDTH,HEIGHT,MAXSPEED)
from SOC import (
    getStateOfCharge
)
from Elevation import elevation_difference
from geopy.distance import geodesic
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import math
import sys
import os
import random


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
        print("response failed, status code:", response.status_code)
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
            print("Response failed, status code:", response.status_code)
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
    privous_charge = current_battery_level
    previous_speed = 0
    last_charge_loss = 0  
    for data in data_pair:
        duration = data[0]
        total_duration += duration
        distance = data[1]
        total_distance += distance
        elevation = data[2]
        if duration == 0 or distance == 0:
            pass
        else:
            road_grade = math.degrees(math.atan(elevation / distance))
            velocity = distance / duration

            if velocity > previous_speed:
                acceleration = 2.38 * math.exp(-0.1 * previous_speed)
                acceleration_time = (velocity - previous_speed) / acceleration
                charge = min(100, privous_charge - (getStateOfCharge(acceleration, velocity, road_grade) * acceleration_time + getStateOfCharge(0, velocity, road_grade) * (duration - acceleration_time)) * 100)
            elif previous_speed > velocity:
                deceleration = 0.005*math.pow(previous_speed,2)+0.15*previous_speed+0.5
                deceleration_time = (velocity - previous_speed) / deceleration
                charge = min(100, privous_charge - (getStateOfCharge(deceleration, velocity, road_grade) * deceleration_time + getStateOfCharge(0, velocity, road_grade) * (duration - deceleration_time)) * 100)
            else:
                acceleration = 0
                charge = min(100, privous_charge - (getStateOfCharge(0, velocity, road_grade) * duration) * 100)
            privous_charge = charge
            previous_speed = velocity
            last_charge_loss = current_battery_level - charge  # 更新最后一段行程的电量损耗
    return last_charge_loss

def calculateEnergyConsumption(start_latitude, start_longitude, end_point, current_battery_level=100):
    trip_coordinate = getTripCoordinate([start_longitude, start_latitude], end_point)
    battery_loss = 0  # 设置一个默认值
    if trip_coordinate:
        trip_distance = getTripDistance(trip_coordinate)
        if trip_distance:
            charge_loss = getChargePair(trip_distance, current_battery_level)
            battery_loss = current_battery_level - charge_loss  # 直接赋值给 battery_loss
    return battery_loss

def generate_random_coordinates(num_points):
    coordinates = []
    for _ in range(num_points):
        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)
        coordinates.append((latitude, longitude))
    return coordinates

def calculate_average_error_rate(api_key, start_latitude, start_longitude, energy_budget, report, route_type, traffic, travel_mode, vehicle_commercial, vehicle_engine_type, vehicleWeight, vehicleLength, vehicleWidth, vehicleHeight, vehicleMaxSpeed, constant_speed_consumption, auxiliaryPowerInkW, current_battery_level=75):
    url = f'https://api.tomtom.com/routing/1/calculateReachableRange/{start_latitude},{start_longitude}/json?key={api_key}&energyBudgetInkWh={energy_budget}&report={report}&routeType={route_type}&traffic={traffic}&travelMode={travel_mode}&vehicleCommercial={vehicle_commercial}&vehicleEngineType={vehicle_engine_type}&vehicleWeight={vehicleWeight}&vehicleLength={vehicleLength}&vehicleWidth={vehicleWidth}&vehicleHeight={vehicleHeight}&vehicleMaxSpeed={vehicleMaxSpeed}&constantSpeedConsumptionInkWhPerHundredkm={constant_speed_consumption}&auxiliaryPowerInkW={auxiliaryPowerInkW}'

    response = requests.get(url)
    print("response = ",response)
    boundary_points = response.json()['reachableRange']['boundary']
    coordinates = [(point['longitude'], point['latitude']) for point in boundary_points]

    current_battery_level = 100  # 当前电量
    total_error_rate = 0
    num_end_points = len(coordinates)

    for end_point in coordinates:
        actual_battery_loss = calculateEnergyConsumption(start_latitude, start_longitude, end_point)
        error_rate = (actual_battery_loss / current_battery_level) * 100
        total_error_rate += error_rate

    average_error_rate = total_error_rate / num_end_points

    return average_error_rate


if __name__ == "__main__":
    api_key = 'r4PwmREcA5rPk7PR9DBYFPQ6sKiQ4ZyE'

    # start_latitude =   23.831757    #纬度
    # start_longitude =   107.576099 #经度
    start_coordinates = [26.022068, 113.474056]  # [latitude, longitude]
    energy_budget = BATTERY_CAPACITY/1000
    report = 'effectiveSettings'
    route_type = 'eco'
    traffic = 'true'
    avoid = 'unpavedRoads'
    travel_mode = 'car'
    vehicleWeight = MASS
    vehicleLength = LENGTH
    vehicleWidth = WIDTH
    vehicleHeight = HEIGHT
    vehicleMaxSpeed = MAXSPEED
    vehicle_commercial = 'false'
    vehicle_engine_type = 'electric'
    constant_speed_consumption = '45,10.7:110,16.3'
    auxiliaryPowerInkW = 0

    average_error_rate = calculate_average_error_rate(api_key, start_coordinates[0], start_coordinates[1], energy_budget, report, route_type, traffic, travel_mode, vehicle_commercial, vehicle_engine_type, vehicleWeight, vehicleLength, vehicleWidth, vehicleHeight, vehicleMaxSpeed, constant_speed_consumption, auxiliaryPowerInkW)
    print(start_coordinates[0],",",start_coordinates[1],",Average Error Rate:", average_error_rate)