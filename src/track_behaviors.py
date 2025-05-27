import os
import numpy as np
import logging
import json
import mysql.connector
from mysql.connector import Error
from sklearn.cluster import KMeans
import random
from datetime import datetime
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.use_DB import DBConnection
logger = logging.getLogger(__name__)

class Node:
    """
    Represents a user behavior tracking node that monitors daily activity patterns.

    Attributes:
        user_id (str): The unique identifier for the user.
        day (str): The current day of the week, automatically set to the day of initialization.
        daily_hours (float): The number of hours the user spends daily on tracked activities.
        current_pattern (any): The current behavioral pattern associated with the user (default is None).
        z_threshold (float): The Z-score threshold for detecting significant deviations (default is 1.8).
        min_z_threshold (float): The minimum Z-score threshold for detecting minor deviations (default is 0.65).
        iterations (int): The number of iterations for pattern analysis (default is 10).

    Methods:
        None defined in this class.
    """
    def __init__(self, user_id, daily_hours, pattern=None, z_threshold=1.8, min_z_threshold=0.65, tolerance=2.5, iterations=10):
        self.user_id = user_id
        self.day = datetime.now().strftime("%A")
        self.daily_hours = daily_hours
        self.current_pattern = pattern

        self.z_threshold = z_threshold
        self.min_z_threshold = min_z_threshold
        self.iterations = iterations
        self.tolerance = tolerance
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
        """
        Processes the given node by setting it as the current node and updating the z_threshold.

        Args:
            node (object): The node to process. It must have a `z_threshold` attribute.

        Raises:
            ValueError: If the provided node is None.
        """
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
        self.z_threshold = new_threshold if new_threshold > 0 else self.z_threshold

    def z_score(self, new_value):
        if self.std == 0:
            return 0
        else: 
            return (new_value - self.mean) / self.std
    
    def detect_spikes(self):
        """
        Detects spikes in daily activity hours based on z-scores and thresholds.
        This method iterates through the daily activity hours of a node, calculates
        the z-score for each value, and identifies spikes where the z-score exceeds
        a dynamically adjusted threshold. Detected spikes are stored in the 
        `activity_spikes` list.
        Steps:
        1. For each daily hour value, calculate the standard deviation.
        2. Skip processing if the standard deviation is below 0.1.
        3. Adjust the z-score threshold dynamically.
        4. Calculate the z-score for the current value.
        5. If the z-score exceeds the threshold, record the index as a spike.
        6. Update the previous mean and standard deviation for future calculations.
        Attributes:
            self.node.daily_hours (list): List of daily activity hours for the node.
            self.std (float): Current standard deviation of the activity hours.
            self.mean (float): Current mean of the activity hours.
            self.prev_mean (float): Previous mean of the activity hours.
            self.prev_std (float): Previous standard deviation of the activity hours.
            self.z_threshold (float): Current z-score threshold for detecting spikes.
            self.activity_spikes (list): List of indices where spikes are detected.
        Raises:
            AttributeError: If required attributes like `self.node.daily_hours` or
                            methods like `self.get_std`, `self.z_score`, or 
                            `self.adjust_z_threshold` are not defined.
        """
        logger.info(f"Detecting Spikes: {self.node.daily_hours}")
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
        """
        Perform k-means clustering on the dataset.
        This method partitions the data into `k` clusters by iteratively assigning
        data points to the nearest centroid and updating the centroids based on the
        mean of the assigned points. The process continues until the centroids
        stabilize or the maximum number of iterations is reached.
        Returns:
            dict: A dictionary where the keys are cluster indices and the values
                  are lists of data points belonging to each cluster. If the dataset
                  contains fewer than 2 points, a single cluster containing all
                  points is returned.
        Attributes:
            self.data (list): The dataset to be clustered.
            self.k (int): The number of clusters to form.
            self.iterations (int): The maximum number of iterations for the algorithm.
            self.centroids (list): The current centroids of the clusters.
            self.clusters (dict): The current assignment of data points to clusters.
        Notes:
            - The centroids are initialized by randomly sampling `k` points from the dataset.
            - The `distances` method is used to determine the nearest centroid for each data point.
            - The `update_centroids` method is used to calculate the new centroids based on the
              mean of the points in each cluster.
        """
        if len(self.data) < 2:
            return {0: self.data}
        
        self.centroids = random.sample(self.data, self.k)
        self.centroids = [centroid for centroid in self.centroids]

        self.clusters = {i: [] for i in range(len(self.centroids))}
        for i in range(self.iterations):
            new_clusters = {i: [] for i in range(len(self.centroids))}
            for j in range(len(self.data)):
                index = self.distances(self.data[j])
                new_clusters[index].append(self.data[j])

            new_centroids = self.update_centroids()
            if new_centroids == self.centroids:
                break
            else:
                self.centroids = new_centroids
                self.clusters = new_clusters

