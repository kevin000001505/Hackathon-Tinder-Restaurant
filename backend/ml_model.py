import pandas as pd
import numpy as np
from typing import List
from sklearn.base import BaseEstimator, TransformerMixin

# Sklearn Packages
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import FunctionTransformer

# K-Prototypes
from kmodes.kprototypes import KPrototypes


drop_cols = [
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

text_cols = [
    "restaurant_name",
    "editorial_summary",
    "reviews",
    "extened_reviews",
]

numericals_cols = ["price_level", "rating", "total_user_ratings", "lat", "lng"]

categorical_cols = [
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


def extract_review(reviews: list[dict]) -> list[str]:
    if reviews:
        return [" ".join(review["text"] for review in reviews)]
    return [""]


class UserInterestPredictor:
    def __init__(self):
        self.tfidf = TfidfVectorizer()
        self.kproto = KPrototypes(n_clusters=4, init="Cao", verbose=1)

    def predict(self, raw_data: List[dict], user_data: List[dict]):
        cluster_data = self.clustering(raw_data)
        
        # User like the restaurant -> get the cluster
        if user_data:
            place_id = user_data[0]["place_id"]
            filter_cluster = cluster_data[cluster.index == place_id]
            return filter_cluster
        else:  
            return cluster_data

    def clustering(self, clean_data):
        transformed_data = self.preprocess_data(clean_data)
        x_df = transformed_data.drop(columns=text_cols)
        X = x_df.values

        categorical_indices = [x_df.columns.get_loc(col) for col in categorical_cols]
        clusters = self.kproto.fit_predict(X, categorical=categorical_indices)
        transformed_data["cluster"] = clusters
        return transformed_data

    def preprocess_data(self, json_list: List[dict]):

        df = pd.DataFrame(json_list)
        df = self.one_hot_encode_types(df)
        df.index = df["place_id"].tolist()

        df["lat"] = df["location"].apply(lambda x: x["lat"])
        df["lng"] = df["location"].apply(lambda x: x["lng"])
        df["extened_reviews"] = df["reviews"].apply(lambda x: extract_review(x))

        df_clean = df.drop(columns=drop_cols, inplace=False).copy()
        bool_cols = df_clean.select_dtypes(include="boolean").columns
        df_clean[bool_cols] = df_clean[bool_cols].map(lambda x: 1 if x else 0)
        df_clean["price_level"] = df_clean["price_level"].map(
            lambda x: int(x) if x != "N/A" else 3
        )

        return df_clean

    def one_hot_encode_types(self, df: pd.DataFrame):
        types_set = set()
        df["types"].map(lambda x: types_set.update(x))
        new_cols = sorted(types_set)
        matrix = np.zeros((df.shape[0], len(new_cols)), dtype=int)

        for index, row in df.iterrows():
            for col in row["types"]:
                if col in new_cols:
                    matrix[index, new_cols.index(col)] = 1

        for i in range(len(new_cols)):
            df[new_cols[i]] = matrix[:, i]

        return df

    def postprocess_output(self, output):

        text_features = output[0]
        numeric_features = output[1]

        text_sim = cosine_similarity(text_features)

        # KMeans
        # num_dist = pairwise_distances(numeric_features, metric='euclidean')

        # KPrototypes
        clusters = self.kproto.fit_predict(numeric_features)

        # First cluster and then use summary and review to get the most similar

        # Use git reset to continue from the last commit
        num_sim = 1 / (1 + num_dist)

        return text_sim + num_sim


if __name__ == "__main__":
    # Example usage
    import json

    user_interest_predictor = UserInterestPredictor()

    with open(
        "/Users/kevinhsu/Documents/Hackathon-Tinder-Restaurant/restaurant_data.json",
        "r",
    ) as json_file:
        data = json.load(json_file)
    predictions = user_interest_predictor.predict(data, [])
    print(predictions)
