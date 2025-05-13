import logging
import os
import sys
import unittest
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.behaviors import DailyBehavior

class TestKMeansClustering(unittest.TestCase):
    def setUp(self):
        # Mock data for testing
        self.user_id = "test_user"
        self.password = "test_password"
        self.daily_hours = [0.0, 0.01, 0.3, 0.64, 0.89, 0.1, 0.01]  # Example dataset
        self.k = 2  # Number of clusters
        self.iterations = 10  # Maximum iterations for clustering
        self.current_pattern = [0.0, 0.05, 0.5, 0.78, 0.2, 0.1, 0.01]

        # Create an instance of DailyBehavior
        self.behavior = DailyBehavior(
            user_id=self.user_id,
            password=self.password,
            daily_hours=self.daily_hours,
            z_threshold=1.5,
            k=self.k
        )

    def test_kmeans_clustering(self):
        # Run the k-means clustering function
        clusters = self.behavior.kmeans_clustering(current_pattern=self.current_pattern, new_data=self.daily_hours, max_iterations=self.iterations, num_clusters=self.k)

        # Assert that the number of clusters matches k
        self.assertEqual(len(clusters), self.k, "Number of clusters does not match k")

        # Assert that all data points are assigned to a cluster
        all_points = [point for cluster in clusters.values() for point in cluster]
        self.assertCountEqual(all_points, self.daily_hours, "Not all data points are assigned to clusters")

        # Print the clusters for verification
        for centroid, points in clusters.items():
            print(f"Centroid: {centroid}, Points: {points}")

if __name__ == "__main__":
    unittest.main()
