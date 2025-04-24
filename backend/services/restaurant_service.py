from .google_map_search import GoogleMapSearch

gmaps = GoogleMapSearch()


def search_nearby_restaurants(
    address=None,
    lat=None,
    lng=None,
    radius=100000,
    next_page_token=None,
    last_info=None,
):
    """
    Search for nearby restaurants based on location information.

    Args:
        address (str, optional): Address string to geocode.
        lat (float, optional): Latitude coordinate.
        lng (float, optional): Longitude coordinate.
        radius (int, optional): Search radius in meters. Default is 100000.
        next_page_token (str, optional): Token for pagination.
        last_info (dict, optional): Dictionary to store state between calls.

    Returns:
        tuple: (results, next_page_token, status_code, error_message)
               results: List of restaurant data
               next_page_token: Token for next page of results
               status_code: HTTP status code (200 for success)
               error_message: Error message if any
    """
    if last_info is None:
        last_info = {}

    lat_lng = {"lat": lat, "lng": lng} if lat and lng else None

    if next_page_token:
        restaurants_response, next_page_token = gmaps.get_nearby_restaurants(
            page_token=last_info.get("next_page_token"),
            location=last_info.get("lat_lng"),
            radius=last_info.get("radius"),
        )
        restaurants_result = gmaps.extract_restaurant_info(restaurants_response)
        last_info["next_page_token"] = next_page_token

        return restaurants_result, next_page_token, 200, None

    if address:
        lat_lng = gmaps.get_address_gecode(address)

    if lat_lng:
        try:
            restaurants_response, next_page_token = gmaps.get_nearby_restaurants(
                location=lat_lng, radius=radius
            )
            restaurants_result = gmaps.extract_restaurant_info(restaurants_response)
            if next_page_token:
                last_info["next_page_token"] = next_page_token
                last_info["lat_lng"] = lat_lng
                last_info["radius"] = radius
            return restaurants_result, next_page_token, 200, None
        except ValueError as e:
            return None, None, 400, str(e)
    else:
        return None, None, 400, "lat_lng are required."
