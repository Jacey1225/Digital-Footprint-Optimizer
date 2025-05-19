import os
import numpy as np
import logging
import json
import mysql.connector
from mysql.connector import Error
from sklearn.cluster import KMeans
import random
import math
from datetime import datetime

CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies16!'),
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo'),
}

logger = logging.getLogger(__name__)

class Node:
    def __init__(self, user_id, daily_hours, z_threshold=1.8, min_z_threshold=0.65, iterations=10):
        self.user_id = user_id
        self.daily_hours = daily_hours
        self.z_threshold = z_threshold
        self.min_z_threshold = min_z_threshold
        self.iterations = iterations

class userInfo:
    def fetch_info(self, user_id, hours):
        hour_node = Node(user_id, hours)
        return hour_node
    
        