from src.track_behaviors import UpdateDB, FetchNext
from src.weekly_overview import GetWeekDetails
from src.use_DB import DBConnection
from flask import Flask, request, jsonify
from flask.views import MethodView
import os
import logging
from dotenv import load_dotenv
import mysql.connector

app = Flask(__name__)
logger = logging.getLogger(__name__)
GEMAPI = load_dotenv()


@app.route('/set-user', methods=["POST"])
def set_user():
    data = request.get_json()
    user_id = data.get("user_id")
    username = data.get("username")
    
    db_functions = DBConnection("users")

    where_values = ["userID", 'user']
    values = [user_id, username]
    db_functions.insert_items(where_values, values)

    return jsonify({"user_id": user_id}), 200
    
@app.route('/find-user', methods=["POST"])
def find_user():
    data = request.get_json()
    user_id = data.get("user_id")
    user = data.get("username")
    
    db_functions = DBConnection("users")
    select_value = "user"
    where_values = ["userID"]
    values = [user_id]
    user_data = db_functions.select_items(select_value, where_values, values, False)
    
    if user_data is not None:
        return jsonify({"user_data": user_data}), 200
    else:
        return jsonify({"message": "User not found"}), 404

@app.route('/track-behavior', methods=["GET", "POST"])
def track_behavior():
    data = request.get_json()
    user_id = data.get("user_id")
    daily_hours = data.get("daily_hours")
    try:
        behavior = UpdateDB(user_id, daily_hours)
        logger.info(f"Daily Hours Input: {daily_hours}")
    except Exception as e:
        logger.info(f"Error initializing UpdateDB: {e}")
        return jsonify({"message": "Error initializing UpdateDB"}), 500

    try:
        behavior.detect_spikes()
    except Exception as e:
        logger.info(f"Error detecting spikes: {e}")
        return jsonify({"message": "Error detecting spikes"}), 500
    else:
        behavior.get_current_pattern()
        behavior.get_updated_pattern()
        behavior.update_db()
        behavior.close()
    
    return jsonify({"message": "Behavior added successfully"}), 200

@app.route('/fetch-pattern', methods=["POST"])
def fetch_pattern():
    data = request.get_json()
    user_id = data.get("user_id")
    pattern_obj = FetchNext(user_id)

    pattern = pattern_obj.get_next_pattern()
    return jsonify({
        "message": "Tracker initialized successfully",
        "pattern": pattern}), 200

@app.route('/weekly-overview', methods={"GET", "POST"})
def weekly_overview():
    data = request.get_json()
    user_id = data.get("user_id")
    weekly_data = GetWeekDetails()
    last_7_items = weekly_data.get_weekly_data()

    if last_7_items:
        return jsonify({"weekly_data": last_7_items}), 200
    else:
        return jsonify({"message": "No data found"}), 404

@app.route('/insert-web-data', methods=["POST"])
def insert_web_data():
    data = request.get_json()
    user_id = data.get("user_id")
    website = data.get("root")
    transfer = data.get("footprint")
    suggestion1 = data.get("suggestion1")
    suggestion2 = data.get("suggestion2")
    suggestion3 = data.get("suggestion3")

    web_data = GetWeekDetails()
    where_values = ["userID", "website", "transfer", "suggestion1", "suggestion2", "suggestion3"]
    values = [
        user_id,
        website,
        transfer,
        suggestion1,
        suggestion2,
        suggestion3
    ]
    web_data.insert_web_data(where_values, values)
    return jsonify({"message": "Web data inserted successfully"}), 200
