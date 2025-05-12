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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

class DailyBehavior:
    def __init__(self, user_id, daily_hours, behavior_data, z_threshold=1.4):
        self.user_id = user_id
        self.daily_hours = daily_hours
        self.behavior_data = behavior_data
        self.activity_spikes = []
        self.z_threshold = z_threshold
        
        day = datetime.now()
        self.week_day = day.strftime("%A")
    
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
                f"Index {i}: Value={new_value}, Mean={mean:.2f}, Std={std:.2f}, Z-Score={z_score:.2f}"
            )

            if z_score > self.z_threshold:
                self.activity_spikes.append(new_value)
                logging.info(f"Index {i}: Spike detected with Z-Score={z_score:.2f} going over {self.z_threshold:.2f}")
        
        logging.info(f"User {self.user_id} detected {len(self.activity_spikes)} spikes.")

class TrackOverallBehavior:
    def __init__(self):
        self.filename = os.path.join("src/behavior_data", "behavior.json")
        with open(self.filename, "r") as f:
            self.behaviors = json.load(f)
        self.data_count = 0

    def add_behavior(self, node):
        if node not in self.behaviors:
            with open(self.filename, "w") as f:
                self.behaviors[node.week_day].append(node.activity_spikes)
                json.dump(self.behaviors, f)
        
        self.data_count += 1



