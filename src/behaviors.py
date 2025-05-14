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
import numpy as np
import logging
import json
from datetime import datetime
import random
import mysql.connector
from mysql.connector import Error
import math
from sklearn.cluster import KMeans

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
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo'),
    "port": int(os.environ.get('MYSQL_PORT', 3306))  # Ensure port is included and cast to int
}

class DailyBehavior:
    def __init__(self, user_id, password, daily_hours, z_threshold=1.8, iterations=10, db_config=CONFIG):
        self.user_id = user_id
        self.daily_hours = daily_hours
        self.activity_spikes = []
        self.z_threshold = z_threshold
        self.db_config = db_config
        self.iterations = iterations
        self.current_pattern = []
    
    def average_spikes(self):
        """Process self.dailyhours(A list of 24 elements eachrepresenting the percentage of activity from a user per hour)
        into a list of the indices where the activity spikes the highest throughout the day. This is done by
        incrementally updating the mean and standard deviation, then calcualting it's z-score concerning the z-threshold which
        is dynamically updated in respect to the growth of the meand and standard deviation.
        """
        mean = 0
        previous_mean = 0
        previous_std = 0
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

            if std < 0.05:  # Skip if standard deviation is too low
                logging.warning(f"Index {i}: Skipping due to low standard deviation.")
                continue

            mean_rate_of_change = abs(mean - previous_mean) 
            std_rate_of_change = abs(std - previous_std)
            self.z_threshold = 1.8 * (mean_rate_of_change + std_rate_of_change) / 2
            logging.info(f"New Z-Threshold: {self.z_threshold:.2f}")

            z_score = (new_value - mean) / std
            logging.info(f"value: {self.daily_hours[i]}, Z-score: {z_score:.2f}, Mean: {mean:.2f}, Std: {std:.2f}")
            
            if z_score > self.z_threshold:
                self.activity_spikes.append(i)
                logging.info(f"Index {i}: Spike detected with Z-Score={z_score:.2f} value={self.daily_hours[i]:.2f}.")
        
            previous_mean = mean
            previous_std = std
        logging.info(f"User {self.user_id} detected {len(self.activity_spikes)} spikes.")
        logging.info(f"Spikes: {self.activity_spikes}")
    
############################################################################  
    def get_k(self):
        """
        Determine the optimal number of clusters (k) using the elbow method.
        Returns:
            int: Optimal number of clusters (k), with a minimum possible value of 1.
        """
        if len(self.activity_spikes) < 2:
            return 1  # If there are less than 2 spikes, only 1 cluster is possible.

        distortions = []
        max_k = min(10, len(self.activity_spikes))  # Limit k to a maximum of 10 or the number of spikes.
        data = np.array(self.activity_spikes).reshape(-1, 1)

        for k in range(1, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(data)
            distortions.append(kmeans.inertia_)

        # Calculate the "elbow" point
        deltas = np.diff(distortions)
        second_deltas = np.diff(deltas)
        elbow_point = np.argmax(second_deltas) + 2  # +2 because second_deltas is offset by 2 from k

        optimal_k = max(1, min(elbow_point, max_k))  # Ensure k is at least 1
        logging.info(f"Optimal k determined by elbow method: {optimal_k}")
        return optimal_k

    def distances(self, data, target, centroids):
        """Calculate the lowest distance between the current index, and each centroid
        Args:
            data (list): list of activity spikes
            target (int): current index of the activity spike
            centroids (list): list of randomly picked indexes

        Returns:
            int: index of the centroid that is closest to the current index
        """
        logging.info(f"Data: {data}, Target: {target}, Centroids: {centroids}")
        distances = [abs(target - point) for point in centroids]

        logging.info(f"Smallest distance: {distances.index(min(distances))}")
        return distances.index(min(distances))
    
    def update_centroids(self, cluster_results, data):
        """Update the centroid list by taking the mean of each currently know cluster as long as the data exists.

        Args:
            cluster_results (dict): hashmap of the clusters and their points
            data (list): list of activity spikes

        Returns:
            list: list of updated centroids
        """
        updated_points = []

        for rand_pt, points in cluster_results.items():
            if points:
                updated_points.append(sum(points) // len(points))
            else:
                updated_points.append(random.choice(data))        
        return updated_points    
    
    def kmeans_spikes(self):
        """Using K-Means clustering, cluster the activity spikes together for the best possible time windows to monitor the user

        Returns:
            dict: Hashmap of clusters for the best possible time windows to monitor the user
        """
        data = self.activity_spikes
        if len(data) < 2:
            return {0: data}
        k = self.get_k()
        
        centroids = random.sample(data, k)
        centroids = [int(c) - 1 for c in centroids]
        logging.info(f"Initial centroids: {centroids}")

        clusters = {i: [] for i in range(len(centroids))}
        for i in range(self.iterations):
            new_clusters = {i: [] for i in range(len(centroids))}
            for j in range(len(data)):
                index = self.distances(data, data[j], centroids)
                new_clusters[index].append(data[j])

            new_centroids = self.update_centroids(new_clusters, data)
            if new_centroids == centroids:
                break
            centroids = new_centroids
            clusters = new_clusters
        return clusters
    
    def set_current_pattern(self, clusters):
        for cluster_id, points in clusters.items():
            activity_range = [min(points), max(points)]
            self.current_pattern.append(activity_range)
        
############################################################################


class TrackOverallBehavior(DailyBehavior):
    def __init__(self, user_id, password, db_config=CONFIG):
        self.user_id = user_id
        self.password = password
        self.data_count = 0
        self.sb_config = db_config

        day = datetime.now()    
        self.week_day = day.strftime("%A")
        try:
            self.connection = mysql.connector.connect(**self.db_config)
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            raise
        self.cursor = self.connection.cursor()
        table_query = f"""
        CREATE TABLE IF NOT EXISTS `{self.user_id}` (
            currentPattern VARCHAR(255), 
            monday VARCHAR(255), 
            tuesday VARCHAR(255), 
            wednesday VARCHAR(255), 
            thursday VARCHAR(255), 
            friday VARCHAR(255), 
            saturday VARCHAR(255), 
            sunday VARCHAR(255));"""
        self.cursor.execute(table_query)

    def add_behavior(self, node):
        #node is the DailyBehavior object above
        day = self.week_day.lower()
        item_query = f"""INSERT INTO {self.user_id} (currentPattern, {day})
        VALUES (%s, %s, %s);
        """
        values = (self.user_id, self.password, day, node.current_pattern)
        self.cursor.execute()
        
        self.data_count += 1