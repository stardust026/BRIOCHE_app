// set starting point coordinate
var start = [51.0276233, -114.087835];
var click_lat
var click_lon
var remaining_battery
const BATTERY_CAPACITY = 75000
const MASS = 2139
const GRAVITY = 9.8066
const CI = 1.75 
const CR = 1.15
const C1 = 0.0328
const C2 = 4.575
const CD = 0.23
const AF = 2.22
const PA = 1.2256
const ED = 0.93
const EM = 0.92
const EB = 0.9
 

// create a map in the "map" div, set the view to a given place and zoom
var map = L.map('map').setView(start, 7);

var carIcon = L.icon({
    iconUrl: 'electric-car.png',
    iconSize:     [38, 38], // size of the icon
    iconAnchor:   [22, 22], // point of the icon which will correspond to marker's location
    popupAnchor:  [-3, -76] // point from which the popup should open relative to the iconAnchor
});

var waypoints = L.icon({
    iconUrl: 'waypoints.png',
    iconSize:     [25, 25], // size of the icon
    iconAnchor:   [22, 22], // point of the icon which will correspond to marker's location
    popupAnchor:  [-3, -76] // point from which the popup should open relative to the iconAnchor
});

var chunk_size = 5

// add an OpenStreetMap tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);


const setVisible = (elementOrSelector, visible) => 
(typeof elementOrSelector === 'string'
? document.querySelector(elementOrSelector)
: elementOrSelector
).style.display = visible ? 'block' : 'none';

function getColor(d) {
    var value = parseFloat(d.replace('>', '').replace('%', ''));
    return value === 70 ? "darkgreen" :
        value === 35 ? "yellow" :
        value === 0 ? "red" : "black";
    }
var legend = L.control({position: 'bottomright'});
legend.onAdd = function (map) {

    var div = L.DomUtil.create('div', 'info legend');
    circleHTML = '<div style="width: 90%;"><div style="font-size: 18px;"><strong>Battery Level</strong></div><div style="width: 100%; display: flex; align-items: center;"><img src="green.png" style="width: 20px; height: 20px; margin-right: 10px;margin-bottom: 5px;margin-top: 5px" /><span style="font-size: 16px;">>=70%</span></div><div style="width: 100%; display: flex; align-items: center;"><img src="yellow.png" style="width: 20px; height: 20px; margin-right: 10px;margin-bottom: 5px;margin-top: 5px" /><span style="font-size: 16px;">35%-<70%</span></div><div style="width: 100%; display: flex; align-items: center;"><img src="red.png" style="width: 20px; height: 20px; margin-right: 10px;margin-bottom: 5px;margin-top: 5px" /><span style="font-size: 16px;">0%-<35%</span></div></div>'

    div.innerHTML = circleHTML;
    return div;
};

legend.addTo(map);

var legendContainer = legend.getContainer();
legendContainer.style.width = '100%';
legendContainer.style.height = '100px';
legendContainer.style.marginBottom = '20px';
legendContainer.style.marginLeft = '15px';


const batteryForm = document.getElementById('batteryForm');

document.getElementById('batteryInputForm').addEventListener('submit', async function(event) {
    event.preventDefault(); 
    var batteryLevel = document.getElementById('batteryLevel').value;
    if (batteryLevel < remaining_battery) {
        alert("Your input charge level is lower than current level");
        return; // Stop further execution
    }
    remaining_battery = batteryLevel
    setVisible('#loading', true);
    getalphashape(click_lat, click_lon, remaining_battery);
    map.setView([click_lat,click_lon], 7);
    batteryForm.style.display = 'none';
    //remove the label 
    const oldLabel = document.querySelector('form#batteryInputForm label[for="currentBatteryLevel"]');
    if (oldLabel) {
        oldLabel.parentNode.removeChild(oldLabel);
    }
});

