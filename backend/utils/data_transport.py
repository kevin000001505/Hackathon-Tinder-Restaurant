import os
import sys, logging, time
from typing import List

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

collections = config.FIREBASE_COLLECTION


class FirebaseClient:
    def __init__(self):
        self.db = None
        self.initialize_firebase()

    def initialize_firebase(self):
        """Initialize Firebase app with credentials"""
        # Path to your Firebase service account key JSON file
        cred_path = config.FIREBASE_ACCOUNT_KEY

        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

    def upload_data(self, data: List[dict], user_id=None, max_retries=3, retry_delay=1):
        """Upload data to Firebase with retry logic for SSL errors"""
        attempt = 0
        while attempt < max_retries:
            try:
                # Your existing upload code
                doc_ref = (
                    self.db.collection("restaurants").document(user_id)
                    if user_id
                    else self.db.collection("restaurants").document()
                )
                doc_ref.set({
                    "restaurant_data": data,
                    "timestamp": firestore.SERVER_TIMESTAMP
                }, merge=True)
                return doc_ref.id
            except Exception as e:
                if isinstance(e, SSLError) or "SSL" in str(e):
                    attempt += 1
                    if attempt < max_retries:
                        logging.warning(f"SSL error, retrying ({attempt}/{max_retries}): {str(e)}")
                        time.sleep(retry_delay)
                        continue
                logging.error(f"Firebase upload error: {str(e)}")
                raise

    def get_data(self, user_id=None):
        """
        Get restaurant data from Firebase for a specific user
        
        Args:
            user_id (str): The user ID to retrieve data for
            
        Returns:
            List[dict]: The restaurant data or None if not found
        """
        if not user_id:
            logging.warning("No user_id provided to get_data method")
            return None
        
        try:
            doc_ref = self.db.collection("restaurants").document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                if data and "restaurant_data" in data:
                    return data["restaurant_data"]
                else:
                    logging.warning(f"Document exists for user {user_id} but no restaurant_data found")
                    return []
            else:
                logging.warning(f"No document found for user_id: {user_id}")
                return None
        except Exception as e:
            logging.error(f"Error retrieving data from Firebase: {str(e)}")
            return None


