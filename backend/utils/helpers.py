import spacy
import pandas as pd
import numpy as np
from typing import List

embedding = spacy.load("en_core_web_lg")


class Tools:
    def extract_review(self, reviews: List[dict]) -> str:
        if reviews[0].get("text"):
            raw_reviews = " ".join(review["text"] for review in reviews)
            return raw_reviews.replace("\\n", " ").replace("\n", " ")
        elif reviews[0].get("reviews"):
            raw_reviews = " ".join(
                review["text"] for item in reviews for review in item["reviews"]
            )
            return raw_reviews.replace("\\n", " ").replace("\n", " ")
        return ""

    def get_vector(self, texts: List[str]) -> np.ndarray:
        if texts:
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

    def top_5_restaurants(self, data: pd.DataFrame, labels_score: dict) -> pd.DataFrame:
        """
        Combine the restaurant data with their corresponding scores and sort them.
        """
        data["final_score"] = data["cluster"].map(labels_score) + data["similarity"]
        data = data.sort_values(by="final_score", ascending=False)
        return data[:5]