async function createPath(){
    setVisible('#loading', true);
    refresh_shapeAndLine();
    removeMarkerAtCoordinates(start[0],start[1]);
    show_marker(start[0],start[1],waypoints);
    show_marker(click_lat,click_lon,carIcon);
    const coordinates_tmp = await getTripCoordinate(click_lat, click_lon);
    var coordinates = swaplatlng(coordinates_tmp)
    coordinates = splitCoordinate(coordinates,chunk_size)
    var chargelist = []
    // console.log(coordinates)
    if (coordinates) {
        // console.log("Coordinates:", coordinates);
        var color = ['#0000FF','#4682B4','#87CEFA','#B0E0E6','#4682B4']
        var previous_charge = remaining_battery
        for (var i = 0;i<coordinates.length;i++){
            coordinates_array = convertToPairs(coordinates[i])
            var coordinates_array_swapped = swaplatlng(coordinates_array)
            var tripdistance =  await getTripDistance(coordinates_array_swapped)
            if (tripdistance){
                var new_charge = getChargePair(tripdistance,previous_charge)
                chargelist.push(new_charge)
                previous_charge = new_charge
            }
            var polyline = new L.polyline(coordinates_array, {color: color[i]
            ,weight: 5,smoothFactor: 1}).addTo(map); 
        }
    } else {
        console.log("Failed to fetch trip coordinates.");
    }
    start = [click_lat,click_lon]
    setVisible('#loading', false);
    return chargelist[chargelist.length-1]
}

function getPowerMotor(acceleration, velocity, road_grade) {
    const road_grade_radian = (road_grade / 180) * Math.PI;
    let power_of_wheel = 0;
    let power_of_motor = 0;
    const gradient_resistance_force = MASS * GRAVITY * Math.sin(road_grade_radian);
    const rolling_resistance_force = MASS * GRAVITY * Math.cos(road_grade_radian) * CR * (C1 * velocity + C2) / 1000;
    const aerodynamic_drag_force = 0.5 * (PA * AF * CD * Math.pow(velocity, 2));
    const inertia_resistance_force = CI * MASS * acceleration;
    power_of_wheel = (gradient_resistance_force + rolling_resistance_force + aerodynamic_drag_force + inertia_resistance_force) * velocity;
    power_of_motor = power_of_wheel / (ED * EM * EB);
    return power_of_motor;
}

function getStateOfCharge(acceleration, velocity, road_grade) {
    const power = getPowerMotor(acceleration, velocity, road_grade);
    let total_power = 0;
    if (acceleration < 0 && power < 0) {
        const ER = 1 / Math.exp(0.0411 / Math.abs(acceleration));
        total_power = ER * power;
    } else if (power < 0) {
        const ER = 0.7;
        total_power = ER * power;
    } else {
        total_power = power;
    }
    return total_power / (3600 * BATTERY_CAPACITY);
}

async function getElevation(coordinateList) {
    const coordinate = coordinateList.map(coord => coord.join(',')).join('|');
    const url = `https://api.open-elevation.com/api/v1/lookup?locations=${coordinate}`;
    const response = await fetch(url);

    if (response.ok) {
        const data = await response.json();
        return data.results;
    } else {
        console.log("Response failed, status code:", response.status);
        return null;
    }
}

async function elevationDifference(coordinateList) {
    const data = await getElevation(coordinateList);
    if (data !== null) {
        const elevationList = data.map(item => item.elevation || 0);
        const elevationPairs = elevationList.slice(1).map((elevation, index) => elevation - elevationList[index]);
        return elevationPairs;
    }
    return null;
}


function swaplatlng(coordinate){
    const swappedCoordinates = [];
        for (let i = 0; i < coordinate.length; i++) {
            const coord = coordinate[i];
            subarray = [coord[1], coord[0]];
            swappedCoordinates.push(subarray);
    }
    return swappedCoordinates;
}
 
async function getTripCoordinate(lat, lon) {
    const origin = [start[1],start[0]]
    const profile='mapbox/driving-traffic'
    const destination = [lon.toString(),lat.toString()]
    const originStr = origin[0] + ',' + origin[1];
    const destinationStr = destination[0] + ',' + destination[1];
    const coordinates = originStr + ';' + destinationStr;
    console.log("coordinates:", coordinates);
    return fetch(`https://api.mapbox.com/directions/v5/${profile}/${coordinates}?&steps=true&geometries=geojson&waypoints_per_route=true&overview=full&access_token=pk.eyJ1IjoiYm9yaXN3YWlraW4iLCJhIjoiY2xzY3hycng3MDVlZTJ2cTc1YjZiamZmcyJ9.-UEBrr6yXlE9K8O1voTUkg`)
        .then(response => {
            if (!response.ok) {
                console.error('Response failed, status code:', response.status);
                return false;
            }
            return response.json();
        })
        .then(data => {
            if (data.code !== 'Ok') {
                console.error('Error in API response:', data.message);
                return false;
            }
            const coordinate = data.routes[0].geometry.coordinates;
            coordinate.unshift(origin);
            coordinate.push(destination);
            return coordinate;
        })
        .catch(error => {
            console.error('Error:', error);
            return false;
        });
}

