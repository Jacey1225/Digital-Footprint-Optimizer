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
        """
        Closes the database connection and cursor if the connection is active.

        This method checks if the database connection is currently active. If so, 
        it closes the cursor and the connection, and logs a message indicating 
        that the MySQL connection has been closed.
        """
        if self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            logger.info("MySQL connection is closed")
    
    def open(self):
        """
        Opens a connection to the MySQL database if it is not already connected.

        This method checks the current connection status and attempts to establish
        a connection to the database using the provided configuration. If the connection
        is successful, it initializes the cursor for executing queries. Logs an error
        message if the connection fails.

        Raises:
            mysql.connector.Error: If an error occurs while connecting to the database.
        """
        if not self.connection.is_connected():
            try:
                self.connection = mysql.connector.connect(**self.db_config)
                self.cursor = self.connection.cursor()
                logger.info("MySQL connection is opened")
            except Error as e:
                logger.error("Error while connecting to MySQL", e)
    
    def find(self, where_values, values):
        """
        Executes a SQL query to find rows in the 'behaviors' table that match the specified conditions.

        Args:
            where_values (list): A list of column names to be used in the WHERE clause of the SQL query.
                                 The list must contain exactly two column names.
            values (list): A list of values corresponding to the columns specified in `where_values`.
                           The list must contain exactly two values.

        Returns:
            list: A list of rows that match the specified conditions, retrieved from the database.

        Raises:
            Error: If an error occurs during the execution of the SQL query, it is logged, and the
                   database transaction is rolled back.
        """
        try:
            count_query = f"""SELECT * FROM behaviors WHERE {where_values[0]} = %s AND {where_values[1]} = %s;"""
            self.cursor.execute(count_query, (values[0], values[1]))
            count = self.cursor.fetchall()
            return count
        except Error as e:
            logger.error(f"Error counting rows: {e}")
            self.connection.rollback()

    def create_table(self):
        """
        Creates a table named 'behaviors' in the database if it does not already exist.

        The table contains the following columns:
            - userID: A VARCHAR(255) that serves as the primary key.
            - day: A VARCHAR(255) representing the day.
            - currentPattern: A TEXT field storing the current behavior pattern.
            - history: A TEXT field storing the history of behaviors.

        Commits the changes to the database if the table is created successfully.
        Rolls back the transaction and logs an error if an exception occurs.

        Raises:
            Error: If there is an issue executing the SQL query or committing the transaction.
        """
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
        """
        Selects items from the 'behaviors' table in the database based on the provided parameters.
        Args:
            select_value (str): The column to select from the table.
            where_values (list): A list of column names to use in the WHERE clause.
            order_value (str): The column to use for ordering the results.
            values (list): A list of values corresponding to the WHERE clause columns.
            fetchall (bool, optional): If True, fetch all rows; if False, fetch a single row. Defaults to True.
            desc (bool, optional): If True, order results in descending order; if False, order in ascending order. Defaults to True.
        Returns:
            list or tuple: The fetched rows from the database. Returns a list if fetchall is True, otherwise a single tuple.
        Raises:
            ValueError: If the input types for the arguments are invalid.
            Error: If there is an issue executing the SQL query.
        Notes:
            - The method constructs a SQL query dynamically based on the input parameters.
            - If `where_values` contains more than one column, the query will include an additional condition in the WHERE clause.
            - The method uses parameterized queries to prevent SQL injection.
            - Logs errors and rolls back the transaction in case of a database error.
        """
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
        """Inserts a new record into the 'behaviors' table in the database.

        Args:
            values (list): A list containing four elements:
                - userID (str): The ID of the user.
                - day (str): The day associated with the behavior.
                - currentPattern (str): The current pattern of behavior.
                - history (str): The history of behaviors.

        Raises:
            ValueError: If the input 'values' is not a list.
            Error: If there is an issue executing the database query, logs the error and rolls back the transaction.

        Notes:
            - This method assumes that the database connection and cursor are already initialized.
            - The method uses parameterized queries to prevent SQL injection."""
        if (not isinstance(values, list)):
            raise ValueError("Invalid input types. Expected strings for user_id, day, currentPattern, and history.")
        try:
            insert_query = f"""
            INSERT INTO behaviors
            (userID, day, currentPattern, history)
            VALUES (%s, %s, %s, %s);
            """
            self.cursor.execute(insert_query, (values[0], values[1], values[2], values[3]))
            self.connection.commit()
        except Error as e:
            logger.error(f"Error inserting items: {e}")
            self.connection.rollback()

    def update_items(self, value_to_update, where_values, values):
        """Updates a specific field in the 'behaviors' table based on given conditions.

        Args:
            value_to_update (str): The column name to update.
            where_values (list): A list containing two column names to use in the WHERE clause.
            values (list): A list containing three values - the new value for the column to update 
                           and the two values to match in the WHERE clause.

        Raises:
            ValueError: If the input types are not as expected.
            Error: If an error occurs during the database operation.

        Notes:
            - The method constructs an SQL query dynamically using the provided column names and values.
            - It ensures the database changes are committed if the operation is successful.
            - In case of an error, the transaction is rolled back and the error is logged."""
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
            WHERE {where_values[0]} = %s AND {where_values[1]} = %s;
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
        self.z_threshold = max(self.z_threshold, new_threshold)

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
        """
        Joins the provided pattern with the existing data and updates the internal data.

        Args:
            pattern_to_join (list): A list of patterns to be joined with the existing data.

        Returns:
            None: The method updates the internal `self.data` attribute in place.
        """
        joined_patterns = self.data.copy() + pattern_to_join
        self.data = joined_patterns
    
    def evaluate_similarity(self, pattern1, pattern2):
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
