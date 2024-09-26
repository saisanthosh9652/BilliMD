from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['demo']
    users_collection = db['user']
except Exception as e:
    logging.error(f"Error connecting to MongoDB: {e}")
    users_collection = None

DB_UNAVAILABLE = "Database is not available"

def update_user_in_db(user_id, first_name, password, updated_datetime):
    if users_collection is None:
        raise ConnectionError(DB_UNAVAILABLE)
    
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {
            "first_name": first_name,
            "password": password,
            "updated_datetime": updated_datetime
        }}
    )
    return result.matched_count > 0

@app.before_request
def log_request_info():
    headers = {key: value for key, value in request.headers.items()}
    logging.info(f"HTTP Headers: {headers}")

@app.route('/user', methods=['PUT'])
def update_user():
    try:
        logging.info("Received a PUT request")
        auth_header = request.headers.get('Authorization')
        session_token = request.headers.get('X-Session-Token') or request.headers.get('session_token')

        if auth_header != "Bearer laurhln7t4gkhlnfsp7ywho_hlsfl" or session_token != "rbvkur79jksfu_shjhu":
            return jsonify({"Status": "failure", "reason": "Unauthorized"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"Status": "failure", "reason": "Invalid JSON input"}), 400

        user_id = data.get('user_id')
        first_name = data.get('first_name')
        password = data.get('password')
        updated_datetime = data.get('updated_datetime')

        if not all([user_id, first_name, password, updated_datetime]):
            return jsonify({"Status": "failure", "reason": "Missing required fields"}), 400

        try:
            updated_datetime = datetime.datetime.fromisoformat(updated_datetime.rstrip('Z'))
        except ValueError:
            return jsonify({"Status": "failure", "reason": "Invalid datetime format"}), 400

        user_updated = update_user_in_db(user_id, first_name, password, updated_datetime)

        if user_updated:
            return jsonify({"Status": "success"}), 200
        else:
            return jsonify({"Status": "failure", "reason": "User not found"}), 404

    except ConnectionError as ce:
        logging.error(f"Database error: {ce}")
        return jsonify({"Status": "failure", "reason": DB_UNAVAILABLE}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"Status": "failure", "reason": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
