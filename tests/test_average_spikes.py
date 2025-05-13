import matplotlib.pyplot as plt
import os 
import logging 

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.behaviors import DailyBehavior

# Mock data for testing
mock_data = [1, 2, 2, 3, 100, 3, 2, 2, 1, 50, 2, 2, 80, 100, 80, 2, 2, 1]

# Create an instance of DailyBehavior wißth mock data
user_id = 1
behavior_data = None
z_threshold = 1.3  # Set a z-score threshold for spike detection
daily_behavior = DailyBehavior(user_id, mock_data, behavior_data, z_threshold)

# Run the average_spikes function
daily_behavior.average_spikes()

# Visualize the results
plt.figure(figsize=(10, 6))
plt.plot(mock_data, label="Mock Data", marker="o")
for spike in daily_behavior.activity_spikes:
    spike_index = mock_data.index(spike)
    plt.axvline(x=spike_index, color="red", linestyle="--", label=f"Spike at index {spike_index}")

plt.title("Spike Detection Using average_spikes")
plt.xlabel("Index")
plt.ylabel("Value")
plt.legend()
plt.grid()
plt.show()