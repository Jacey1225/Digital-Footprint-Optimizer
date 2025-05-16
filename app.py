from src.user_integration import UserIntegration
from src.behaviors import DailyBehavior, TrackOverallBehavior
from flask import Flask, request, jsonify
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
class TrackWeekDetails:
    def __init__(self, info_config=INFO_CONFIG, suggestion_config=SUGGESTION_CONFIG):
        self.info_config = info_config
        self.suggestion_config = suggestion_config
        self.info_connection = mysql.connector.connect(**info_config)
        self.suggestion_connection = mysql.connector.connect(**suggestion_config)
        self.info_cursor = self.info_connection.cursor()
        self.suggestion_cursor = self.suggestion_connection.cursor()


class HandlePatterns:
    def __init__(self):
        data = request.get_json()
        self.user_id = data.get("user_id")
        self.daily_report = data.get("daily_report")
        self.behavior = TrackOverallBehavior(self.user_id)
    
    @app.route('/track-behavior', methods=["POST"])
    def track_behavior(self):
        data = request.get_json()
        user_id = data.get("user_id")
        daily_report = data.get("daily_report")
        behavior_data = DailyBehavior(user_id, daily_report)
        behavior_data.average_spikes()
        clusters = behavior_data.kmeans_spikes()
        behavior_data.set_pattern(clusters)
        
        self.behavior.update_behavior(behavior_data.current_pattern)
        
        return jsonify({"message": "Behavior added successfully"}), 200