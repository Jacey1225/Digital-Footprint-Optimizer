from src.user_integration import UserIntegration
from src.behaviors import TrackOverallBehavior
from flask import Flask, request, jsonify
import os
import logging
from dotenv import load_dotenv

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
    
@app.route('/add-behavior', methods=["POST"])
def add_behavior():
    data = request.get_json()
    user_id = data.get("user_id")
    behavior_data = data.get("behavior_data")
    
    behavior = TrackOverallBehavior(user_id)
    behavior.add_behavior(behavior_data)
    
    return jsonify({"message": "Behavior added successfully"}), 200