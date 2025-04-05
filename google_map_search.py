import os
from dotenv import load_dotenv
import googlemaps
from datetime import datetime

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

if not GOOGLE_MAPS_API_KEY:
    raise ValueError("Please set the GOOGLE_MAPS_API_KEY environment variable.")


class GoogleMapSearch:
    def __init__(self, api_key):
        self.client = googlemaps.Client(key=api_key)

    def search_places(self, query, location=None, radius=1000, page_token=None) -> list:
        """
        Search for places using a query string.
        :param query: The search query string.
        :param location: Optional. The latitude/longitude around which to retrieve place information.
        :param radius: Optional. The distance (in meters) within which to return place results.
        :return: A list of 20 places matching the query.
        """
        if location:
            #
            places_result = self.client.places(
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
        else:
            places_result = self.client.places(query=query)

        return places_result.get("results", [])


if __name__ == "__main__":
    gmaps = GoogleMapSearch(GOOGLE_MAPS_API_KEY)
    query = "Japanese restaurants"
    # maps_response = gmaps.geolocate()
    # location = maps_response.get('location')
    location = {"lat": 38.8248377, "lng": -77.3209443}  # The Main Street, Virginia
    radius = 5000  # 5 km
    results = gmaps.search_places(query, location, radius)

    for place in results:
        print(f"Name: {place['name']}, Address: {place.get('vicinity', 'N/A')}")
