import unittest
import json
import logging
from unittest.mock import patch
from app import app  # Ensure this imports your Flask app

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestFetchTransfers(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('src.get_alternatives.GenerateAlternatives')
    def test_fetch_transfers_success(self, MockGenerateAlternatives):
        """
        Test the /fetch-transfers endpoint for a successful response.
        """
        logger.info("Testing /fetch-transfers endpoint (success case)")

        # Mock the behavior of GenerateAlternatives
        mock_instance = MockGenerateAlternatives.return_value
        mock_instance.is_green.return_value = True
        mock_instance.calculate_total_emissions.return_value = 0.9
        mock_instance.fetch_matches.return_value = ["example1.com", "example2.com"]

        # Define the test data
        test_data = {
            "user_id": "1234",
            "url": "example.com",
            "data_transfer": 500
        }

        # Make a POST request to the /fetch-transfers endpoint
        response = self.app.post(
            '/fetch-transfers',
            data=json.dumps(test_data),
            content_type='application/json'
        )

        # Log the response
        logger.info("Received response: %s", response.json)

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertIn("alternatives", response.json)
        self.assertEqual(response.json["alternatives"], ["example1.com", "example2.com"])
        self.assertIn("emissions", response.json)
        self.assertEqual(response.json["emissions"], 0.9)

    @patch('src.get_alternatives.GenerateAlternatives')
    def test_fetch_transfers_failure(self, MockGenerateAlternatives):
        """
        Test the /fetch-transfers endpoint for a failure response.
        """
        logger.info("Testing /fetch-transfers endpoint (failure case)")

        # Mock the behavior of GenerateAlternatives to raise an exception
        mock_instance = MockGenerateAlternatives.return_value
        mock_instance.is_green.side_effect = Exception("Mocked exception")

        # Define the test data
        test_data = {
            "user_id": "1234",
            "url": "example.com",
            "data_transfer": 500
        }

        # Make a POST request to the /fetch-transfers endpoint
        response = self.app.post(
            '/fetch-transfers',
            data=json.dumps(test_data),
            content_type='application/json'
        )

        # Log the response
        logger.info("Received response: %s", response.json)

        # Assert the response
        self.assertEqual(response.status_code, 500)
        self.assertIn("message", response.json)
        self.assertEqual(response.json["message"], "Error processing emissions")

if __name__ == '__main__':
    unittest.main()