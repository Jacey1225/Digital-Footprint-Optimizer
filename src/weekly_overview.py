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

from src.use_DB import DBConnection
class GetWeekDetails(DBConnection):
    def __init__(self ,user_id):
        super().__init__("websites")
        self.user_id = user_id
    
    def get_weekly_data(self):

            select_value = "*"
            where_values = ["userID"]
            order_value = "day"
            values = [self.user_id]
            fetchAmount = 7

            last_7_items = self.select_items(select_value, where_values, values, order_value=order_value, fetchAmount=fetchAmount)

            if last_7_items:    
                return last_7_items