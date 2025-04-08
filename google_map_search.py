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
                logging.info("API key might be invalid or there was an issue with the request")
        except Exception as e:
            logging.info(e)
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

    def search_restaurants(self, query, location=None, radius=1000, page_token=None):
        """
        Search for places using a query string.
        :param query: The search query string.
        :param location: Optional. The latitude/longitude around which to retrieve place information.
        :param radius: Optional. The distance (in meters) within which to return place results.
        :return: A list of 20 places matching the query.
        """
        if location is None:
            raise ValueError("Location is required for searching restaurants.")
        else:
            restaurants_response = self.client.places(
                query=query,
                location=location,
                radius=radius,
                language=None,
                min_price=None,
                max_price=None,
                open_now=False,
                type="restaurant",
                region=None,
                page_token=page_token,
            )
            next_page_token = restaurants_response.get("next_page_token")
            restaurants_results = restaurants_response.get("results", [])
            return restaurants_results, next_page_token


    def search_place(self, query):
        """
        Search for a place using a query string.
        :param query: The search query string.
        :return: A dictionary containing the place ID and its latitude/longitude.
        """
        place_result = self.client.places(
            input=query,
            input_type="textquery",
            fields=["place_id", "geometry/location"],
        )
        place_lat_lng = (
            place_result.get("candidates", [{}])[0]
            .get("geometry", {})
            .get("location", {})
        )
        return place_lat_lng

    def get_self_geocode(self):
        """
        Geocode your location to get latitude and longitude.
        :return: A dictionary with latitude and longitude.
        """
        geocode_result = self.client.geolocate()
        if geocode_result:
            location = geocode_result.get("location", {})
            return location

    def get_place_photos(self, restaurant_info):
        for restaurant in restaurant_info:
            place_id = restaurant.get("place_id")
            if place_id:
                place_info = self.client.place(place_id=place_id, fields=["photos"])

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


if __name__ == "__main__":
    gmaps = GoogleMapSearch()
    query = "Japanese restaurants"
    # maps_response = gmaps.geolocate()
    # location = maps_response.get('location')
    location = {"lat": 38.8248377, "lng": -77.3209443}  # The Main Street, Virginia
    radius = 5000  # 5 km
    results = gmaps.search_restaurants(query, location, radius)

    for place in results:
        print(f"Name: {place['name']}, Address: {place.get('vicinity', 'N/A')}")
