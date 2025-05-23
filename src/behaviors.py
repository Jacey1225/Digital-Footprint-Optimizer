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
    def __init__(self, user_id, daily_hours, z_threshold=1.8, min_z_threshold=0.65, iterations=10, db_config=CONFIG):
        self.user_id = user_id
        self.daily_hours = daily_hours
        self.activity_spikes = []
        self.z_threshold = z_threshold
        self.min_z_threshold = min_z_threshold
        self.db_config = db_config
        self.iterations = iterations
        self.current_pattern = []
    
    def average_spikes(self):
        """Process self.dailyhours(A list of 24 elements each representing the percentage of activity from a user per hour)
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

            if std < 0.1:  # Skip if standard deviation is too low
                logging.warning(f"Index {i}: Skipping due to low standard deviation.")
                continue

            mean_rate_of_change = abs(mean - previous_mean) 
            std_rate_of_change = abs(std - previous_std)
            new_threshold = 1.8 * (mean_rate_of_change + std_rate_of_change) / 2
            self.z_threshold = max(self.min_z_threshold, new_threshold)
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
    
##########################################
# K-MEANS CLUSTERING FOR ACTIVITY SPIKES #
##########################################

    def get_k(self):
        """
        Determine the optimal number of clusters (k) using the elbow method.
        Returns:
            int: Optimal number of clusters (k), with a minimum possible value of 1.
        """
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
    
    def set_pattern(self, clusters):
        for cluster_id, points in clusters.items():
            activity_range = [min(points), max(points)]
            self.current_pattern.append(activity_range)
        
##############################################################
# DATABASE INTEGRATION FOR USER BEHAVIOR TRACKING OVER WEEKS #
##############################################################
class TrackOverallBehavior():
    def __init__(self, user_id, password, db_config=CONFIG):
        """
        Initializes the behavior tracking object for a specific user.
        Args:
            user_id (str): The unique identifier for the user.
            password (str): The password for the user.
            db_config (dict, optional): The database configuration dictionary. Defaults to CONFIG.
        Attributes:
            user_id (str): The unique identifier for the user.
            password (str): The password for the user.
            data_count (int): Counter for tracking data entries, initialized to 0.
            db_config (dict): The database configuration dictionary.
            week_day (str): The current day of the week in string format.
            connection (mysql.connector.connection.MySQLConnection): The MySQL database connection object.
            cursor (mysql.connector.cursor.MySQLCursor): The cursor object for executing database queries.
        Raises:
            Error: If there is an issue connecting to the MySQL database.
        Notes:
            - Creates a table for the user in the database if it does not already exist.
            - Logs the table creation query for debugging purposes.
        """

        self.user_id = user_id
        self.password = password 
        self.db_config = db_config
        day = datetime.now()    
        self.week_day = day.strftime("%A")

        try:
            self.connection = mysql.connector.connect(**self.db_config)
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            
        self.cursor = self.connection.cursor()
        table_query = f"""
        CREATE TABLE IF NOT EXISTS `{self.user_id}` (
            day VARCHAR(255) PRIMARY KEY,
            currentPattern TEXT,
            history TEXT);"""
        
        logging.info(f"Executing table creation query: {table_query}")
        self.cursor.execute(table_query)

        count_query = f"SELECT COUNT(*) FROM `{self.user_id}`"
        self.cursor.execute(count_query)
        self.data_count = self.cursor.fetchone()[0]


    def add_behavior(self, current_pattern, pattern_of_day):
        #node is the DailyBehavior object above
        day = self.week_day.lower()
        item_query = f"""INSERT INTO `{self.user_id}` (day, currentPattern, history)
        VALUES (%s, %s, %s);
        """
        values = (day, json.dumps(current_pattern), json.dumps(pattern_of_day))
        self.cursor.execute(item_query, values)
        self.connection.commit()
        

########################################################
# K-MEANS CLUSTERING FOR PAST PATTERNS AND CURRENT DAY #
########################################################
    def get_k(self, pattern_data):
        """Using KMeans inertia calculations, we can calculate the most potimal number of clusters for the given 
        activity spikes

        Args:
            pattern_data (2D Array): a 2-Dimensional array of the activty spikes where each spike is represented as a range
            from the earliest known value to the latest known value

        Returns:
            int: optimal value for K 
        """
        if len(pattern_data) < 2:
            return 1
        
        distortions = []
        max_k = min(10, len(pattern_data))
        data = np.array(pattern_data)

        for k in range(1, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(data)
            distortions.append(kmeans.inertia_)
        
        deltas = np.diff(distortions)
        second_deltas = np.diff(deltas)
        elbow_point = np.argmax(second_deltas) + 2

        optimal_k = max(1, min(elbow_point, max_k))
        logging.info(f"Optimal k determined by elbow method: {optimal_k}")
        return optimal_k
    
    def distances(self, target, centroids):
        """calculates the distance for each point in the range according to each centroid
        1. calculates the distance between the centroid and the target's first point
        2. calculates the distance between the centroid and the target's second point
        3. add the two distances together
        4. return the index of the centroid with the lowest distance

        Args:
            target (list): tuple of the current index
            centroids (list): 2D aray of tuple centroids

        Returns:
            int: index within the clusters hashmap of thec entroid with the lowest distance
        """
        distances = []
        for point in centroids:
            distance1 = abs(target[0] - point[0])
            distance2 = abs(target[1] - point[1])
            distance = distance1 + distance2
            distances.append(distance)

        return distances.index(min(distances))
    
    def update_centroids(self, cluster_results, pattern_data):
        """In order to maximize the accuracy of our clusters, we mean out each cluster's points
        as long as they exist, adn update the cluster's centroids respectively, repeating the process from the beginning
        If, however, the clusters are empty, we randomly select a centroid from the original data to be in-place. 

        Args:
            cluster_results (dict): hashmap of the currently known cluster items
            pattern_data (list): 2D array of the activity spikes pulled from the database

        Returns:
            list: return the new centroids 
        """
        updated_points = []
        for rand_pt, points in cluster_results.items():
            if points:
                updated_points.append([sum(p[0] for p in points) // len(points), sum(p[1] for p in points) // len(points)])
            else:
                updated_points.append(random.choice(pattern_data))
        
        return updated_points
    
    def kmeans_pattern(self, kmean_data, iterations=10):
        """Using K-Means clustering, cluster the current pattern, to the last known pattern together 
        for the best adjustment of the two patterns. 

        Args:
            kmean_data (list): 2D array of the two patterns joined together
            iterations (int, optional): _description_. Defaults to 10.

        Returns:
            dict: a hashmap of the clusterse for the best possible adjustment of the two patterns
        """
        if len(kmean_data) < 2:
            return {0: kmean_data}
        
        k = self.get_k(kmean_data)
        centroids = random.sample(kmean_data, k)

        clusters = {i: [] for i in range(len(centroids))}
        for i in range(iterations):
            new_clusters = {i: [] for i in range(len(centroids))}
            for j in range(len(kmean_data)):
                index = self.distances(kmean_data[j], centroids)
                new_clusters[index].append(kmean_data[j])

            new_centroids = self.update_centroids(new_clusters, kmean_data)
            if new_centroids == centroids:
                break

            centroids = new_centroids
            clusters = new_clusters
        
        return clusters
        
    def set_new_pattern(self, clusters):
        """average out the cluster results to make a new pattern for the user 

        Args:
            clusters (dict): cluster results from the kmeans pattern function

        Returns:
            list: adjusted pattern list as instruction for the frontend monitoring service
        """
        ranges = []
        for cluster_id, points in clusters.items():
            average_start = sum(p[0] for p in points) // len(points)
            average_stop = sum(p[1] for p in points) // len(points)
            ranges.append([average_start, average_stop])
        
        return ranges
    
    def evaluate_similarity(self, daily_pattern, current_pattern, tolerance=2.5):
        """ignore first coming outliers to the data, if the new data is recurring however, update the 
        pattern accordingly, otherwise, if they are similar, return True to continue through the process

        Args:
            daily_pattern (list): pattern do be evaluated -> adjusting the current pattern
            current_pattern (list): last known pattern that is being adjusted
            tolerance (float, optional): threshold for which values can be similar to each other. Defaults to 2.5.

        Returns:
            bool: True if the two patterns are similar, False otherwise
        """
        if not daily_pattern or not current_pattern:
            logging.warning("One of the patterns is empty. Returning False.")
            return False
        
        for pattern1, pattern2 in zip(daily_pattern, current_pattern):
            diff1 = abs(pattern1[0] - pattern2[0])
            diff2 = abs(pattern1[1] - pattern2[1])
            average_diff = (diff1 + diff2) / 2
            if average_diff > tolerance:
                return False
        return True
    
# Wrapper function for previous fucntions to complete the behavior updating process
    def update_behavior(self, daily_pattern):
        """
        Updates the user's behavior pattern in the database based on the provided daily pattern.
        This method retrieves the current and previous day's patterns from the database, evaluates 
        their similarity with the provided daily pattern, and updates the current pattern accordingly. 
        If the patterns are too different, it attempts to match the daily pattern with the previous day's 
        pattern. If successful, it updates the current pattern using a combination of the previous day's 
        pattern and the daily pattern. Otherwise, it retains the current pattern.
        Args:
            daily_pattern (list): A list representing the user's daily behavior pattern.
        Returns:
            str: A message indicating whether the patterns were too different to update or if the update 
                 was successful.
        Raises:
            json.JSONDecodeError: If the current or previous day's pattern cannot be parsed as JSON.
            Exception: If there are issues executing the database queries.
        Database Schema:
            - The method assumes a table named after the user's ID (`self.user_id`) with the following columns:
                - `day`: The day of the week (e.g., Monday, Tuesday).
                - `currentPattern`: The current behavior pattern stored as a JSON string.
                - `previousPattern`: The previous day's behavior pattern stored as a JSON string.
        Logging:
            - Logs information about the similarity evaluation and the update process.
            - Logs the final updated pattern for the user.
        Note:
            - The method uses K-Means clustering (`self.kmeans_pattern`) to generate a new pattern 
              based on the combined data.
            - The new pattern is sorted by the first element of each cluster before being stored.
        """
        if self.data_count > 7: # If there are more than 7 data points, we can start tracking by the day
            pattern_query = f"""SELECT * FROM `{self.user_id}` 
            WHERE day = %s
            ORDER BY day DESC
            LIMIT 1;""" 
        else: # If there are less than 7 data points, we can only track by the hour
            pattern_query = f"""SELECT * FROM `{self.user_id}`
            ORDER BY day DESC
            LIMIT 1;"""

        self.cursor.execute(pattern_query, (self.week_day,))
        current_node = self.cursor.fetchone()
        if not current_node:
            logging.info(f"No previous pattern found for {self.user_id}.")
            return "No previous pattern found."
        
        current_pattern = json.loads(current_node[1])
        previous_day = json.loads(current_node[2])
        if current_node:
            if not self.evaluate_similarity(daily_pattern, current_pattern):
                logging.info(f"Patterns are too different to update - trying to match the last day's pattern")
                if not self.evaluate_similarity(daily_pattern, previous_day):
                    logging.info(f"Pattern cannot be matched, updating the current pattern")
                    update_query = f"""UPDATE `{self.user_id}` SET currentPattern = %s WHERE day = %s"""
                    values = [json.dumps(current_pattern), self.week_day]
                    self.cursor.execute(update_query, values)
                    return "Patterns are too different to update."
                else:
                    logging.info(f"Patterns are similar, updating the current pattern to the last day's pattern")
                    kmean_data = previous_day + daily_pattern
            else:
                logging.info(f"Patterns are similar, updating the current pattern to the current day's pattern")
                kmean_data = current_pattern + daily_pattern

            clusters = self.kmeans_pattern(kmean_data)
            new_pattern = self.set_new_pattern(clusters)
            sorted_array = sorted(new_pattern, key=lambda x: x[0])

    
            self.add_behavior(sorted_array, daily_pattern)
        if sorted_array:
            logging.info(f"Behavior updated or {self.user_id} where the new pattern is {sorted_array}.")
    
    def get_next_pattern(self):
        if self.data_count > 7:
            next_pattern = f"SELECT currentPattern FROM `{self.user_id}` WHERE day = %s" 
            self.cursor.execute(next_pattern, (self.week_day, ))
        else:
            next_pattern = f"SELECT currentPattern FROM `{self.user_id}` ORDER BY day DESC LIMIT 1"
            self.cursor.execute(next_pattern)

        pattern = self.cursor.fetchone()
        if pattern:
            return json.loads(pattern[0])
        else:
            return None