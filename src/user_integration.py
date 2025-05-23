import os
import mysql.connector
from mysql.connector import Error
import logging
import random
import string

logger = logging.getLogger(__name__)

CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies!'),
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo')
}
class DBConnection:
    def __init__(self, db_config=CONFIG):
        self.db_config = db_config

        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
        except Error as e:
            logger.error("Error while connecting to MySQL", e)
            raise

    def open(self):
        if not self.connection.is_connected():
            try:
                self.connection.connect(**self.db_config)
                self.cursor = self.connection.cursor()
            except Error as e:
                logger.error("Error while connecting to MySQL", e)
    
    def close(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logger.info("MySQL connection is closed")
        else:
            logger.warning("MySQL connection is already closed")
            raise
    
    def create_table(self):
        try:
            table_query = """
            CREATE TABLE IF NOT EXISTS users (
                userID VARCHAR(255) PRIMARY KEY,
                user VARCHAR(255),
                pass VARCHAR(255),
                email VARCHAR(255));"""
            self.cursor.execute(table_query)
        except Error as e:
            logger.error("Error while creating table", e)
            raise
    
    def insert_user(self, values):
        try:
            insert_query = """
            INSERT INTO users (userID, user, pass, email)
            VALUES (%s, %s, %s, %s);"""
            self.cursor.execute(insert_query, values)
            self.connection.commit()
        except Error as e:
            logger.error("Error while inserting user", e)
            raise

    def verify_user(self, user, email, password):
        try:
            find_query = """
            SELECT * FROM users WHERE user = %s AND email = %s;"""
            self.cursor.execute(find_query, user)
            result = self.cursor.fetchone()
            if result:
                if result[2] == password:
                    return True
            
            return False
        except Error as e:
            logger.error("Error while verifying user", e)
            raise
    
    def select_user(self, user, email):
        try:
            find_query = """
            SELECT * FROM users WHERE user = %s AND email = %s;"""
            self.cursor.execute(find_query, (user, email))
            result = self.cursor.fetchone()
            if result:
                return result
            else:
                return None
        except Error as e:
            logger.error("Error while selecting user", e)
            raise
class UserIntegration(DBConnection):
    def __init__(self, username, email, password):
        self.user = username
        self.email = email
        self.password = password
        self.user_id = None

        try:
            self.connection = mysql.connector.connect(
                host = self.db_config["host"],
                user = self.db_config["user"],
                password = self.db_config["password"],
                database = self.db_config["database"]
            ) 
            self.cursor = self.connection.cursor()
        except Error as e:
            logger.info("Error while connectiing to MySQL", e)
        
    
    def generate_random_id(self, max_length=10):
        """generate a random ID for the new user in the system

        Args:
            max_length (int, optional): maximum ID length for each new user. Defaults to 10.

        Returns:
            string: the user ID
        """
        max_alpha = 5
        max_num = 3
        max_symbol = 2

        rand_alpha = [random.choice(string.ascii_letters) for i in range(max_alpha)]
        rand_num = [random.choice(string.digits) for i in range(max_num)]
        rand_symbols = [random.choice("!@#$%^&*?.," for i in range(max_symbol))]

        sequence = rand_alpha + rand_num + rand_symbols
        id = random.shuffle(sequence)
        self.user_id = id

    