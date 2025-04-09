from flask import Flask, request, jsonify
from google_map_search import GoogleMapSearch

app = Flask(__name__)
gmaps = GoogleMapSearch()

@app.route("/search", methods=["GET"])
def search_restaurants():
    query = request.args.get("query") # restaurant type
    address = request.args.get("address") # address string
    radius = request.args.get("radius", default=1000, type=int)

    if address is None:
        lat_lng = gmaps.get_self_geocode()

    if query is None:
        restaurants_result = gmaps.get_nearby_restaurants(lat_lng, radius)
        return jsonify(restaurants_result)
    
    if query and lat_lng:
        restaurants_result, next_page_token = gmaps.search_restaurants(query, lat_lng, radius)
        return jsonify(restaurants_result)

@app.route("/geolocate", methods=["GET"])
def geolocate():
    try:
        location = gmaps.get_self_geocode()
        return jsonify(location)
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)