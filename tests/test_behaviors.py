import pytest
import logging
import random
import json
from datetime import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.behaviors import DailyBehavior, TrackOverallBehavior, CONFIG
import mysql.connector
from mysql.connector import Error

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Test database setup
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_password"

@pytest.fixture(scope="module")
def db_connection():
    """Fixture to set up and tear down the test database connection."""
    try:
        connection = mysql.connector.connect(**CONFIG)
        cursor = connection.cursor()
        # Create a test table for the user
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS `{TEST_USER_ID}` (
            day VARCHAR(255) PRIMARY KEY,
            currentPattern TEXT,
            history TEXT
        );
        """)
        connection.commit()
        yield connection
    finally:
        # Clean up: Drop the test table after tests
        cursor.execute(f"DROP TABLE IF EXISTS `{TEST_USER_ID}`;")
        connection.commit()
        connection.close()

def generate_mock_data():
    """Generate mock data for testing."""
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    data = {}
    for day in days_of_week:
        # Generate a 2D list where each item is a range from 1-24
        pattern = [[random.randint(1, 12), random.randint(13, 24)] for _ in range(3)]
        # Generate a mock list of 24 items ranging from 0-1 (activity percentages)
        activity_percentages = [round(random.uniform(0, 1), 2) for _ in range(24)]
        data[day] = {"pattern": pattern, "activity_percentages": activity_percentages}
    return data

def test_behavior_processing(db_connection):
    """Test the behavior processing functions."""
    mock_data = generate_mock_data()
    behavior_tracker = TrackOverallBehavior(TEST_USER_ID, TEST_PASSWORD, CONFIG)

    for day, data in mock_data.items():
        # Set the current day for testing
        behavior_tracker.week_day = day

        # Create a DailyBehavior instance
        daily_behavior = DailyBehavior(
            user_id=TEST_USER_ID,
            daily_hours=data["activity_percentages"],
            db_config=CONFIG
        )

        # Process the activity percentages
        daily_behavior.average_spikes()
        clusters = daily_behavior.kmeans_spikes()
        daily_behavior.set_pattern(clusters)

        # Log the results
        logging.info(f"Day: {day}")
        logging.info(f"Activity Percentages: {data['activity_percentages']}")
        logging.info(f"Detected Spikes: {daily_behavior.activity_spikes}")
        logging.info(f"Clusters: {clusters}")
        logging.info(f"Current Pattern: {daily_behavior.current_pattern}")

        # Add the behavior to the database
        behavior_tracker.add_behavior(daily_behavior.current_pattern, data["pattern"])

    # Verify the data in the database
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM `{TEST_USER_ID}`;")
    rows = cursor.fetchall()
    assert len(rows) == 7  # Ensure all 7 days of data were added

    for row in rows:
        day, current_pattern, history = row
        logging.info(f"Database Entry - Day: {day}, Current Pattern: {current_pattern}, History: {history}")
        assert day in mock_data
        assert json.loads(current_pattern) is not None
        assert json.loads(history) == mock_data[day]["pattern"]