from flask import Flask, jsonify, request
from flask_cors import CORS
from EV_heatmap_new import return_alpha_shape, get_public_charging_stations
import os

app = Flask(__name__)
CORS(app)

current_directory = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def hello():
    hello = "Hello, World!"
    return jsonify(hello)

@app.route('/alpha')
def get_alpha_shape():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    battery = float(request.args.get('battery')) 
    processed_data = return_alpha_shape(lat, lon, battery)
    response = jsonify(processed_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/station')
def get_station():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    processed_data = get_public_charging_stations(lat, lon)
    response = jsonify(processed_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == '__main__':
    app.run(debug=True)