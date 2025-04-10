from flask import Flask, request, jsonify
from google_map_search import GoogleMapSearch

app = Flask(__name__)
gmaps = GoogleMapSearch()
last_info = {}

@app.route("/search", methods=["GET"])
def search_restaurants():
    global last_info
    address = request.args.get("address") # address string
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius = request.args.get("radius", default=10000, type=int)
    next_page_token = request.args.get("next_page_token") # next page token

    lat_lng = {"lat": lat, "lng": lng} if lat and lng else None

    if next_page_token:
        restaurants_response, next_page_token = gmaps.get_nearby_restaurants(
            page_token=last_info.get("next_page_token"),
            location=last_info.get("lat_lng"),
            radius=last_info.get("radius")
        )
        restaurants_result = gmaps.extract_restaurant_info(restaurants_response)
        last_info["next_page_token"] = next_page_token

        return jsonify({
            "results": restaurants_result,
            "next_page_token": next_page_token
        })

    if address:
        lat_lng = gmaps.get_address_gecode(address)
    
    if lat_lng:
        try:
            restaurants_response, next_page_token = gmaps.get_nearby_restaurants(lat_lng, radius)
            restaurants_result = gmaps.extract_restaurant_info(restaurants_response)
            if next_page_token:
                last_info["next_page_token"] = next_page_token
                last_info["lat_lng"] = lat_lng
                last_info["radius"] = radius
            return jsonify({
                "results": restaurants_result,
                "next_page_token": next_page_token
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

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