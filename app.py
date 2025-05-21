from src.user_integration import UserIntegration
from src.track_behaviors import UpdateDB, FetchNext
from flask import Flask, request, jsonify
from flask.views import MethodView
import os
import logging
from dotenv import load_dotenv
import mysql.connector

app = Flask(__name__)
GEMAPI = load_dotenv()


@app.route('/set-user', methods=["POST"])
def set_user():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    
    user = UserIntegration(username, email, password)
    user_id = user.generate_random_id()
    user.create_table(user_id)
    
    return jsonify({"user_id": user_id}), 200
    
@app.route('/find-user', methods=["POST"])
def find_user():
    data = request.get_json()
    user_id = data.get("user_id")
    
    user = UserIntegration(user_id)
    user_data = user.user_exists()
    
    if user_data:
        return jsonify({"user_data": user_data}), 200
    else:
        return jsonify({"message": "User not found"}), 404
    
INFO_CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies!'),
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo')
}
SUGGESTION_CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies!'),
    "database": os.environ.get('MYSQL_DATABASE', 'website_tracker')
}

@app.route('/track-behavior', methods=["POST"])
def track_behavior(self):
    data = request.get_json()
    user_id = data.get("user_id")
    daily_hours = data.get("daily_hours")

    behavior = UpdateDB(user_id, daily_hours)
    behavior.detect_spikes()
    behavior.get_current_pattern()
    behavior.get_updated_pattern()
    behavior.update_db()

    return jsonify({"message": "Behavior added successfully"}), 200

@app.route('/fetch-pattern', methods=["POST"])
def fetch_pattern(self):
    data = request.get_json()
    user_id = data.get("user_id")
    pattern_obj = FetchNext(user_id)

    pattern = pattern_obj.get_current_pattern()
    return jsonify({
        "message": "Tracker initialized successfully",
        "pattern": pattern}), 200