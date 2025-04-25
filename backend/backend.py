from flask import Flask, request, jsonify, send_file, make_response
from services.google_map_search import GoogleMapSearch
from flask_cors import CORS
from utils.helpers import Tools
from utils.data_transport import FirebaseClient
from utils.session import Session
from services.restaurant_service import search_nearby_restaurants
from ml_model import UserInterestPredictor
import threading
import logging
import os

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173","http://127.0.0.1:5173"], supports_credentials=True)
session = Session()

gmaps = GoogleMapSearch()
last_info = {}
tools = Tools()
firebase_client = FirebaseClient()
model = UserInterestPredictor()

# Dummy user
USER = {
    'username': 'user',
    'password': 'pass'
}

@app.before_request
def before_request():
    """Perform actions before each request."""
    if request.endpoint in ['login', 'static', 'check-session']:  # Exclude login and static routes
        return  # Allow access to login and static files without session check

    session_id = request.cookies.get('session_id')
    if not session_id:
        logging.info("Session ID not found in cookie")
        return jsonify({'message': 'Not authenticated'}), 401

    session_data = session.get_session_data(session_id)
    if not session_data:
        logging.info(f"Invalid session ID: {session_id}")
        return jsonify({'message': 'Invalid session. Please log in.'}), 401
    
@app.route('/check-session', methods=['GET'])
def check_session():
    """Check if the user has a valid session."""
    session_id = request.cookies.get('session_id')
    if not session_id:
        logging.info("Session ID not found in cookie")
        return jsonify({'message': 'Not authenticated'}), 401
    session_data = session.get_session_data(session_id)
    if session_data:
        logging.info(f"Session is valid")
        return jsonify({'message': 'Session is valid'}), 200
    else:
        logging.info("Session is invalid or expired")
        return jsonify({'message': 'Not authenticated'}), 401

@app.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    data = request.get_json()
    if data['username'] == USER['username'] and data['password'] == USER['password']:
        session_id = session.create_session(data['username'])
        response = jsonify({'message': 'Login successful'})
        response.set_cookie('session_id', session_id, httponly=True, samesite='Lax')
        return response, 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """Handle user logout."""
    session_id = request.cookies.get('session_id')
    if session_id:
        session.delete_session(session_id)
        response = jsonify({'message': 'Logged out'})
        response.delete_cookie('session_id')
        return response, 200
    return jsonify({'message': 'No session to log out from'}), 200

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
    return jsonify({"results": results}), 200


@app.route("/suggestion", methods=["POST"])
def get_suggestion():
    response = make_response("Creating suggestions", 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    if request.method == 'OPTIONS':
        return response
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
