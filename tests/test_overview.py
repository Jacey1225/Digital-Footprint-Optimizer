import unittest
from unittest.mock import patch, MagicMock

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.weekly_overview import GetWeekDetails

class TestGetWeekDetails(unittest.TestCase):
    @patch('src.use_DB.DBConnection')
    def setUp(self, MockDBConnection):
        """
        Set up the mock database connection and insert mock data into the websites table.
        """
        # Mock the DBConnection
        self.mock_db = MockDBConnection.return_value
        self.mock_cursor = MagicMock()
        self.mock_db.cursor = self.mock_cursor

        # Mock user_id
        self.user_id = "1234"

        # Mock data to insert into the websites table
        self.mock_data = [
            {"userID": "1234", "day": "2025-05-21", "url": "https://example1.com", "data_transfer": 1000},
            {"userID": "1234", "day": "2025-05-22", "url": "https://example2.com", "data_transfer": 2000},
            {"userID": "1234", "day": "2025-05-23", "url": "https://example3.com", "data_transfer": 3000},
            {"userID": "1234", "day": "2025-05-24", "url": "https://example4.com", "data_transfer": 4000},
            {"userID": "1234", "day": "2025-05-25", "url": "https://example5.com", "data_transfer": 5000},
            {"userID": "1234", "day": "2025-05-26", "url": "https://example6.com", "data_transfer": 6000},
            {"userID": "1234", "day": "2025-05-27", "url": "https://example7.com", "data_transfer": 7000},
        ]

        # Mock the `select_items` method to return the mock data
        self.mock_db.select_items.return_value = self.mock_data

        # Initialize the GetWeekDetails object
        self.week_details = GetWeekDetails(self.user_id)

    def test_get_weekly_data(self):
        """
        Test the get_weekly_data method to ensure it retrieves the last 7 items correctly.
        """
        # Call the method
        result = self.week_details.get_weekly_data()

        # Assert the result matches the mock data
        self.assertEqual(len(result), 7)
        self.assertEqual(result, self.mock_data)

        # Verify the select_items method was called with the correct arguments
        self.mock_db.select_items.assert_called_once_with(
            "*", ["userID"], [self.user_id], fetchAmount=7
        )

if __name__ == "__main__":
    unittest.main()