async function getTripDistance(tripCoordinate, profile = 'mapbox/driving-traffic') {
    let data = tripCoordinate;
    const max_request_size = 20;
    const sublists = [];
    for (let i = 0; i < data.length; i += max_request_size) {
        sublists.push(data.slice(i, i + max_request_size));
    }
    for (let i = 0; i < sublists.length - 1; i++) {
        sublists[i + 1] = [sublists[i][sublists[i].length - 1]].concat(sublists[i + 1]);
    }

    let duration_distance_pairs = [];
    let elevation_pairs = [];

    const swapped_coordinates = data.map(coord => [coord[1], coord[0]]);
    elevation_pairs = await elevationDifference(swapped_coordinates);

    for (const sublist of sublists) {
        const coordinates_str = sublist.map(item => `${item[0]}, ${item[1]}`).join('; ');

        const url = `https://api.mapbox.com/directions/v5/${profile}/${coordinates_str}?&access_token=pk.eyJ1IjoiYm9yaXN3YWlraW4iLCJhIjoiY2xzY3hycng3MDVlZTJ2cTc1YjZiamZmcyJ9.-UEBrr6yXlE9K8O1voTUkg`;
        const response = await fetch(url);
        if (response.ok) {
            const responseData = await response.json();
            const legData = responseData.routes[0].legs;
            for (const leg of legData) {
                duration_distance_pairs.push([leg.duration, leg.distance]);
            }
        } else {
            console.log("Response failed (Get Distance), status code:", response.status);
            return null;
        }
    }

    const combinedList = [];
    if (elevation_pairs === null) {
        elevation_pairs = Array(duration_distance_pairs.length).fill(0);
    }
    for (let i = 0; i < duration_distance_pairs.length; i++) {
        const [duration, distance] = duration_distance_pairs[i];
        const elevation = elevation_pairs[i];
        combinedList.push([duration, distance, elevation]);
    }
    return combinedList;
}

function getChargePair(tripdistance, current_battery_level) {
    let data_pair = tripdistance;
    let total_duration = 0;
    let total_distance = 0;
    let previous_charge = current_battery_level;
    let previous_speed = 0;

    for (const data of data_pair) {
        let duration = data[0];
        if (duration === null) {
            duration = 0.0;
        }
        total_duration += duration;
        let distance = data[1];
        total_distance += distance;
        let elevation = data[2];

        if (duration === 0 || distance === 0) {
            continue;
        } else {
            let road_grade = Math.atan2(elevation, distance) * (180 / Math.PI);
            let velocity = distance / duration;
            let max_acceleration = 3;

            if (velocity > previous_speed) {
                let acceleration;
                if ((velocity - previous_speed) > (10 * 1000 / 3600)) {
                    acceleration = max_acceleration;
                } else {
                    acceleration = (max_acceleration / 10) * (velocity - previous_speed);
                }
                let acceleration_time = (velocity - previous_speed) / acceleration;
                let charge = Math.min(100, previous_charge - (getStateOfCharge(acceleration, velocity, road_grade) * acceleration_time + getStateOfCharge(0, velocity, road_grade) * (duration - acceleration_time)) * 100);
                previous_charge = charge;
            } else if (previous_speed > velocity) {
                let deceleration = -(0.005 * Math.pow(previous_speed, 2) + 0.154 * previous_speed + 0.493);
                let deceleration_time = (velocity - previous_speed) / deceleration;
                let charge = Math.min(100, previous_charge - (getStateOfCharge(deceleration, velocity, road_grade) * deceleration_time + getStateOfCharge(0, velocity, road_grade) * (duration - deceleration_time)) * 100);
                previous_charge = charge;
            } else {
                let charge = Math.min(100, previous_charge - (getStateOfCharge(0, velocity, road_grade) * duration) * 100);
                previous_charge = charge;
            }
            previous_speed = velocity;
        }
    }
    return previous_charge;
}

function getalphashape(lat, lon, battery=100){
    fetch(`http://127.0.0.1:5000/alpha?lat=${lat}&lon=${lon}&battery=${battery}`)
    .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();})
    .then(
        
        data => {
        console.log("data:",data);
        var colorlist = ['darkgreen', 'yellow', 'red']
        var count = 0
        data.forEach(element => {
            // Check if the element is an empty list
            if (element.length > 0) {
                var polygon = L.polygon(element,{
                    color: colorlist[count],
                    fillColor: colorlist[count],
                    weight: 3
                }).addTo(map);
            }
            count++;
        });
    }).then(() => {
        setVisible('#loading', false);
    })
}


