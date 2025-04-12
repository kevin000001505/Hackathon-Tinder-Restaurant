import os
import sys

# Insert the project root directory into sys.path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from backend.google_map_search import GoogleMapSearch

# Define a fake client to simulate responses from googlemaps.Client
class FakeGoogleMapsClient:
    def geocode(self, address):
        # Fake response for get_address_gecode()
        return [{"geometry": {"location": {"lat": 12.34, "lng": 56.78}}}]
    
    def geolocate(self):
        # Fake response for get_self_geocode()
        return {"location": {"lat": 98.76, "lng": 54.32}}

    def places_nearby(self, **kwargs):
        # Fake response for get_nearby_restaurants()
        return {
            "results": [
                {"place_id": "fake_place", "name": "Fake Restaurant", "vicinity": "Fake Address"}
            ],
            "next_page_token": None
        }

    def place(self, place_id, reviews_sort, fields):
        # Fake response for get_info_by_place_id()
        return {
            "result": {
                "name": "Test Restaurant",
                "formatted_address": "Test Address",
                "geometry": {"location": {"lat": 12.34, "lng": 56.78}},
                "current_opening_hours": {
                    "open_now": True,
                    "weekday_text": ["Monday: 9:00 AM – 5:00 PM"]
                },
                "user_ratings_total": 100,
                "price_level": 2,
                "rating": 4.5,
                "types": ["restaurant"],
                "vicinity": "Test Vicinity",
                "website": "http://test.com",
                "formatted_phone_number": "123-456-7890",
                "photos": []
            }
        }

@pytest.fixture
def fake_google_map_search(monkeypatch):
    # Use a dummy API key that starts with "AIza" to satisfy the validation in the googlemaps.Client
    gms = GoogleMapSearch(api_key="AIzaDummyKey")
    fake_client = FakeGoogleMapsClient()
    
    # Replace the real googlemaps.Client with the fake one.
    monkeypatch.setattr(gms, "client", fake_client)
    return gms

def test_get_address_gecode(fake_google_map_search):
    address = "Some Fake Address"
    result = fake_google_map_search.get_address_gecode(address)
    assert result == {"lat": 12.34, "lng": 56.78}

def test_get_self_geocode(fake_google_map_search):
    result = fake_google_map_search.get_self_geocode()
    assert result == {"lat": 98.76, "lng": 54.32}

def test_clean_weekday_text(fake_google_map_search):
    # Provide a test string with fancy unicode spacing characters.
    input_text = ["Monday: 11:30\u202fAM\u2009–\u20092:30\u202fPM"]
    expected = ["Monday: 11:30 AM – 2:30 PM"]
    output = fake_google_map_search.clean_weekday_text(input_text)
    assert output == expected

def test_get_nearby_restaurants(fake_google_map_search):
    location = {"lat": 12.34, "lng": 56.78}
    keyword = "test"
    radius = 5000
    results, next_page = fake_google_map_search.get_nearby_restaurants(location, keyword, radius)
    assert isinstance(results, list)
    assert len(results) > 0
    assert next_page is None

def test_get_info_by_place_id(fake_google_map_search):
    info = fake_google_map_search.get_info_by_place_id("fake_place")
    assert info["name"] == "Test Restaurant"
    assert info["formatted_address"] == "Test Address"
    assert info["current_opening_hours"]["open_now"] is True