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

    def get_address_gecode(self, address) -> dict:
        """
        Search for a place using a address string.
        :param address: The search address string.
        :return: A dictionary containing its latitude/longitude.
        """

        # Get the address latitude and longitude
        place_info = self.client.geocode(address)
        place_lat_lng = place_info[0].get("geometry", {}).get("location", {})
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

    def get_place_photos(self, place_id:str, raw_photos:list) -> list:
        result = []
        photo_num = 0
        if raw_photos:
            logging.debug(raw_photos)
            for photo in raw_photos:
                photo_reference = photo.get("photo_reference", "")
                if photo_reference:
                    photo_response = self.client.places_photo(photo_reference=photo_reference, max_width=400, max_height=400)
                    self.download_photo(place_id, photo_response, photo_num)
                    photo_num += 1
        logging.info(f"{photo_num} photos downloaded successfully.")
        return result
    
    def download_photo(self, place_id, photo_response, photo_num):
        
        f = open(f"photos/{place_id}_photo_{photo_num}.jpg", "wb")
        for chunk in photo_response:
            if chunk:
                f.write(chunk)
        f.close()
        
    
    def get_nearby_restaurants(self, location=None, keyword=None, radius=10000, page_token=None):
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
                open_now=False,
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


    def get_info_by_place_id(self, place_id):
        """
        Get restaurant information using place_id.
        :param place_id: The place ID of the restaurant.
        :return: A dictionary containing restaurant information.
        """
        restaurant_info = self.client.place(place_id=place_id, reviews_sort="newest", fields=["name", "review", "rating", "type", "price_level", "user_ratings_total", "formatted_phone_number", "website", "reviews", "photo", "curbside_pickup", "delivery"])
        return restaurant_info.get("result", {})
    

    def extract_restaurant_info(self, restaurants_results):
        """
        Extract restaurant information from the response.
        :param restaurant_info: The response from the Google Maps API.
        :return: A list of dictionaries containing restaurant information.
        """
        results = []
        for restaurant in restaurants_results:
            place_id = restaurant.get("place_id")
            vicinity = restaurant.get("vicinity", "N/A")
            restaurant_info = self.get_info_by_place_id(place_id)

            restaurant_name = restaurant_info.get("name", "N/A")
            price_level = restaurant_info.get("price_level", "N/A")
            total_user_ratings = restaurant_info.get("user_ratings_total", "N/A")
            rating = restaurant_info.get("rating", "N/A")
            types = restaurant_info.get("types", [])
            website = restaurant_info.get("website", "N/A")
            phone_number = restaurant_info.get("formatted_phone_number", "N/A")
            raw_photos = restaurant_info.get("photos", [])
            # photos = self.get_place_photos(place_id, raw_photos)
            photos = raw_photos
            reviews = restaurant_info.get("reviews", [])
            results.append(
                {
                    "place_id": place_id,
                    "restaurant_name": restaurant_name,
                    "price_level": price_level,
                    "rating": rating,
                    "types": types,
                    "total_user_ratings": total_user_ratings,
                    "vicinity": vicinity,
                    "website": website,
                    "phone_number": phone_number,
                    "photos": photos, # list of photos reference
                    "reviews": reviews, # list of reviews
                }
            )
        return results




if __name__ == "__main__":
    gmaps = GoogleMapSearch()
    query = "Japanese restaurants"
    location = {"lat": 38.8248377, "lng": -77.3209443}  # The Main Street, Virginia
    radius = 5000  # 5 km
    results = gmaps.get_nearby_restaurants(location, query, radius)

    for place in results:
        print(f"Name: {place['name']}, Address: {place.get('vicinity', 'N/A')}")
