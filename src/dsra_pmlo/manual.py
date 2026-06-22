# src/dsra_pmlo/manual.py
# Manual loading class for DSRA PMLO models
from .base import DSRABase
import matplotlib.pyplot as plt
import numpy as np

class DSRAManual(DSRABase):
    # Receive parameters from user and pass to base class
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def prepare_train_data(self):
        total_len = len(self.sensor_data_total)
        
        # Manual mode uses the last 60% for training.
        split_limit = round(total_len * 0.4)
        
        self.train_data = self.sensor_data_total[split_limit:]
        print(f"Data prepared: Total={total_len}, Test Boundary={split_limit}, Training Size={len(self.train_data)}")

    # Load data manually
    def load_data(self, target_size=None):
        print("Manual loading...")
        return super().load_data(target_size=target_size)

    def plot2d(self, range_k, range_c):
        """
        Plots a scatter graph showing how E and S affect the number of measurements.
        Colors represent the density/efficiency of the measurements.
        """
        # Request calculation results from the base class
        x, y, z = self.cal_dsra_grid(range_k, range_c)
        
        if not z:
            print(" No parameters met the similarity threshold. Try adjusting range_k or range_c.")
            return

        # Visualize the results
        max_z = max(z)
        # Normalize colors based on the maximum number of measurements
        colors = [val / max_z for val in z]
        
        plt.figure(figsize=(8, 6))
        plt.scatter(x, y, c=colors, alpha=0.8, cmap='viridis')
        plt.xlabel('E')
        plt.ylabel('S')
        plt.title(f'DSRA Parameter Analysis ({self.target_col})')
        
        cbar = plt.colorbar()
        cbar.set_label('Number of Measurements')
        plt.show()

        return [z, x, y]
