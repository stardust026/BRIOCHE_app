from flask import Flask, jsonify, request
from flask_cors import CORS
from EV_heatmap_new import return_alpha_shape, get_public_charging_stations

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    hello = "Hello, World!"
    return jsonify(hello)

@app.route('/alpha')
def get_alpha_shape():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    processed_data = return_alpha_shape(lat,lon)
    return jsonify(processed_data)

@app.route('/station')
def get_station():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    processed_data = get_public_charging_stations(lat, lon)
    return jsonify(processed_data)


if __name__ == '__main__':
    app.run(debug=True)