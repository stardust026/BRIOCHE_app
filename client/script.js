// set starting point coordinate
var start = [51.0276233, -114.087835];

// create a map in the "map" div, set the view to a given place and zoom
var map = L.map('map').setView(start, 7);

var carIcon = L.icon({
    iconUrl: 'electric-car.png',
    iconSize:     [38, 38], // size of the icon
    iconAnchor:   [22, 22], // point of the icon which will correspond to marker's location
    popupAnchor:  [-3, -76] // point from which the popup should open relative to the iconAnchor
});

// add an OpenStreetMap tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
}).addTo(map);

function getalphashape(lat, lon, battery){
    fetch(`http://127.0.0.1:5000/alpha?lat=${lat}&lon=${lon}&battery=${battery}`)
    .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();})
    .then(data => {
        console.log("data:",data);
        var colorlist = ['green', 'yellow', 'red']
        var count = 0
        data.forEach(element => {
            // Check if the element is an empty list
            if (element.length > 0) {
                var polygon = L.polygon(element,{
                    color: colorlist[count],
                    fillColor: colorlist[count],
                    weight: 1
                }).addTo(map);
            }
            count++;
        });
    });
    }

function getchargingstation(lat, lon){
    fetch(`http://127.0.0.1:5000/station?lat=${lat}&lon=${lon}`)
    .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();})
    .then(data => {
        console.log(data);
        data.forEach(element => {
            var marker = L.marker([element.lat, element.lon]).addTo(map);
            marker.addEventListener('click', function(){
                show_charging_station_range(element.lat, element.lon);
            });
        });
    })
}

function show_charging_station_range(lat, lon) {
    refresh();
    map.setView([lat, lon], 7);
    show_starting_point(lat, lon);
    getchargingstation(lat, lon);
    getalphashape(lat, lon);
}

function show_starting_point(lat, lon) {
    L.marker([lat, lon],{icon:carIcon}).addTo(map);
}

function refresh() {
    map.eachLayer(function (layer) {
        if (layer instanceof L.Marker || layer instanceof L.Polygon) {
            map.removeLayer(layer);
        }
    });
}

    document.getElementById('coordinateForm').addEventListener('submit', function(event) {
    event.preventDefault();
    var latitude = document.getElementById('latitude').value;
    var longitude = document.getElementById('longitude').value;
    var battery = document.getElementById('battery').value;
    refresh();
    map.setView([latitude, longitude], 7);
    show_starting_point(latitude, longitude);
    getchargingstation(latitude, longitude);
    getalphashape(latitude, longitude, battery);
})
