import pytest
from unittest.mock import MagicMock

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.behaviors import DailyBehavior, TrackOverallBehavior
import json
import logging
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_behavior_tracker():
    # Mock database configuration
    mock_db_config = {
        "host": "localhost",
        "user": "jaceysimpson",
        "password": "WeLoveDoggies16!",
        "database": "userInfo"
    }
    logger.info("Mock database configuration created: %s", mock_db_config)

    # Mock user ID and password
    user_id = "test_user_id"
    password = "test_password"
    logger.info("Mock user credentials set: user_id=%s", user_id)

    # Create a TrackOverallBehavior instance
    behavior_tracker = TrackOverallBehavior(user_id, password, mock_db_config)
    logger.info("TrackOverallBehavior instance created.")

    # Mock the database cursor and connection
    behavior_tracker.cursor = MagicMock()
    behavior_tracker.connection = MagicMock()
    logger.info("Mock database cursor and connection initialized.")

    return behavior_tracker

@pytest.fixture
def mock_daily_behavior():
    # Create a DailyBehavior instance
    user_id = "test_user_id"
    password = "test_password"
    logger.info("Creating DailyBehavior instance with user_id=%s", user_id)
    daily_behavior = DailyBehavior(user_id, password)

    # Mock activity spikes data (2D array)
    daily_behavior.activity_spikes = [
        [1, 5], [6, 10], [15, 20], [21, 25]
    ]
    logger.info("Mock activity spikes data set: %s", daily_behavior.activity_spikes)

    return daily_behavior

def test_kmeans_pattern(mock_behavior_tracker, mock_daily_behavior): 
    # Combine mock activity spikes data
    kmean_data = mock_daily_behavior.activity_spikes
    logger.info("Mock activity spikes data combined for kmeans_pattern: %s", kmean_data)

    # Call the kmeans_pattern function
    clusters = mock_behavior_tracker.kmeans_pattern(kmean_data)
    logger.info("kmeans_pattern function called. Clusters returned: %s", clusters)

    # Assert that clusters are returned
    assert isinstance(clusters, dict)
    assert len(clusters) > 0
    logger.info("Assertions passed: clusters is a dictionary and contains data.")

def test_set_new_pattern(mock_behavior_tracker):
    # Mock clusters data
    clusters = {
        0: [[1, 5], [6, 10]],
        1: [[15, 20], [21, 25]]
    }
    logger.info("Mock clusters data created: %s", clusters)

    # Call the set_new_pattern function
    new_pattern = mock_behavior_tracker.set_new_pattern(clusters)
    logger.info("set_new_pattern function called. New pattern returned: %s", new_pattern)

    # Assert that a new pattern is returned
    assert isinstance(new_pattern, list)
    assert len(new_pattern) == len(clusters)
    logger.info("Assertions passed: new_pattern is a list and matches the number of clusters.")

def test_update_behavior(mock_behavior_tracker, mock_daily_behavior):
    # Mock daily pattern
    daily_pattern = mock_daily_behavior.activity_spikes
    logger.info("Mock daily pattern set: %s", daily_pattern)

    # Mock database query results
    mock_behavior_tracker.cursor.fetchone.return_value = [
        "test_day",
        json.dumps([[1, 5], [6, 10]]),  # currentPattern
        json.dumps([[15, 20], [21, 25]])  # history
    ]
    logger.info("Mock database query results set: %s", mock_behavior_tracker.cursor.fetchone.return_value)

    # Call the update_behavior function
    logger.info("Calling update_behavior function with daily_pattern: %s", daily_pattern)
    result = mock_behavior_tracker.update_behavior(daily_pattern)
    logger.info("update_behavior function executed. Result: %s", result)

    # Assert that the function executes without errors
    assert result is None or isinstance(result, str)
    logger.info("Assertions passed: result is None or a string.")