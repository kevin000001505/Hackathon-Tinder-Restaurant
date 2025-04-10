from flask import Flask, request, jsonify
from google_map_search import GoogleMapSearch

app = Flask(__name__)
gmaps = GoogleMapSearch()

@app.route("/search", methods=["GET"])
def search_restaurants():
    query = request.args.get("query", "restaurant") # restaurant type
    address = request.args.get("address") # address string
    lat_lng = request.args.get("lat_lng") # lat and lng dict
    radius = request.args.get("radius", default=1000, type=int)
    next_page_token = request.args.get("next_page_token") # next page token

    if next_page_token:
        restaurants_result, next_page_token = gmaps.get_nearby_restaurants(
            next_page_token=next_page_token
        )
        return jsonify(restaurants_result)

    if address:
        lat_lng = gmaps.get_address_gecode(address)
    
    if lat_lng:
        restaurants_result, next_page_token = gmaps.get_nearby_restaurants(lat_lng, query, radius)
        return jsonify(restaurants_result)
    else:
        return jsonify({"error": "lat_lng are required."}), 400

@app.route("/geolocate", methods=["GET"])
def geolocate():
    try:
        location = gmaps.get_self_geocode()
        return jsonify(location)
    except ValueError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)