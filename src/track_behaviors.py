import os
import numpy as np
import logging
import json
import mysql.connector
from mysql.connector import Error
from sklearn.cluster import KMeans
import random
from datetime import datetime

CONFIG = {
    "host": os.environ.get('MYSQL_HOST', 'localhost'),
    "user": os.environ.get('MYSQL_USER', 'jaceysimpson'),
    "password": os.environ.get('MYSQL_PASSWORD', 'WeLoveDoggies16!'),
    "database": os.environ.get('MYSQL_DATABASE', 'userInfo'),
}

logger = logging.getLogger(__name__)

class Node:
    def __init__(self, user_id, daily_hours, pattern=None, z_threshold=1.8, min_z_threshold=0.65, iterations=10):
        self.user_id = user_id
        self.day = datetime.now().strftime("%A")
        self.daily_hours = daily_hours
        self.current_pattern = pattern

        self.z_threshold = z_threshold
        self.min_z_threshold = min_z_threshold
        self.iterations = iterations

class DBConnection:
    def __init__(self, db_config=CONFIG):
        self.db_config = db_config
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            self.cursor = self.connection.cursor()
        except Exception as e:
            logger.error("Error while connecting to MySQL: %s", e)
            
        
    def close(self):
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logger.info("MySQL connection is closed")
    
    def open(self):
        if not self.connection.is_connected():
            try:
                self.connection = mysql.connector.connect(**self.db_config)
                self.cursor = self.connection.cursor()
                logger.info("MySQL connection is opened")
            except Error as e:
                logger.error("Error while connecting to MySQL", e)
    
    def find(self, where_values, values):
        try:
            count_query = f"""SELECT * FROM behaviors WHERE {where_values[0]} = %s AND {where_values[1]} = %s"""
            self.cursor.execute(count_query, (values[0], values[1]))
            count = self.cursor.fetchall()
            return count
        except Error as e:
            logger.error(f"Error counting rows: {e}")
            self.connection.rollback()

    def create_table(self):
        try:
            table_query = f"""CREATE TABLE IF NOT EXISTS
            behaviors (
                userID VARCHAR(255) PRIMARY KEY,
                day VARCHAR(255),
                currentPattern TEXT,
                history TEXT);"""
            self.cursor.execute(table_query)
            self.connection.commit()
        except Error as e:
            logger.error(f"Error creating table: {e}")
            self.connection.rollback()
    
    def select_items(self, select_value, where_values, order_value, values, fetchall=True, desc=True):
        if desc:
            order_value = f"{order_value} DESC LIMIT 1"
        else:
            order_value = f"{order_value} ASC LIMIT 1"

        if (
            not isinstance(select_value, str) or 
            not isinstance(where_values, list) or 
            not isinstance(order_value, str) or 
            not isinstance(values, list)
        ):
            raise ValueError("Invalid input types. Expected strings for select_value, from_value, where_value, order_value and list for values.")
        
        try:
            if self.find(where_values, values) is None:
                select_query = f"""
                SELECT {select_value} 
                FROM behaviors
                WHERE {where_values[0]} = %s
                ORDER BY {order_value};"""
            else:
                select_query = f"""
                SELECT {select_value} 
                FROM behaviors
                WHERE {where_values[0]} = %s AND {where_values[1]} = %s
                ORDER BY {order_value};"""

            self.cursor.execute(select_query, (values))
            if fetchall:
                rows = self.cursor.fetchall()
            else:
                rows = self.cursor.fetchone()
            return rows
        except Error as e:
            logger.error(f"Error selecting items: {e}")
            self.connection.rollback()
    
    def insert_items(self, values):
        if (not isinstance(values, list)):
            raise ValueError("Invalid input types. Expected strings for user_id, day, currentPattern, and history.")
        try:
            insert_query = f"""
            INSERT INTO behaviors
            (userID, day, currentPattern, history)
            VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(insert_query, (values[0], values[1], values[2], values[3]))
            self.connection.commit()
        except Error as e:
            logger.error(f"Error inserting items: {e}")
            self.connection.rollback()

    def update_items(self, value_to_update, where_values, values):
        if (
            not isinstance(value_to_update, str) or 
            not isinstance(where_values, list) or 
            not isinstance(values, list)
        ):
            raise ValueError("Invalid input types. Expected strings for user_id, value_to_update, where_value, and new_value.")
        try:
            update_query = f"""
            UPDATE behaviors
            SET {value_to_update} = %s
            WHERE {where_values[0]} = %s AND {where_values[1]} = %s
            """
            self.cursor.execute(update_query, (values[0], values[1], values[2]))
            self.connection.commit()
        except Error as e:
            logger.error(f"Error updating items: {e}")
            self.connection.rollback()

class DetectSpikes:
    def __init__(self):
        self.activity_spikes = []
        self.node = None
        self.mean = 0
        self.prev_mean = 0
        self.std = 0
        self.prev_std = 0
        self.window_size = 0
        self.M2 = 0
        self.z_threshold = 0
    
    def process_node(self, node):
        if node:
            self.node = node
            self.z_threshold = node.z_threshold
        else:
            raise ValueError("Node is None. Cannot process.")
        
    def get_std(self, new_value):
        if self.node:
            self.window_size += 1
            delta = new_value - self.mean
            self.mean += delta / self.window_size
            self.M2 += delta * (new_value - self.mean)
            variance = self.M2 / self.window_size if self.window_size > 1 else 0

            self.std = variance ** 0.5
        
    def adjust_z_threshold(self):
        mean_rate_of_change = abs(self.mean - self.prev_mean)
        std_rate_of_change = abs(self.std - self.prev_std)
        new_threshold = 1.8 * (mean_rate_of_change + std_rate_of_change) / 2
        self.z_threshold = max(self.z_threshold, new_threshold)

    def z_score(self, new_value):
        if self.std == 0:
            return 0
        else: 
            return (new_value - self.mean) / self.std
    
    def detect_spikes(self):
        for i in range(len(self.node.daily_hours)):
            new_value = self.node.daily_hours[i]
            self.get_std(new_value)
            
            if self.std < 0.1:
                continue
            else:
                self.adjust_z_threshold()
                z_score = self.z_score(new_value)
            
                if z_score > self.z_threshold:
                    self.activity_spikes.append(i)
            self.prev_mean = self.mean
            self.prev_std = self.std
    
    def update_node(self):
        if self.activity_spikes:
            return Node(self.node.user_id, self.node.daily_hours, self.activity_spikes)
        else:
            raise ValueError("No activity spikes detected.")

class Cluster:
    def __init__(self):
        self.clusters = None
        self.k = None
        self.centroids = None

        self.user_id = None
        self.day = None
        self.data = None
        self.history = None

        self.iterations = None
        self.tolerance = None

    def process_node(self, node):
        if node:
            self.user_id = node.user_id
            self.day = node.day
            self.data = node.current_pattern
            self.history = node.daily_hours
            self.iterations = node.iterations
            self.tolerance = node.tolerance
        else:
            raise ValueError("Node is None. Cannot process.")
    
    def distances(self, target):
        return []

    def update_centroids(self):
        return []
        
    def kmeans(self):
        if len(self.data) < 2:
            return {0: self.data}
        
        self.centroids = random.sample(self.data, self.k)
        self.centroids = [int(centroid) - 1 for centroid in self.centroids]

        self.clusters = {i: [] for i in range(len(self.centroids))}
        for i in range(self.iterations):
            new_clusters = {i: [] for i in range(len(self.centroids))}
            for j in range(len(self.data)):
                index = self.distances(self.data[j])
                new_clusters[index].append(self.data[j])

            new_centroids = self.update_centroids(self.data)
            if new_centroids == self.centroids:
                break
            else:
                self.centroids = new_centroids
                self.clusters = new_clusters

class ClusterSpikes(Cluster):
    def __init__(self):
        super().__init__()
    
    def get_k(self):
        distortions = []
        max_k = min(10, len(self.data))
        data = np.array(self.data).reshape(-1, 1)

        for k in range(1, max_k + 1):
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(data)
            distortions.append(kmeans.inertia_)

        deltas = np.diff(distortions)
        second_deltas = np.diff(deltas)
        if not len(second_deltas) < 2:
            elbow_point = np.argmax(second_deltas) + 2
        else:
            elbow_point = 1

        optimal_k = max(1, min(elbow_point))

        self.k = optimal_k
    
    def distances(self, target):
        distances = [abs(target - point) for point in self.centroids]

        return distances.index(min(distances))
    
    def update_centroids(self):
        updated_points = []

        for rand_pt, points in self.clusters.items():
            if points: 
                updated_points.append(sum(points) // len(points))
            else:
                updated_points.append(random.choice(self.data))

        return updated_points
        
    def update_node(self):
        pattern = []

        for cluster_id, points in self.clusters.items():
            activity_range = [min(points), max(points)]
            pattern.append(activity_range)
        
        return Node(self.user_id, self.data, pattern)
    
class ClusterPatterns(Cluster):
    def __init__(self):
        super().__init__()

    def join_patterns(self, pattern_to_join):
        joined_patterns = self.data.copy() + pattern_to_join
        self.data = joined_patterns
    
    def evaluate_similarity(self, pattern1, pattern2):
        if not pattern1 or not pattern2:
            return False

        for p1, p2 in zip(pattern1, pattern2):
            d1 = abs(p1[0] - p2[0])
            d2 = abs(p1[1] - p2[1])
            average_diff = (d1 + d2) / 2
            if average_diff > self.tolerance:
                return False
        
        return True

    def get_k(self):
        distortions = []

        max_k = min(10, len(self.data))
        data = np.array(self.data)

        for k in range(1, max_k+1):
            kmeans = KMeans(n_clusters=k, random_state=42)
            kmeans.fit(data)
            distortions.append(kmeans.inertia_)
        
        deltas = np.diff(distortions)
        second_deltas = np.diff(deltas)
        elbow_point = np.argmax(second_deltas) + 2
        optimal_k = max(1, min(elbow_point))

        return optimal_k
    
    def distances(self, target):
        distances = []
        for point in self.centroids:
            d1 = abs(target[0] - point[0])
            d2 = abs(target[1] - point[1])
            distance = d1 + d2
            distances.append(distance)
        
        return distances.index(min(distances))
    
    def update_centroids(self):
        updated_points = []

        for rand_pt, points in self.clusters.items():
            if points:
                updated_points.append([sum(point[0] for point in points) // len(points), sum(point[1] for point in points) // len(points)])
            else:
                updated_points.append(random.choice(self.data))
        return updated_points
    
    def update_node(self):
        pattern = []

        for cluster_id, points in self.clusters.items():
            if points:
                average_start = sum(point[0] for point in points) // len(points)
                average_end = sum(point[1] for point in points) // len(points)
                pattern.append([average_start, average_end])
            else:
                continue
        return Node(self.user_id, self.data, pattern)

class UpdateDB(DBConnection):
    def __init__(self, user_id, daily_hours):
        self.user_id = user_id
        self.daily_hours = daily_hours

        self.input_obj = Node(self.user_id, self.daily_hours)
        self.spikes_obj = None
        self.current_obj = None
        self.updated_obj = None

        self.open()
        self.create_table(self.user_id)

    def detect_spikes(self):
        spike_detector = DetectSpikes()
        spike_detector.process_node(self.input_obj)
        spike_detector.detect_spikes()
        self.spikes_obj = spike_detector.update_node()


    def get_current_pattern(self):
        cluster = ClusterSpikes()
        cluster.process_node(self.spikes_obj)
        cluster.kmeans()
        self.current_obj = cluster.update_node()
    
    def get_updated_pattern(self):
        cluster = ClusterPatterns()
        cluster.process_node(self.current_obj)
        last_pattern = self.select_items(self.user_id, "*", self.user_id, "day", "day", [self.current_obj.day])
        if last_pattern is None or not cluster.evaluate_similarity(self.current_obj.current_pattern, last_pattern[1]):
            values = [self.user_id, self.current_obj.day, json.dumps(self.current_obj.current_pattern), json.dumps(self.current_obj.daily_hours)]
            self.insert_items(values)
            return 
        cluster.join_patterns(last_pattern)
        cluster.kmeans()
        self.updated_obj = cluster.update_node()
    
    def update_db(self):
        if self.updated_obj:
            day = self.updated_obj.day
            current_pattern = json.dumps(self.updated_obj.current_pattern)
            history = json.dumps(self.updated_obj.daily_hours)
            where_values = ["userID", "day"]
            self.update_items("currentPattern", where_values, [current_pattern, self.user_id, day])
        
    def close(self):
        self.close()
        logger.info("MySQL connection is closed")

class FetchNext(DBConnection):
    def __init__(self, user_id, pattern_obj):
        self.user_id = user_id
        self.pattern_obj = pattern_obj
        self.open()
        self.create_table(self.user_id)

    def get_next_pattern(self):
        if self.pattern_obj:
            values = [self.user_id, self.pattern_obj.day]
            where_values = ["userID", "day"]
            last_pattern = self.select_items("currenPattern", where_values, "day", "day", values)
            if last_pattern is None:
                return None
            else:
                return json.loads(last_pattern[0])
    
    def close(self):
        self.close()
        logger.info("MySQL connection is closed")
