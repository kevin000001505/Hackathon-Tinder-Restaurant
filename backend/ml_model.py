import pandas as pd
import numpy as np
import logging
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

    def predict(
        self, cluster_data: List[dict], like_place_id: list, dislike_place_id: list
    ):
        """
        Predicts restaurants that might interest a user based on their previous choices.

        This function works by:
        1. Converting input data to a DataFrame
        2. Creating a weighted scoring system based on cluster preferences
        3. Adjusting weights based on liked/disliked restaurants
        4. Ranking remaining restaurants using the weighted scores

        Args:
            cluster_data (List[dict]): Pre-clustered restaurant data
            like_place_id (list): List of restaurant IDs the user has liked
            dislike_place_id (list): List of restaurant IDs the user has disliked

        Returns:
            pd.DataFrame: Sorted restaurant recommendations with ranking scores
        """
        cluster_data = pd.DataFrame(cluster_data)
        cluster_weights_dict = {
            str(cluster): 0 for cluster in cluster_data["cluster"].unique()
        }
        if like_place_id:
            like_cluster_values_counts = (
                tools.get_place_id_data(data=cluster_data, place_id_list=like_place_id)[
                    "cluster"
                ]
                .value_counts()
                .to_dict()
            )
            for cluster, count in like_cluster_values_counts.items():
                cluster_weights_dict[str(cluster)] = count

        if dislike_place_id:
            dislike_cluster_values_counts = (
                tools.get_place_id_data(
                    data=cluster_data, place_id_list=dislike_place_id
                )["cluster"]
                .value_counts()
                .to_dict()
            )
            for cluster, count in dislike_cluster_values_counts.items():
                cluster_weights_dict[str(cluster)] -= count

        # STEP 3: Rank the filtered restaurants based on similarity
        rank_data = self.rank(
            cluster_data, cluster_weights_dict, like_place_id, dislike_place_id
        )
        return rank_data

    def clustering(self, restaurants_data: List[dict]) -> pd.DataFrame:
        """
        Performs clustering on restaurant data to group similar restaurants.

        The clustering process involves:
        1. Data preprocessing (one-hot encoding, feature extraction)
        2. Feature selection by dropping text columns
        3. Identifying categorical features for K-Prototypes
        4. Applying K-Prototypes clustering algorithm
        5. Assigning cluster labels to restaurants

        Args:
            restaurants_data (List[dict]): Raw restaurant data containing features

        Returns:
            pd.DataFrame: Original data with added cluster assignments
        """
        # STEP 1: Preprocess the data for clustering
        restaurant_df = pd.DataFrame(restaurants_data)
        processed_data = self.preprocess_data(restaurant_df)

        # STEP 2: Drop text columns that shouldn't be used for clustering
        features_df = processed_data.drop(columns=config.TEXT_COLUMNS)
        feature_matrix = features_df.values

        # STEP 3: Identify categorical features for K-Prototypes algorithm
        # K-Prototypes requires explicit identification of categorical features
        categorical_indices = [
            features_df.columns.get_loc(col)
            for col in config.CATEGORICAL_COLUMNS
            if col in features_df.columns
        ]
        # STEP 4: Perform clustering
        cluster_labels = self.kproto.fit_predict(
            feature_matrix, categorical=categorical_indices
        )

        # STEP 5: Add place_id and cluster assignments back to the data
        restaurant_df["cluster"] = cluster_labels
        logging.info(f"Clustering completed with {len(set(cluster_labels))} clusters.")

        return restaurant_df

    def preprocess_data(self, restaurant_df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocesses raw restaurant data for clustering analysis.

        Preprocessing steps include:
        1. One-hot encoding of restaurant types
        2. Storing place IDs for reference
        3. Extracting geographic coordinates
        4. Processing text reviews
        5. Cleaning data types (converting boolean to int, handling NA values)
        6. Dropping unnecessary columns

        Args:
            restaurant_df (pd.DataFrame): Raw restaurant data frame

        Returns:
            pd.DataFrame: Cleaned and processed data ready for clustering
        """

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
            lambda x: int(float(x)) if x != "N/A" else 3
        )
        # Replace N/A with medium rating (3)
        df_clean["rating"] = df_clean["rating"].map(
            lambda x: float(x) if x != "N/A" else 3
        )

        return df_clean

    def one_hot_encode_types(self, df: pd.DataFrame):
        """
        Creates binary features for each restaurant type using one-hot encoding.

        The encoding process:
        1. Collects all unique restaurant types from the dataset
        2. Creates a binary matrix for efficient encoding
        3. Sets values to 1 where a restaurant has a specific type
        4. Adds encoded columns to the original dataframe

        Args:
            df (pd.DataFrame): Restaurant data with 'types' column containing lists

        Returns:
            pd.DataFrame: Original data with added binary type columns
        """
        # STEP 1: Collect all unique restaurant types across all restaurants
        types_set = set()
        df["types"].map(lambda x: types_set.update(x))
        new_cols = sorted(types_set)

        # STEP 2: Create a binary matrix for one-hot encoding
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

    def rank(
        self,
        data: pd.DataFrame,
        cluster_weights_dict: dict,
        like_place_id: list,
        dislike_place_id: list,
    ) -> pd.DataFrame:
        """
        Ranks restaurants based on user preferences and similarity scores.

        Ranking process:
        1. Calculates text similarity between restaurant reviews
        2. Considers both positive (liked) and negative (disliked) preferences
        3. Applies cluster weights based on user history
        4. Combines similarity scores with cluster weights
        5. Sorts restaurants by final composite score

        Args:
            data (pd.DataFrame): Restaurant dataset with clusters
            cluster_weights_dict (dict): Weight for each cluster based on preferences
            like_place_id (list): IDs of liked restaurants
            dislike_place_id (list): IDs of disliked restaurants

        Returns:
            pd.DataFrame: Sorted restaurants with similarity and ranking scores
        """
        # Initialize similarity score lists for both liked and disliked restaurants
        like_cosine_similarity_list = []
        dislike_cosine_similarity_list = []

        # Extract subsets of data for liked and disliked restaurants
        like_data = tools.get_place_id_data(data, like_place_id)
        dislike_data = tools.get_place_id_data(data, dislike_place_id)

        # FILTERING STEP: Remove restaurants that the user has already rated
        filter_data = data[~data["place_id"].isin(like_place_id + dislike_place_id)]

        # EMBEDDING GENERATION: Create text embeddings from concatenated reviews
        like_reviews = like_data["extended_reviews"].str.cat(sep=" ")
        like_reviews_embedding = tools.get_vector(like_reviews)

        dislike_reviews = dislike_data["extended_reviews"].str.cat(sep=" ")
        dislike_reviews_embedding = tools.get_vector(dislike_reviews)

        # SIMILARITY CALCULATION: Compute similarity scores for each candidate restaurant
        for reviews in filter_data["extended_reviews"]:
            reviews_embedding = tools.get_vector(reviews)

            # Calculate positive similarity (to liked restaurants)
            # Higher values indicate stronger match to user preferences
            like_cosine_similarity_list.append(
                cosine_similarity([like_reviews_embedding], [reviews_embedding])[0][0]
            )

            # Calculate negative similarity (to disliked restaurants)
            # Higher values indicate similarity to what user dislikes
            dislike_cosine_similarity_list.append(
                cosine_similarity([dislike_reviews_embedding], [reviews_embedding])[0][
                    0
                ]
            )

        # Create a copy to avoid pandas warning
        filter_data = filter_data.copy()
        # SCORE COMPUTATION: Calculate net similarity score
        # Subtracting dislike similarity from like similarity to balance preferences
        filter_data["similarity"] = (
            np.array(like_cosine_similarity_list) * 100
            - np.array(dislike_cosine_similarity_list) * 100
        ).tolist()

        # Store individual similarity components for analysis
        filter_data["positive_similarity"] = like_cosine_similarity_list
        filter_data["negative_similarity"] = dislike_cosine_similarity_list

        # FINAL RANKING: Combine cluster weights with similarity scores
        # This creates a composite score that considers both content similarity
        # and cluster-based user preference patterns
        filter_data["final_score"] = (
            filter_data["cluster"].astype(str).map(cluster_weights_dict)
            + filter_data["similarity"]
        )

        return filter_data.sort_values(by="final_score", ascending=False)
