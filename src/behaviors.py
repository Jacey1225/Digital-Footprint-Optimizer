"""Work Flow:
1. Take in a daily report of the percentage that the user was active for each hour of the day
2. Search this data via z-score to find the shifts in activity throughout the day
3. The search function will return a 1D list of each index where a shift in activty occurred
4. Take the list of indices, and as more data is fed into the system for each day, use
cross-correlation to find the most common shifts in activity, and store them as results
5. After the most common shifts are found, send them as timers to the frontend service 
to let it know exactly when to start and stop monitoring the user's activity
6. Relate the results back to the original dataset, noting the percentage of activity
throughout each sequence which will tell us the activity level of the user
7. As data gets larger, move the model logic to a larger generalization function
from hours a day to hours per each day of the week. 
"""
import os
import logging
import json
from datetime import datetime
import random
import mysql.connector
from mysql.connector import Error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies16!'),
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo')
}

class DailyBehavior:
    def __init__(self, user_id, password, daily_hours, db_config=CONFIG, z_threshold=1.3, k=3):
        self.user_id = user_id
        self.daily_hours = daily_hours
        self.activity_spikes = []
        self.z_threshold = z_threshold
        self.k = k
        
        day = datetime.now()    
        self.week_day = day.strftime("%A")

        self.db_config = db_config
        self.connection = mysql.connector.connect(**self.db_config)
        self.cursor = self.connection.cursor()
        table_query = f"""
        CREATE TABLE IF NOT EXISTS {self.user_id} (
            user_id VARCHAR(255) PRIMARY KEY, 
            PASSWORD VARCHAR(255), 
            MONDAY VARCHAR(255), 
            TUESDAY VARCHAR(255), 
            WEDNESDAY VARCHAR(255), 
            THURSDAY VARCHAR(255), 
            FRIDAY VARCHAR(255), 
            SATURDAY VARCHAR(255), 
            SUNDAY VARCHAR(255));"""
        self.cursor.execute(table_query)
    
    def average_spikes(self):
        mean = 0
        window_size = 0
        M2 = 0

        for i in range(len(self.daily_hours)):  # Update both the mean and std incrementally
            new_value = self.daily_hours[i]
            window_size += 1 
            delta = new_value - mean
            mean += delta / window_size
            M2 += delta * (new_value - mean)
            variance = M2 / window_size if window_size > 1 else 0

            std = variance ** 0.5

            if std == 0:
                logging.warning(f"Index {i}: Skipping due to zero standard deviation.")
                continue

            z_score = abs(new_value - mean) / std
            logging.info(
                f"Index {i}: Value={new_value}, Mean={mean:.2f}, Std={std:.2f}, Z-Score={z_score:.2f} -> threshold={self.z_threshold:.2f}"
            )

            if z_score > self.z_threshold:
                self.activity_spikes.append(new_value)
                logging.info(f"Index {i}: Spike detected with Z-Score={z_score:.2f} on index {i}.")
        
        logging.info(f"User {self.user_id} detected {len(self.activity_spikes)} spikes.")
    
    def kmeans_clustering(self, current_pattern=None, new_data=None, iterations=10):
        """cluster spike trends together using k-means clustering
        1. Pull data from SQL database
        2. Set the number of clusters needed to group the data together
        3. Take a random number of values from the data
        4. Iterate through each point of data and calculate the distance to each randomized point
        5. Assign each point to the closest K point
        6. Once the points are assigned, calculate the mean of each cluster and repeat the process
        6. Continue calculating these distances until the points are stable
        7. Return each cluster from its min and max points

        Args:
            data (_type_): _description_
        """
        if not day_pattern_query:
            day_pattern_query = f"""SELECT {self.week_day} FROM {self.user_id} ORDER BY {self.week_day} DESC LIMIT 1;"""
        
        self.cursor.execute(day_pattern_query)
        current_pattern = self.cursor.fetchone()
        data = new_data + current_pattern

        random_points = random.sample(data, self.k)
        clusters = {random_point: [] for random_point in random_points}
        for i in range(iterations):
            new_clusters = {random_point: [] for random_point in random_points}
            for j in range(len(data)):
                if j not in random_points:
                    distances = [abs(data[j] - data[point]) for point in random_points]
                    closest_point = random_points[distances.index(min(distances))]
                    new_clusters[closest_point].append(data[j])

            updated_points = []
            for rand_pt, points in clusters.items():
                if points:
                    updated_points.append(sum(points) / len(points))
                else:
                    updated_points.append(random.choice(data))

            if updated_points == random_points:
                break
            random_points = updated_points
            clusters = new_clusters
        return clusters
class TrackOverallBehavior(DailyBehavior):
    def __init__(self, user_id, password, daily_hours):
        super().__init__(user_id, password, daily_hours)
        self.user_id = user_id
        self.password = password
        self.daily_hours = daily_hours
        self.data_count = 0

    def add_behavior(self, node):
        day = node.week_day.upper()
        item_query = f"""INSERT INTO {self.user_id} (user_id, PASSWORD, {day})
        VALUES (%s, %s, %s);
        """
        values = (self.user_id, self.password, day, node.current_pattern)
        self.cursor.execute()
        
        self.data_count += 1



