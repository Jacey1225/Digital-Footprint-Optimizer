"""Workflow:
1. read the databse for both MySQL databases userInfo and website_tracker
2. Get the last 7 or last known rows from userInfo as the current pattern for each day of the week
3. Get the last 7 or last known rows from the website_tracker as the latest known suggestions form the user's webisite activity
4. Store each result in a dictionary as userInfo and webInfo
5. userInfo = [day, pattern, last known activity] -- webInfo = [user, password, url, data_transfer, suggested website, suggested website, suggested_website, data_age]

Returns:
    dict: Dictionary of information containing the last 7 items of data from the userInfo and website_tracker databases
"""

import mysql.connector
from mysql.connector import Error
import logging
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

SUGG_CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies!'),
    "database": os.environ.get('MYSQL_DATABASE', 'website_tracker'),
    "port": int(os.environ.get('MYSQL_PORT', 3306))  # Ensure port is included and cast to int
}
INFO_CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies16!'),
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo'),
    "port": int(os.environ.get('MYSQL_PORT', 3306))  # Ensure port is included and cast to int
}

class TrackWeekDetails:
    def __init__(self, info_config=INFO_CONFIG, suggestion_config=SUGG_CONFIG):
        """
        Initializes the class with database connection configurations and establishes
        connections to the respective databases.
        Args:
            info_config (dict, optional): Configuration dictionary for the information
                database connection. Defaults to INFO_CONFIG.
            suggestion_config (dict, optional): Configuration dictionary for the suggestion
                database connection. Defaults to SUGG_CONFIG.
        Attributes:
            info_config (dict): Stores the configuration for the information database.
            suggestion_config (dict): Stores the configuration for the suggestion database.
            info_connection (mysql.connector.connection.MySQLConnection): Connection object
                for the information database.
            suggestion_connection (mysql.connector.connection.MySQLConnection): Connection
                object for the suggestion database.
            info_cursor (mysql.connector.cursor.MySQLCursor): Cursor object for executing
                queries on the information database.
            suggestion_cursor (mysql.connector.cursor.MySQLCursor): Cursor object for
                executing queries on the suggestion database.
        """

        self.info_config = info_config
        self.suggestion_config = suggestion_config
        self.info_connection = mysql.connector.connect(**info_config)
        self.suggestion_connection = mysql.connector.connect(**suggestion_config)
        self.info_cursor = self.info_connection.cursor()
        self.suggestion_cursor = self.suggestion_connection.cursor()

    def get_last_7_rows(self, user_id):
        try:
            query = f"SELECT * FROM `{user_id}` ORDER BY id DESC LIMIT 7"
            self.info_cursor.execute(query)
            rows = self.info_cursor.fetchall()
            return rows
        except Error as e:
            logging.error(f"Error fetching last 7 rows: {e}")
            return []