IMAGE_EXPIRY_SECONDS = 3600  # Image expiry time

FIREBASE_ACCOUNT_KEY = "./utils/Hackathon Firebase Admin SDK.json"
FIREBASE_COLLECTION = "(default)"

FIELDS = [
    "website",
    "takeout",
    "formatted_address",
    "serves_breakfast",
    "business_status",
    "serves_wine",
    "url",
    "serves_vegetarian_food",
    "vicinity",
    "name",
    "dine_in",
    "geometry",
    "user_ratings_total",
    "price_level",
    "current_opening_hours",
    "reviews",
    "adr_address",
    "serves_beer",
    "place_id",
    "type",
    "review",
    "opening_hours",
    "serves_brunch",
    "permanently_closed",
    "rating",
    "formatted_phone_number",
    "delivery",
    "geometry/location",
    "photo",
    "wheelchair_accessible_entrance",
    "utc_offset",
    "editorial_summary",
    "curbside_pickup",
    "address_component",
    "reservable",
    "serves_lunch",
    "serves_dinner",
]

DROP_COLUMNS = [
    "place_id",
    "location",
    "formatted_address",
    "open_now",
    "periods",
    "opening_hours",
    "vicinity",
    "website",
    "phone_number",
    "photos",
    "business_status",
    "types",
]

TEXT_COLUMNS = [
    "restaurant_name",
    "editorial_summary",
    "reviews",
    "extended_reviews",
]

NUMERICALS_COLUMNS = ["price_level", "rating", "total_user_ratings", "lat", "lng"]

CATEGORICAL_COLUMNS = [
    "curbside_pickup",
    "delivery",
    "dine_in",
    "reservable",
    "takeout",
    "serves_breakfast",
    "serves_lunch",
    "serves_dinner",
    "serves_brunch",
    "serves_vegetarian_food",
    "serves_beer",
    "serves_wine",
    "wheelchair_accessible",
    "bar",
    "cafe",
    "establishment",
    "food",
    "liquor_store",
    "meal_delivery",
    "meal_takeaway",
    "point_of_interest",
    "restaurant",
    "store",
]
