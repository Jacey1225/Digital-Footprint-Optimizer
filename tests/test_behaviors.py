import logging
import mysql.connector
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.behaviors import TrackOverallBehavior, DailyBehavior

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Test configuration
TEST_USER_ID = "test_user"
TEST_PASSWORD = "test_password"
TEST_DB_CONFIG = {
    "host": "localhost",
    "user": "jaceysimpson",
    "password": "WeLoveDoggies16!",
    "database": "userInfo",
    "port": 3306
}

def test_behavior_tracking():
    logging.info("Starting test for behavior tracking...")

    # Step 1: Initialize TrackOverallBehavior
    behavior_tracker = TrackOverallBehavior(TEST_USER_ID, TEST_PASSWORD, TEST_DB_CONFIG)
    logging.info("Initialized TrackOverallBehavior.")

    default_current_pattern = [[0, 2], [4, 6], [8, 10]]  # Example default pattern
    insert_query = f"""
    INSERT INTO `{TEST_USER_ID}` (day, currentPattern, history)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE currentPattern = VALUES(currentPattern);
    """
    behavior_tracker.cursor.execute(
        insert_query,
        (behavior_tracker.week_day, json.dumps(default_current_pattern), json.dumps([]))
    )
    behavior_tracker.connection.commit()
    logging.info(f"Inserted default current pattern into the database: {default_current_pattern}")


    # Step 2: Add a daily behavior
    daily_hours = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.1, 0.2, 0.3, 0.4]
    daily_behavior = DailyBehavior(TEST_USER_ID, daily_hours)
    daily_behavior.average_spikes()
    clusters = daily_behavior.kmeans_spikes()
    logging.info(f"Daily behavior spikes detected: {daily_behavior.activity_spikes}")
    logging.info(f"Clusters formed: {clusters}")

    # Step 3: Add behavior to the database
    behavior_tracker.add_behavior(daily_behavior)
    logging.info("Added daily behavior to the database.")

    # Step 4: Update behavior with a new daily pattern
    new_daily_pattern = [[2, 4], [10, 12], [18, 20]]
    behavior_tracker.update_behavior(new_daily_pattern)
    logging.info("Updated behavior with a new daily pattern.")

    # Step 5: Verify the updated behavior
    verify_query = f"SELECT currentPattern FROM `{TEST_USER_ID}` WHERE day = %s"
    behavior_tracker.cursor.execute(verify_query, (behavior_tracker.week_day,))
    updated_pattern = behavior_tracker.cursor.fetchone()
    logging.info(f"Updated pattern in the database: {updated_pattern}")

    # Step 6: Clean up - Drop the test table
    drop_table_query = f"DROP TABLE IF EXISTS `{TEST_USER_ID}`"
    behavior_tracker.cursor.execute(drop_table_query)
    behavior_tracker.connection.commit()
    logging.info(f"Test table `{TEST_USER_ID}` dropped successfully.")

    # Close the database connection
    behavior_tracker.cursor.close()
    behavior_tracker.connection.close()
    logging.info("Database connection closed.")

if __name__ == "__main__":
    test_behavior_tracking()