class ClusterSpikes(Cluster):
    def __init__(self):
        super().__init__()
    
    def get_k(self):
        """
        Determines the optimal number of clusters (k) for KMeans clustering 
        using the "elbow method" based on the distortions (inertia) of the 
        clustering results.

        The method calculates the first and second derivatives of the distortions 
        to identify the "elbow point," which represents the optimal number of clusters.

        Attributes:
            self.data (list or array-like): The input data to be clustered.
            self.k (int): The optimal number of clusters determined by the method.

        Steps:
            1. Compute distortions for k values ranging from 1 to min(10, len(self.data)).
            2. Calculate the first and second derivatives of the distortions.
            3. Identify the elbow point as the index where the second derivative is maximized.
            4. Set the optimal k to the elbow point, ensuring it is at least 1.

        Notes:
            - If the second derivative array has fewer than 2 elements, the method defaults 
              the optimal k to 1.
            - The method uses a random state of 42 for reproducibility in KMeans.

        Returns:
            None: The optimal number of clusters is stored in the `self.k` attribute.
        """
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

        optimal_k = max(1, int(elbow_point))

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
        self.shift = False

    def join_patterns(self, pattern_to_join):
        """
        Joins the provided pattern with the existing data and updates the internal data.

        Args:
            pattern_to_join (list): A list of patterns to be joined with the existing data.

        Returns:
            None: The method updates the internal `self.data` attribute in place.
        """
        joined_patterns = self.data.copy() + pattern_to_join
        self.data = joined_patterns
    
    def evaluate_similarity(self, target_pattern, others):
        """
        Evaluates the similarity between two patterns based on a tolerance threshold.
        Args:
            pattern1 (list of tuples): The first pattern, where each tuple contains two numeric values.
            pattern2 (list of tuples): The second pattern, where each tuple contains two numeric values.
        Returns:
            bool: True if the average difference between corresponding elements of the patterns 
                  is within the specified tolerance for all elements, False otherwise.
        Notes:
            - The method assumes that `self.tolerance` is defined and represents the maximum 
              allowable average difference between corresponding elements of the patterns.
            - If either pattern1 or pattern2 is empty or None, the method returns False.
        """
        if not target_pattern or not others:
            return False
        
        sims = 0
        for target in target_pattern:
            for other in others:
                d1 = abs(target[0] - other[0])
                d2 = abs(target[1] - other[1])
                average_diff = (d1 + d2) // 2
                if average_diff < self.tolerance:
                    sims += 1
                    break
        
        if sims >= (len(target_pattern) // 2):
            self.shift = 0
            return True
        
        self.shift = 1
        return False

    def get_k(self):
        """
        Determines the optimal number of clusters (k) for KMeans clustering 
        using the "elbow method" based on the second derivative of distortions.
        The function calculates distortions for k values ranging from 1 to the 
        minimum of 10 or the length of the dataset. It then computes the first 
        and second derivatives of the distortions to identify the "elbow point," 
        which corresponds to the optimal number of clusters.
        Returns:
            int: The optimal number of clusters (k), constrained to be at least 1.
        """
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
        optimal_k = max(1, int(elbow_point))

        self.k = optimal_k
    
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
        logger.info(f"Proceessing Clusters for DB: {self.clusters}")

        for cluster_id, points in self.clusters.items():
            if points:
                average_start = sum(point[0] for point in points) // len(points)
                average_end = sum(point[1] for point in points) // len(points)
                pattern.append([average_start, average_end])
            else:
                continue
        return Node(self.user_id, self.data, pattern)

class UpdateDB(DBConnection):

    """
    A class to manage and update user behavior patterns in a database.
    Attributes:
        user_id (int): The ID of the user.
        daily_hours (list): A list of daily hours representing user activity.
        input_obj (Node): A Node object initialized with user_id and daily_hours.
        spikes_obj (Node): A Node object containing detected spikes in user activity.
        current_obj (Node): A Node object representing the current behavior pattern.
        updated_obj (Node): A Node object representing the updated behavior pattern.
    Methods:
        __init__(user_id, daily_hours):
            Initializes the UpdateDB object and sets up the database table for the user.
        detect_spikes():
            Detects spikes in user activity and updates the spikes_obj attribute.
        get_current_pattern():
            Clusters the detected spikes to determine the current behavior pattern and updates the current_obj attribute.
        get_updated_pattern():
            Evaluates the current pattern against the last stored pattern in the database.
            Updates the database with a new pattern if necessary or merges patterns and updates the updated_obj attribute.
        update_db():
            Updates the database with the updated behavior pattern if available.
        close():
            Closes the database connection and logs the closure.
    """
    def __init__(self, user_id, daily_hours):
        super().__init__("behaviors")
        self.user_id = user_id
        self.daily_hours = daily_hours

        self.input_obj = Node(self.user_id, self.daily_hours)
        self.spikes_obj = None
        self.current_obj = None
        self.updated_obj = None

        self.open()

    def detect_spikes(self):
        spike_detector = DetectSpikes()
        spike_detector.process_node(self.input_obj)
        spike_detector.detect_spikes()
        self.spikes_obj = spike_detector.update_node()
        logger.info(f"Spikes detected: {self.spikes_obj.current_pattern}")


    def get_current_pattern(self):
        cluster = ClusterSpikes()
        cluster.process_node(self.spikes_obj)
        cluster.get_k()
        cluster.kmeans()
        self.current_obj = cluster.update_node()
        logger.info(f"Current pattern: {self.current_obj.current_pattern}")
    
    def get_updated_pattern(self):
        cluster = ClusterPatterns()
        cluster.process_node(self.current_obj)

        last_patterns = self.special_select("currentPattern", "userID", self.user_id)
        if last_patterns:
            patterns = []
            for pattern in last_patterns:
                patterns.extend(json.loads(pattern[0][0]))

        if last_patterns is None or not cluster.evaluate_similarity(self.current_obj.current_pattern, last_patterns):
            where_values = ["userID", "day", "currentPattern", "history", "shift"]
            values = [self.user_id, self.current_obj.day, json.dumps(self.current_obj.current_pattern), json.dumps(self.current_obj.daily_hours), 0]
            self.insert_items(where_values, values)
            logger.info(f"Inserted new pattern: {self.current_obj.current_pattern}")
            return 
        
        cluster.join_patterns(last_patterns)

        cluster.get_k()
        cluster.kmeans()

        self.updated_obj = cluster.update_node()
    
    def update_db(self):
        if self.updated_obj:
            day = self.updated_obj.day
            current_pattern = json.dumps(self.updated_obj.current_pattern)
            history = json.dumps(self.updated_obj.daily_hours)
            where_values = ["userID", "day"]
            values_to_update = ["currentPattern", "history", "shift"]
            values = []
            self.update_items("currentPattern", where_values, [current_pattern, self.user_id, day])
            logger.info(f"Updated pattern in DB: {self.updated_obj.current_pattern}")
        else:
            logger.info("No updated pattern to save in DB.")
        
class FetchNext(DBConnection):
    """
    A class to fetch the next pattern for a user from the database.
    Inherits from:
        DBConnection: A base class for handling database connections.
    Attributes:
        user_id (int): The ID of the user.
        pattern_obj (object): An object containing pattern-related data.
    Methods:
        __init__(user_id, pattern_obj):
            Initializes the FetchNext instance, opens the database connection, 
            and creates a table for the user if it doesn't exist.
        get_next_pattern():
            Retrieves the next pattern for the user based on the provided pattern object.
            Returns the pattern as a JSON object or None if no pattern is found.
        close():
            Closes the database connection and logs the closure.
    """
    def __init__(self, user_id):
        super().__init__("behaviors")
        self.user_id = user_id
        self.day = datetime.now().strftime("%A")
        self.open()

    def get_next_pattern(self):
        values = [self.user_id, self.day]
        where_values = ["userID", "day"]
        last_pattern = self.select_items("currentPattern", where_values, "day", values, 1)
        if last_pattern is None:
            return None
        else:
            logger.info(f"Last pattern: {last_pattern}")
            return json.loads(last_pattern[0][0])