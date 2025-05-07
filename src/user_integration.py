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
    "database": os.environ.get('MYSQL_DATABASE', 'website_tracker')
}

class UserIntegration:
    def __init__(self, username, email, password, db_config=CONFIG):
        self.user = username
        self.email = email
        self.password = password
        self.db_config = db_config

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
        user_id = random.shuffle(sequence)
        return user_id

    def create_table(self, user_id):
        """add a new table in the SQL database under the user's new ID and 
        insert the following informatino about the user

        Args:
            user_id (string): Generated User ID
        """
        self.cursor.execute("CREATE TABLE IF NOT EXISTS {user_id} (user VARCHAR(255) PRIMARY KEY, pass VARCHAR(255), url VARCHAR(255), data_transfer INT, web_suggested_1 VARCHAR(255), web_suggested_2 VARCHAR(255), web_suggested_3 VARCHAR(255), date VARCHAR(255))")
    
    def user_exists(self, user_id):
        """Verify if the user exists within any table within the SQL database and if the tables pass corresponds
        to the password provided from the user in the init function

        Args:
            user_id: ID of the user
        """
        query = """
        SELECT COUNT(*)
        FORM information_schema.tables
        WHERE table_schema = %s
            AND table_name = %s;
        """
        self.cursor.execute(query, (self.db_config["database"], user_id))
        result = self.cursor.fetchone()
        if result:
            if result[1] == self.password:
                return True
        else:
            return False