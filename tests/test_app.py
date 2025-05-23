import unittest
import json
import logging
from app import app  # Ensure this imports your Flask app

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestTrackBehavior(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_track_behavior_with_daily_hours(self):
        # Define the test data
        daily_hours = [
            0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8,
            0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0, 0.9, 0.8, 0.7, 0.6
        ]
        data = {
            "user_id": "test_user_id",
            "daily_hours": daily_hours
        }

        # Make a POST request to the /track-behavior route
        response = self.app.post(
            '/track-behavior',
            data=json.dumps(data),
            content_type='application/json'
        )

        # Log the response
        logger.info("Received response: %s", response.json)

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"message": "Behavior added successfully"})

if __name__ == '__main__':
    unittest.main()