"""API Workflow:
    1. Request setting user ID and username into the database
    2. When need be, call the find_user() route to locate the existence of a user in the database(for log in purposes)
    3. Start sending data to the system at the end of each day via track_behavior
    4. After the new data has been processed and stored, call the pattern for the next given day via fetch_pattern
    5. During the day, for each pattern highlighted from fetch_pattern, call fetch_transfers on all websites the user visits
    6. When the user visits a website with an intense emissions rate, the function will enerate some alterantive websites that can then be sent to 
    frontend for the user to choose from 

    
"""

from src.track_behaviors import UpdateDB, FetchNext
from src.weekly_overview import GetWeekDetails
from src.use_DB import DBConnection
from src.get_alternatives import GenerateAlternatives
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

@app.route('/fetch-transfers', methods=["POST"])
def fetch_transfers(tolerance=0.8):
    data = request.get_json()
    user_id = data.get("user_id")
    website = data.get("url")
    transfer = data.get("data_transfer")

    evaluation = GenerateAlternatives(user_id, transfer)
    try:
        green_hosted =evaluation.is_green(website)
        emissions = evaluation.calculate_total_emissions(green_hosted)

        if emissions > tolerance:
            alternatives = evaluation.fetch_matches()
            if not alternatives:
                alternatives = evaluation.fetch_ai_response()
            
            return jsonify({
                "message": "Alternatives found",
                "alternatives": alternatives,
                "emissions": emissions,
                "green_hosted": green_hosted
            }), 200
    except:
        logger.error("Error calculating emissions or checking green hosting")
        return jsonify({"message": "Error processing emissions"}), 500


@app.route('/weekly-overview', methods=["POST"])
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
