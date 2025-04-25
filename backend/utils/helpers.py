import spacy
import math
import pandas as pd
import numpy as np
from typing import List

embedding = spacy.load("en_core_web_lg")


class Tools:
    def extract_review(self, reviews) -> str:
        if not reviews:
            return ""
        if isinstance(reviews[0], dict) and "text" in reviews[0]:
            raw_reviews = " ".join(review["text"] for review in reviews)
            return raw_reviews.replace("\\n", " ").replace("\n", " ")
        elif isinstance(reviews[0], dict) and "reviews" in reviews[0]:
            raw_reviews = " ".join(
                review["text"] for item in reviews for review in item["reviews"]
            )
            return raw_reviews.replace("\\n", " ").replace("\n", " ")
        else:
            raise ValueError("Invalid review format. Not a list or dict.")

    def get_vector(self, texts: str) -> np.ndarray:
        if len(texts) > 0:
            return embedding(texts).vector
        return np.zeros(embedding.vocab.vectors.shape[1])

    def extract_all_place_ids(self, data: List[dict]) -> List[str]:
        """
        Extract all place_ids from the data.
        """
        result = set()
        for item in data:
            if "place_id" in item:
                result.add(item["place_id"])
        return list(result)

    def upadate_cluster_weights(
        self, whole_dict: dict, like_dict: dict, dislike_dict: dict
    ) -> dict:
        """
        Update the cluster weights based on user preferences.
        """
        for cluster in whole_dict:
            if cluster in like_dict:
                whole_dict[cluster] += 1
            if cluster in dislike_dict:
                whole_dict[cluster] -= 1
        return whole_dict

    def get_place_id_data(
        self, data: pd.DataFrame, place_id_list: List[str]
    ) -> pd.DataFrame:
        """
        Get the data for a specific place_id.
        """
        return data[data["place_id"].isin(place_id_list)]

    def get_locations(self, lat: float, lng: float, radius=100000) -> dict:
        """
        Given a center latitude and longitude and a radius in meters,
        return a dict with center, north, south, east, and west coordinates.
        """
        delta_lat = radius / 111000.0
        delta_lng = radius / (111000.0 * math.cos(math.radians(lat)))
        return {
            "center": {"lat": lat, "lng": lng},
            "north": {"lat": lat + delta_lat, "lng": lng},
            "south": {"lat": lat - delta_lat, "lng": lng},
            "east": {"lat": lat, "lng": lng + delta_lng},
            "west": {"lat": lat, "lng": lng - delta_lng},
        }
