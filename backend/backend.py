from flask import Flask, request, jsonify, send_file
from services.google_map_search import GoogleMapSearch
from flask_cors import CORS
from utils.helpers import Tools
from utils.data_transport import FirebaseClient
from services.restaurant_service import search_nearby_restaurants
from ml_model import UserInterestPredictor
import threading
import logging
import os

app = Flask(__name__)
gmaps = GoogleMapSearch()
last_info = {}
CORS(app)
tools = Tools()
firebase_client = FirebaseClient()
model = UserInterestPredictor()


@app.route("/search", methods=["GET"])
def search_restaurants():
    global last_info
    address = request.args.get("address")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius = request.args.get("radius", default=10000, type=int)
    next_page_token = None
    user_id = request.args.get("user_id", type=str, default=None)

    # Get the first batch of results
    results, next_page_token, status_code, error = search_nearby_restaurants(
        address=address,
        lat=lat,
        lng=lng,
        radius=radius,
        next_page_token=next_page_token,
        last_info=last_info,
    )
    
    if error:
        return jsonify({"error": error}), status_code
    
    # Start background processing for remaining pages and clustering
    def background_processing():
        try:
            all_data = results.copy()  # Start with the first batch
            
            # Fetch remaining pages
            current_next_page_token = next_page_token
            while current_next_page_token:
                more_results, current_next_page_token, _, _ = search_nearby_restaurants(
                    address=address,
                    lat=lat,
                    lng=lng,
                    radius=radius,
                    next_page_token=current_next_page_token,
                    last_info=last_info,
                )
                all_data.extend(more_results)
            
            # Process clustering after all data is collected
            if all_data:
                label_data_df = model.clustering(all_data)
                label_data_dict = label_data_df.to_dict(orient="records")
                firebase_client.upload_data(label_data_dict, user_id=user_id)
                logging.info(
                    f"Successfully uploaded clustering data for user {user_id}"
                )
        except Exception as e:
            logging.error(f"Error in background processing: {str(e)}")

    # Start the background thread if we have both results and more pages
    if results and next_page_token:
        threading.Thread(target=background_processing).start()
    # Even if there's no next page, run clustering on initial results
    elif results:
        def process_initial_results():
            try:
                label_data_df = model.clustering(results)
                label_data_dict = label_data_df.to_dict(orient="records")
                firebase_client.upload_data(label_data_dict, user_id=user_id)
                logging.info(
                    f"Successfully uploaded clustering data for user {user_id}"
                )
            except Exception as e:
                logging.error(f"Error in processing initial results: {str(e)}")
        
        threading.Thread(target=process_initial_results).start()

    # Return the first batch of results immediately
    return jsonify({"results": results}), status_code


@app.route("/suggestion", methods=["POST"])
def get_suggestion():
    try:
        data = request.json
        app.logger.info(f"Received data: {data}")
        
        # Get user liked restaurant IDs
        like_place_id = data.get("like_place_id", [])
        dislike_place_id = data.get("dislike_place_id", [])
        user_id = data.get("user_id")
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
            
        cluster_data = firebase_client.get_data(user_id=user_id)
        
        if not cluster_data:
            return jsonify({"error": "No data found for user"}), 404

        suggestion = model.predict(cluster_data, like_place_id, dislike_place_id)
        return jsonify({"suggestion": suggestion.to_dict(orient="records")}), 200
    except Exception as e:
        app.logger.error(f"Error in get_suggestion: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/photos/<place_id>/<photo_id>")
def get_photos(place_id, photo_id):
    return send_file(
        os.path.join("photos", place_id, photo_id + ".jpg"), mimetype="image/jpeg"
    )


if __name__ == "__main__":
    app.run(debug=True)
