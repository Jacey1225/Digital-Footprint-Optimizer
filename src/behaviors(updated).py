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

class UserInfo:
    def __init__(self, user_id, daily_report):
        self.user_id = user_id
        self.daily_report = daily_report
        self.connection = mysql.connector.connect(**CONFIG)
        self.cursor = self.connection.cursor()
        self.data = []
        self.cluster_data = []
        self.cluster_labels = []
        self.cluster_centers = []
        self.clustered_data = []