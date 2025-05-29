import os
import sys
import random
import logging
import string
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.use_DB import DBConnection

class UserIntegration(DBConnection):
    def __init__(self, username):
        super().__init__("users")
        self.username = username
        self.user_id = ""

    def generate_random_id(self, length=8):
        max_alpha = 5
        max_num = 3
        
        random_alpha = [random.choice(string.ascii_letters) for _ in range(max_alpha)]
        random_num = [random.choice(string.digits) for _ in range(max_num)]

        sequence = random_alpha + random_num
        id = random.shuffle(sequence)
        self.user_id = id

    def set_user(self):
        where_values = ["userID", "user"]
        values = [self.user_id, self.username]
        try:
            self.insert_items(where_values, values)
            logging.info(f"User {self.username} with ID {self.user_id} added to the database.")
        except Exception as e:
            logging.error(f"Error adding user {self.username}: {e}")
            raise

    def validate_user(self):
        where_values = ["user"]
        values = [self.username]

        is_user = self.find(where_values, values)
        if len(is_user) > 0:
            logging.info(f"User already exists: {self.username}")
            return True
        return False
    
    def get_user(self):
        select_value = "userID"
        where_values = ["user"]
        values = [self.username]

        id = self.select_items(select_value, where_values, values)
        if id:
            self.user_id = id[0][0]
            logging.info(f"User ID for {self.username} is {self.user_id}")
        else:
            logging.error(f"User {self.username} not found. Creating account...")
            self.generate_random_id()
            self.set_user()
            logging.info(f"New user ID generated: {self.user_id}")
        
        return self.user_id