function splitCoordinate(coordinates) {
    var result = [];
    var chunkSize = Math.ceil(coordinates.length / 5);

    for (var i = 0; i < 5; i++) {
        var start = i * chunkSize;
        var end = (i + 1) * chunkSize;
        if (i > 0) {
            start -= 2;
        }
        var subarray = coordinates.slice(start, end).flat();
        result.push(subarray);
    }

    return result;
}

function convertToPairs(array) {
    var result = [];
    for (var i = 0; i < array.length; i += 2) {
        result.push([array[i], array[i + 1]]);
    }
    return result;
}



async function getchargingstation(lat, lon){
    fetch(`http://127.0.0.1:5000/station?lat=${lat}&lon=${lon}`)
    .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();})
    .then(data => {
        data.forEach(element => {
            var icon = L.icon({iconUrl: 'charging_station.png',iconSize: [20, 20]})
            var marker = L.marker([element.lat, element.lon],{icon:icon}).addTo(map);
            
            marker.addEventListener('click', async function() {
                marker.bindPopup(`<b>Charging Station</b><br>${element.name}<br>`).openPopup();
                click_lat = element.lat
                click_lon = element.lon
                remaining_battery = await createPath()
                const currentBatteryLabel = document.createElement('label');
                currentBatteryLabel.setAttribute('for', 'currentBatteryLevel');
                currentBatteryLabel.textContent = "Current Battery level is: " + Math.round(remaining_battery * 10)/10 + " %";
                const form = document.getElementById('batteryInputForm');
                form.insertBefore(currentBatteryLabel, form.firstChild);
                map.setView([click_lat,click_lon], 10);
                batteryForm.style.display = 'flex';
            });
        });
    })
}




function show_marker(lat, lon, picture) {
    L.marker([lat, lon],{icon:picture}).addTo(map);
}

function refresh() {
    map.eachLayer(function (layer) {
        if (layer instanceof L.Marker || layer instanceof L.Polygon || layer instanceof L.Polyline) {
            map.removeLayer(layer);
        }
    });
}

function refresh_shapeAndLine() {
    map.eachLayer(function (layer) {
        if (layer instanceof L.Polygon) {
            map.removeLayer(layer);
        }
    })
}

function removeMarkerAtCoordinates(latToRemove, lngToRemove) {
    // Iterate through all markers on the map
    map.eachLayer(function(layer) {
        // Check if the layer is a marker
        if (layer instanceof L.Marker) {
            // Get the coordinates of the marker
            var markerLat = layer.getLatLng().lat;
            var markerLng = layer.getLatLng().lng;

            // Check if the marker coordinates match the coordinates to remove
            if (markerLat === latToRemove && markerLng === lngToRemove) {
                map.removeLayer(layer);
            }
        }
    });
}


async function geocodeAddress(address) {
    return new Promise((resolve, reject) => {
        var geocoder = new google.maps.Geocoder();
        geocoder.geocode({'address': address}, function(results, status) {
            if (status === 'OK' && results[0]) {
                var latitude = results[0].geometry.location.lat();
                var longitude = results[0].geometry.location.lng();
                resolve([latitude, longitude]);
            } else {
                reject('Geocode was not successful for the following reason: ' + status);
            }
        });
    });
}

function initAutocomplete() {
    var autocomplete = new google.maps.places.Autocomplete(
        document.getElementById('address'), {
            types: ['geocode']
        });
}


    document.getElementById('coordinateForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    setVisible('#loading', true);
    var addressInput = document.getElementById('address').value;
    var batteryInput = document.getElementById('battery').value;

    var address = addressInput !== '' ? addressInput : "2922 10 St SW, Calgary";

    var battery = batteryInput !== '' ? batteryInput : "100";
    
    var [latitude, longitude] = await geocodeAddress(address);
    start = [latitude, longitude];
    remaining_battery = battery
    refresh();
    map.setView([latitude, longitude], 7);
    show_marker(latitude,longitude,carIcon);
    // show_starting_point(latitude, longitude);
    getalphashape(latitude, longitude, remaining_battery);
    await getchargingstation(latitude, longitude);
})

