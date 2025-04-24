import pandas as pd
import numpy as np
import os
from typing import List

# Sklearn Packages
from sklearn.metrics.pairwise import cosine_similarity

# K-Prototypes
from kmodes.kprototypes import KPrototypes

# Import the config file
import config

from utils.helpers import Tools
tools = Tools()


class UserInterestPredictor:
    """
    A predictor model that clusters restaurants and predicts user interests
    based on their previous preferences.

    Uses K-Prototypes clustering algorithm to group similar restaurants and
    cosine similarity to rank recommendations.
    """

    def __init__(self):
        """
        Initialize the predictor with KPrototypes clustering algorithm.
        Using 4 clusters with Cao initialization method.
        """
        self.kproto = KPrototypes(n_clusters=4, init="Cao", verbose=1)

    def predict(self, cluster_data: pd.DataFrame, user_data: List[dict]):
        """
        Predicts restaurants that might interest a user based on their previous choices.

        Args:
            cluster_data (pd.DataFrame): Pre-clustered restaurant data
            user_data (List[dict]): User's previously liked restaurants

        Returns:
            pd.DataFrame: Filtered and ranked restaurant recommendations
        """
        # User like the restaurant -> get the cluster
        if user_data:
            place_ids = tools.extract_all_place_ids(user_data)
            # STEP 1: Find which cluster the user's liked restaurant belongs to
            target_label_dict = cluster_data[cluster_data["place_id"].isin(place_ids)][
                "cluster"
            ].value_counts().to_dict()

            # STEP 2: Filter restaurants from the same cluster (excluding the already liked one)
            filter_cluster = cluster_data[
                (cluster_data["cluster"].isin(target_label_dict.keys())) &
                (~cluster_data["place_id"].isin(place_ids))
            ]

            # STEP 3: Rank the filtered restaurants based on similarity
            rank_data = self.rank(filter_cluster, user_data)
            top_5_resataurants = tools.top_5_restaurants(
                rank_data, target_label_dict
            )
            return top_5_resataurants
        else:
            # If no user preferences exist, return all restaurants
            return cluster_data

    def clustering(self, clean_data):
        """
        Performs clustering on restaurant data to group similar restaurants.

        Args:
            clean_data (List[dict]): List of restaurant data dictionaries

        Returns:
            pd.DataFrame: Processed data with cluster assignments
        """
        # STEP 1: Preprocess the data for clustering
        processed_data = self.preprocess_data(clean_data)

        # STEP 2: Drop text columns that shouldn't be used for clustering
        features_df = processed_data.drop(columns=config.TEXT_COLUMNS)
        feature_matrix = features_df.values

        # STEP 3: Identify categorical features for K-Prototypes algorithm
        # K-Prototypes requires explicit identification of categorical features
        categorical_indices = [
            features_df.columns.get_loc(col) for col in config.CATEGORICAL_COLUMNS
        ]

        # STEP 4: Perform clustering
        cluster_labels = self.kproto.fit_predict(
            feature_matrix, categorical=categorical_indices
        )

        # STEP 5: Add place_id and cluster assignments back to the data
        processed_data["place_id"] = self.place_id_list
        processed_data["cluster"] = cluster_labels

        # Save the clustered data for later use
        os.makedirs("data", exist_ok=True)
        processed_data.to_csv("data/cluster_data.csv", index=False)
        return processed_data

    def preprocess_data(self, restaurant_data: List[dict]):
        """
        Preprocesses raw restaurant data for clustering.

        Performs one-hot encoding, extracts location coordinates,
        processes reviews, and handles special data types.

        Args:
            restaurant_data (List[dict]): Raw restaurant data

        Returns:
            pd.DataFrame: Processed data ready for clustering
        """
        # STEP 1: Convert json to DataFrame
        restaurant_df = pd.DataFrame(restaurant_data)

        # STEP 2: One-hot encode restaurant types
        restaurant_df = self.one_hot_encode_types(restaurant_df)

        # Store place_ids for later reference
        self.place_id_list = restaurant_df["place_id"].tolist()

        # STEP 3: Extract latitude and longitude from location
        restaurant_df["lat"] = restaurant_df["location"].apply(lambda x: x["lat"])
        restaurant_df["lng"] = restaurant_df["location"].apply(lambda x: x["lng"])

        # STEP 4: Process reviews into extended text
        restaurant_df["extended_reviews"] = restaurant_df["reviews"].apply(
            lambda x: tools.extract_review(x)
        )

        # STEP 5: Clean and transform the data
        df_clean = restaurant_df.drop(columns=config.DROP_COLUMNS, inplace=False).copy()

        # Convert boolean columns to integers (1/0)
        bool_cols = df_clean.select_dtypes(include="boolean").columns
        df_clean[bool_cols] = df_clean[bool_cols].map(lambda x: 1 if x else 0)

        # Handle missing price levels (N/A -> 3 as a default mid-range price)
        df_clean["price_level"] = df_clean["price_level"].map(
            lambda x: int(x) if x != "N/A" else 3
        )

        return df_clean

    def one_hot_encode_types(self, df: pd.DataFrame):
        """
        Performs one-hot encoding for restaurant types.

        Creates binary columns for each possible restaurant type
        (e.g., 'cafe', 'italian', etc.)

        Args:
            df (pd.DataFrame): Restaurant data

        Returns:
            pd.DataFrame: Data with one-hot encoded type columns
        """
        # STEP 1: Collect all unique restaurant types across all restaurants
        types_set = set()
        df["types"].map(lambda x: types_set.update(x))
        new_cols = sorted(types_set)

        # STEP 2: Create a binary matrix for one-hot encoding
        # This is more efficient than creating each column individually
        matrix = np.zeros((df.shape[0], len(new_cols)), dtype=int)

        # STEP 3: Fill the matrix with 1s where restaurants have the corresponding type
        for index, row in df.iterrows():
            for col in row["types"]:
                if col in new_cols:
                    matrix[index, new_cols.index(col)] = 1

        # STEP 4: Add the one-hot encoded columns to the dataframe
        for i in range(len(new_cols)):
            df[new_cols[i]] = matrix[:, i]

        return df

    def rank(self, data: pd.DataFrame, user_data: List[dict]):
        """
        Ranks restaurants based on similarity to user preferences.

        Uses cosine similarity between review embeddings to determine
        how similar restaurants are to the user's liked restaurants.

        Args:
            data (pd.DataFrame): Filtered restaurant data from the same cluster
            user_data (List[dict]): User's previously liked restaurants

        Returns:
            pd.DataFrame: Restaurants sorted by similarity to user preferences
        """
        cosine_similarity_list = []

        # STEP 1: Get embeddings from the reviews of the user's liked restaurant
        target_reviews = tools.extract_review(user_data)
        target_reviews_embedding = tools.get_vector(target_reviews)

        # STEP 2: Calculate similarity between target restaurant and each potential recommendation
        for reviews in data["extended_reviews"]:
            reviews_embedding = tools.get_vector(reviews)
            # Calculate cosine similarity between review embeddings
            # Higher value means more similar content
            cosine_similarity_list.append(
                cosine_similarity([target_reviews_embedding], [reviews_embedding])[0][0]
            )

        # STEP 3: Add similarity scores to the dataframe and sort
        data = data.copy()  # Create a copy to avoid SettingWithCopyWarning
        data["similarity"] = cosine_similarity_list

        # Return restaurants sorted by descending similarity (most similar first)
        return data.sort_values(by="similarity", ascending=False)


if __name__ == "__main__":
    # Example usage
    import json

    user_interest_predictor = UserInterestPredictor()

    with open(
        "/Users/kevinhsu/Documents/Hackathon-Tinder-Restaurant/restaurant_data.json",
        "r",
    ) as json_file:
        data = json.load(json_file)
    # Get the clustering data
    user_interest_predictor.clustering(data)
    cluster_data = pd.read_csv("data/cluster_data.csv").fillna("")
    predictions = user_interest_predictor.predict(cluster_data, data[0:5])
    print(predictions)
