import spacy
import numpy as np
from typing import List

embedding = spacy.load("en_core_web_lg")


def extract_review(reviews: List[dict]) -> str:
    if reviews:
        raw_reviews = " ".join(review["text"] for review in reviews)
        return raw_reviews.replace("\\n", " ").replace("\n", " ")
    return ""


def get_vector(texts: List[str]) -> np.ndarray:
    if texts:
        return embedding(texts).vector
    return np.zeros(embedding.vocab.vectors.shape[1])
