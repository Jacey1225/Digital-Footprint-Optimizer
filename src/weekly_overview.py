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

CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies16!'),
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo'),
    "port": int(os.environ.get('MYSQL_PORT', 3306))  # Ensure port is included and cast to int
}

class DBConnection:
    def __init__(self,db_config=CONFIG):
        self.db_config = db_config
        try:
            self.connection = mysql.connector.connect(**db_config)
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
        except Error as e:
            logging.error("Error while connecting to MySQL", e)
            raise
    
    def open(self):
        if not self.connection.is_connected():
            try:
                self.connection.connect(**self.db_config)
                self.cursor = self.connection.cursor()
            except Error as e:
                logging.error("Error while connecting to MySQL", e)
                raise
    
    def close(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logging.info("MySQL connection is closed")
        else:
            logging.warning("MySQL connection is already closed")
            raise
    
    def create_table(self):
        try:
            table_query = """
            CREATE TABLE IF NOT EXISTS websites (
                userID VARCHAR(255) PRIMARY KEY,
                 root VARCHAR(255),
                 footprint INT,
                 suggestion1 VARCHAR(255),
                 suggestion2 VARCHAR(255),
                 suggestion3 VARCHAR(255));"""
            self.cursor.execute(table_query)
        except Error as e:
            logging.error("Error while creating table", e)
            raise
    
    def insert_items(self, user_id, values):
        try:
            insert_query = """
            INSERT INTO websites (userID, root, footprint, suggestion1, suggestion2, suggestion3)
            VALUES (%s, %s, %s, %s, %s, %s)"""
            self.cursor.execute(insert_query, values)
            self.connection.commit()
        except Error as e:
            logging.error("Error while inserting items", e)
            raise
    
    def select_items(self, user_id, value_to_select=None):
        try:
            if value_to_select is None:
                select_query = """
                SELECT * FROM websites 
                WHERE userID = %s
                ORDER BY root DESC
                LIMIT 7"""
                self.cursor.execute(select_query, (user_id,))
                result = self.cursor.fetchall()
            else:
                select_query = """
                SELECT %s FROM webistes 
                WHERE userID = %s
                ORDER BY root DESC
                LIMIT 7"""
                self.cursor.execute(select_query, (value_to_select, user_id))
                result = self.cursor.fetchone()
            
            if result:
                return result
        except Error as e:
            logging.error("Error while selecting items", e)
            raise



class TrackWeekDetails(DBConnection):
    def __init__(self, user_id):
        self.user_id = user_id
    
    def get_weekly_data(self):
            self.open()
            self.create_table()
            last_7_items = self.select_items(self.user_id)
            self.close()

            if last_7_items:    
                return last_7_items
            
    def insert_web_data(self, values):
        self.open()
        self.create_table()
        self.insert_items(self.user_id, values)
        self.close()