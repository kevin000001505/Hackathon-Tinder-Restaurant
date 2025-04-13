import time, os, threading, logging, googlemaps, unicodedata
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
logging.basicConfig(level=logging.INFO)

GOOGLE_MAPS_API_KEY = None
IMAGE_EXPIRY_SECONDS = 3600  # Image expiry time

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
        self.photos = {} # Store download time for photos for automatic cleanup

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
        photo_num = 0
        if raw_photos:
            logging.debug(raw_photos)
            
            # Create the list of urls to the photos
            image_urls = [f'http://127.0.0.1:5000/photos/{place_id}/{num}' for num in range(photo_num)]

            # If photos are already cached, skipped downloading
            if not os.path.isdir(f'photos/{place_id}'):
                os.mkdir(f'photos/{place_id}')
                for photo in raw_photos[:3]:
                    photo_reference = photo.get("photo_reference", "")
                    if photo_reference:
                        photo_response = self.client.places_photo(photo_reference=photo_reference, max_width=400, max_height=400)
                        self.download_photo(place_id, photo_response, photo_num)
                    photo_num += 1
            
            return image_urls
        
        logging.info(f"{photo_num} photos downloaded successfully.")
        return None
        
    
    def download_photo(self, place_id, photo_response, photo_num):
        self.photos[place_id] = datetime.now()
        with open(f"photos/{place_id}/{photo_num}.jpg", "wb") as f:
            for chunk in photo_response:
                if chunk:
                    f.write(chunk)
    
    def cleanup_photos(self, place_id):
        os.rmdir(f"photos/{place_id}")
        self.photos.pop(place_id)

    # Background cleanup thread
    def auto_cleanup_photos(self):
        while True:
            time.sleep(10)  # Sweep interval
            now = datetime.now()
            expired_keys = [key for key, data in self.photos.items()
                            if now - data > timedelta(seconds=IMAGE_EXPIRY_SECONDS)]
            for key in expired_keys:
                self.cleanup_photos(key)
                logging.debug(f"Deleted expired photos: {key}")
    
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
        restaurant_info = self.client.place(place_id=place_id, reviews_sort="newest", fields=['website', 'takeout', 'formatted_address', 'serves_breakfast', 'business_status', 'serves_wine', 'url', 'serves_vegetarian_food', 'vicinity', 'name', 'dine_in', 'geometry', 'user_ratings_total', 'price_level', 'current_opening_hours', 'reviews', 'adr_address', 'serves_beer', 'place_id', 'type', 'review', 'opening_hours', 'serves_brunch', 'permanently_closed', 'rating', 'formatted_phone_number', 'delivery', 'geometry/location', 'photo', 'wheelchair_accessible_entrance', 'utc_offset', 'editorial_summary', 'curbside_pickup', 'address_component', 'reservable', 'serves_lunch', 'serves_dinner'])
        return restaurant_info.get("result", {})
    
    import unicodedata

    def clean_weekday_text(self, weekday_text):
        cleaned = []
        for line in weekday_text:
            normalized = unicodedata.normalize("NFKC", line)  # Normalize fancy spaces
            cleaned.append(normalized)
        return cleaned

    def extract_restaurant_info(self, restaurants_results):
        """
        Extract restaurant information from the response.
        :param restaurant_info: The response from the Google Maps API.
        :return: A list of dictionaries containing restaurant information.
        """
        results = []
        for restaurant in restaurants_results:
            place_id = restaurant.get("place_id")
            restaurant_info = self.get_info_by_place_id(place_id)

            restaurant_name = restaurant_info.get("name", "N/A")
            formatted_address = restaurant_info.get("formatted_address", "N/A")
            location = restaurant_info.get("geometry", {}).get("location", {})
            open_now = restaurant_info.get("current_opening_hours", {}).get("open_now", False)
            periods = restaurant_info.get("current_opening_hours", {}).get("periods", False)
            opening_hours_text = self.clean_weekday_text(restaurant_info.get("current_opening_hours", {}).get("weekday_text", []))
            price_level = restaurant_info.get("price_level", "N/A")
            total_user_ratings = restaurant_info.get("user_ratings_total", "N/A")
            vicinity = restaurant_info.get("vicinity", "N/A")
            rating = restaurant_info.get("rating", "N/A")
            types = restaurant_info.get("types", [])
            website = restaurant_info.get("website", "N/A")
            phone_number = restaurant_info.get("formatted_phone_number", "N/A")
            raw_photos = restaurant_info.get("photos", [])
            curbside_pickup = restaurant_info.get("curbside_pickup", False)
            delivery = restaurant_info.get("delivery", False)
            dine_in = restaurant_info.get("dine_in", False)
            reservable = restaurant_info.get("reservable", False)
            takeout = restaurant_info.get("takeout", False)
            serves_breakfast = restaurant_info.get("serves_breakfast", False)
            serves_lunch = restaurant_info.get("serves_lunch", False)
            serves_dinner = restaurant_info.get("serves_dinner", False)
            serves_brunch = restaurant_info.get("serves_brunch", False)
            serves_vegetarian_food = restaurant_info.get("serves_vegetarian_food", False)
            serves_beer = restaurant_info.get("serves_beer", False)
            serves_wine = restaurant_info.get("serves_wine", False)
            wheelchair_accessible = restaurant_info.get("wheelchair_accessible_entrance", False)
            business_status = restaurant_info.get("business_status", "N/A")
            editorial_summary = restaurant_info.get("editorial_summary", {}).get("overview", "")
            photos = self.get_place_photos(place_id, raw_photos)
            reviews = restaurant_info.get("reviews", [])
            results.append(
                {
                    "place_id": place_id,
                    "restaurant_name": restaurant_name,
                    "formatted_address": formatted_address,
                    "location": location,
                    "open_now": open_now,
                    "periods": periods,
                    "opening_hours": opening_hours_text,
                    "price_level": price_level,
                    "rating": rating,
                    "types": types,
                    "total_user_ratings": total_user_ratings,
                    "vicinity": vicinity,
                    "website": website,
                    "phone_number": phone_number,
                    "photos": photos, # list of photo 
                    "reviews": reviews, # list of reviews
                    "curbside_pickup": curbside_pickup,
                    "delivery": delivery,
                    "dine_in": dine_in,
                    "reservable": reservable,
                    "takeout": takeout,
                    "serves_breakfast": serves_breakfast,
                    "serves_lunch": serves_lunch,
                    "serves_dinner": serves_dinner,
                    "serves_brunch": serves_brunch,
                    "serves_vegetarian_food": serves_vegetarian_food,
                    "serves_beer": serves_beer,
                    "serves_wine": serves_wine,
                    "wheelchair_accessible": wheelchair_accessible,
                    "business_status": business_status,
                    "editorial_summary": editorial_summary,
                }
            )
        return results




if __name__ == "__main__":
    gmaps = GoogleMapSearch()
    threading.Thread(target=gmaps.auto_cleanup_photos, daemon=True).start()
    query = "Japanese restaurants"
    location = {"lat": 38.8248377, "lng": -77.3209443}  # The Main Street, Virginia
    radius = 5000  # 5 km
    results = gmaps.get_nearby_restaurants(location, query, radius)

    for place in results:
        print(f"Name: {place['name']}, Address: {place.get('vicinity', 'N/A')}")
