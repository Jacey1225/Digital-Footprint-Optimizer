import matplotlib.pyplot as plt
import os
import logging
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.behaviors import DailyBehavior

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Define multiple mock datasets for testing
mock_datasets = {
    "Scenario 1: Gradual Increase with Spikes": [
        0.3, 0.32, 0.31, 0.33, 0.34,  # Baseline activity
        0.35, 0.36, 0.37, 0.38, 0.39,  # Gradual increase
        0.8, 0.9, 0.85, 0.95, 0.9,     # Spike
        0.3, 0.31, 0.32, 0.33, 0.34    # Drop back to baseline
    ],
    "Scenario 2: High Variability with Spikes": [
        0.3, 0.5, 0.4, 0.6, 0.35,      # Fluctuations
        0.9, 1.0, 0.95, 1.0, 0.98,     # Spike
        0.3, 0.31, 0.3, 0.32, 0.33,    # Drop back to baseline
        0.4, 0.42, 0.41, 0.43, 0.44    # Slightly higher baseline
    ],
    "Scenario 3: Flat Baseline with Single Spike": [
        0.3, 0.3, 0.3, 0.3, 0.3,       # Flat baseline
        1.0,                           # Single spike
        0.3, 0.3, 0.3, 0.3, 0.3        # Return to baseline
    ],
    "Scenario 4: Multiple Spikes": [
        0.3, 0.32, 0.31, 0.33, 0.34,   # Baseline
        0.8, 0.9, 0.85, 0.95, 0.9,     # Spike 1
        0.3, 0.31, 0.32, 0.33, 0.34,   # Drop back to baseline
        0.9, 1.0, 0.95, 1.0, 0.98,     # Spike 2
        0.3, 0.31, 0.3, 0.32, 0.33     # Drop back to baseline
    ]
}

# Test each dataset
for scenario, mock_data in mock_datasets.items():
    print(f"\nRunning {scenario}...")
    
    # Create an instance of DailyBehavior with the mock data
    user_id = "test_user"
    passw = "test_password"
    z_threshold = 1.3  # Set a z-score threshold for spike detection
    daily_behavior = DailyBehavior(user_id, passw, mock_data, z_threshold=z_threshold)

    # Run the average_spikes function
    daily_behavior.average_spikes()

    # Print the detected spikes
    print(f"Detected spikes for {scenario}: {daily_behavior.activity_spikes}")

    # Visualize the results
    plt.figure(figsize=(10, 6))
    plt.plot(mock_data, label="Mock Data", marker="o")
    for spike in daily_behavior.activity_spikes:
        plt.axvline(x=spike, color="red", linestyle="--", label=f"Spike at index {spike}")
    plt.title(f"Spike Detection - {scenario}")
    plt.xlabel("Index")
    plt.ylabel("Activity Level")
    plt.legend()
    plt.show()