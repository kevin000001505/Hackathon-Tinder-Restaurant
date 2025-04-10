import os
from dotenv import load_dotenv
import logging
import googlemaps
from datetime import datetime
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)

GOOGLE_MAPS_API_KEY = None

def validate_google_api_key() -> str:
    tries = 0
    key_idx = 1
    api_key = os.getenv(f"GOOGLE_MAPS_API_KEY_{key_idx}")
    while api_key and tries < 10:
        try:
            # Try authenticating the API key
            gmaps = googlemaps.Client(key=api_key)
            geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')
            if geocode_result:
                return api_key
            else:
                logging.warning("API key might be invalid or there was an issue with the request")
        except Exception as e:
            logging.error(e)
            continue
        key_idx += 1
        api_key = os.getenv(f"GOOGLE_MAPS_API_KEY_{key_idx}")
        tries += 1
        time.sleep(1) # Try again in 1 second
    raise ValueError("You have no valid API keys.")

# Find valid Google Maps API key
GOOGLE_MAPS_API_KEY = validate_google_api_key()

class GoogleMapSearch:
    def __init__(self, api_key=GOOGLE_MAPS_API_KEY):
        self.client = googlemaps.Client(key=api_key)
        self.restaurant_info = list()

    def get_address_gecode(self, address) -> dict:
        """
        Search for a place using a address string.
        :param address: The search address string.
        :return: A dictionary containing its latitude/longitude.
        """
        # Get the address info
        address_result = self.client.place(
            input=address,
            input_type="textquery",
            fields=["place_id", "geometry/location"],
        )
        # Get the address latitude and longitude
        place_lat_lng = (
            address_result.get("candidates", [{}])[0]
            .get("geometry", {})
            .get("location", {})
        )
        return place_lat_lng

    def get_self_geocode(self) -> dict:
        """
        Geocode your location right now to get latitude and longitude.
        :return: A dictionary with latitude and longitude.
        """
        geocode_result = self.client.geolocate()
        if geocode_result:
            location = geocode_result.get("location", {})
            return location
        else:
            raise ValueError("Geolocation failed. Please check your API key or network connection.")

    def get_place_photos(self, restaurant_info):
        for restaurant in restaurant_info:
            place_id = restaurant.get("place_id")
            if place_id:
                place_info = self.client.place(place_id=place_id, fields=["photos"])
                logging.debug(place_info)

                for info in place_info["result"]["photos"]:
                    photo_id = info["photo_reference"]
                    raw_photo = self.client.places_photo(
                        photo_reference=photo_id, max_width=400, max_height=400
                    )
                    f = open(f"photos/{photo_id}.jpg", "wb")
                    for chunk in raw_photo:
                        if chunk:
                            f.write(chunk)
                    f.close()
        logging.info("Photos downloaded successfully.")
    
    def get_nearby_restaurants(self, location, keyword, radius=1000, page_token=None):
        """
        Get nearby restaurants using latitude and longitude.
        :param lat_lng: A dictionary containing latitude and longitude.
        :param radius: The distance (in meters) within which to return place results.
        :return: A list of places matching the query.
        """
        if location is None:
            raise ValueError("Latitude and Longitude are required for searching nearby restaurants.")
        if int(radius) > 100000:
            raise ValueError("The radius must be less than 100,000 meters or we get no results.")
        else:
            restaurants_response = self.client.places_nearby(
                location=location,
                radius=radius, # max 100000 meters
                keyword=keyword,
                language=None, 
                min_price=None, # 0 to 4
                max_price=None, # 0 to 4
                open_now=True,
                type="restaurant",
                rank_by="prominence", # or "distance",
                page_token=page_token
            )
            next_page_token = restaurants_response.get("next_page_token")
            restaurants_results = restaurants_response.get("results", [])
            logging.info(f"Result return: {len(restaurants_results)}")
            if restaurants_results:
                return restaurants_results, next_page_token
            else:
                raise ValueError("No restaurants found in the specified radius.")


if __name__ == "__main__":
    gmaps = GoogleMapSearch()
    query = "Japanese restaurants"
    location = {"lat": 38.8248377, "lng": -77.3209443}  # The Main Street, Virginia
    radius = 5000  # 5 km
    results = gmaps.get_nearby_restaurants(location, query, radius)

    for place in results:
        print(f"Name: {place['name']}, Address: {place.get('vicinity', 'N/A')}")
