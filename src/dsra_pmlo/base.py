# src/dsra_pmlo/base.py
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError
from matplotlib import pyplot as plt
import numpy as np
import math

# Base class for DSRA PMLO models
class DSRABase:
    # Set default values for parameters
    def __init__(self, filepath, similarity_method="MAAPE", interpolation_method="quadratic", similarity_threshold=1, target_col="Amplitude"):
        self.filepath = filepath
        self.target_col = target_col
        self.similarity_method = similarity_method
        self.interpolation_method = interpolation_method
        self.similarity_threshold = similarity_threshold
        self.sensor_data_total = None
        self.train_data = None
        self.raw_data = None

    def load_data(self, target_size=None): 
        """
        Load the target column from a data file and prepare the training data.

        target_size can resize the signal before splitting. The file must exist,
        include the target column, and contain numeric finite values.
        """
        self._validate_config()
        self._validate_target_size(target_size)

        # Load data from the file
        print(f"Loading data from: {self.filepath}")
        data_path = Path(self.filepath)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.filepath}")

        if not data_path.is_file():
            raise ValueError(f"Data path is not a file: {self.filepath}")

        try:
            self.raw_data = pd.read_csv(data_path, sep=r'\s+')
        except EmptyDataError as exc:
            raise ValueError(f"Data file is empty: {self.filepath}") from exc
        except Exception as exc:
            raise ValueError(f"Could not read data file '{self.filepath}': {exc}") from exc

        if self.raw_data.empty:
            raise ValueError(f"Data file has no rows: {self.filepath}")
        
        # Get data length of target column
        if self.target_col in self.raw_data.columns:
            try:
                data_array = pd.to_numeric(self.raw_data[self.target_col], errors="raise").to_numpy(dtype=float)
            except Exception as exc:
                raise ValueError(f"Target column '{self.target_col}' must contain only numeric values.") from exc

            if len(data_array) < 4:
                raise ValueError("Data must contain at least 4 points so both train and test data can be evaluated.")

            if not np.all(np.isfinite(data_array)):
                raise ValueError(f"Target column '{self.target_col}' contains NaN or infinite values.")

            if target_size:
                self.sensor_data_total = np.resize(data_array, target_size)
            else:
                self.sensor_data_total = data_array
                
            # Run the mode-specific training split.
            self.prepare_train_data()
            
            print(f"Successfully loaded '{self.target_col}'.\n")
        else:
            available = ", ".join(self.raw_data.columns)
            raise ValueError(f"Target column '{self.target_col}' not found. Available columns: {available}")

    def prepare_train_data(self):
        """
        Split the loaded signal into testing and training parts.

        The first 40% is kept for testing. The last 60% is used for training.
        """
        # First 40% is reserved for testing; the remaining 60% is used for training.
        split_idx = round(len(self.sensor_data_total) * 0.4)
        
        self.train_data = self.sensor_data_total[split_idx:]  
        self._validate_data_ready(self.train_data, "Training data")
        print(f"Base Data Split: Train size = {len(self.train_data)} (Last 60%)")
        
    def get_data_summary(self):
        """
        Print basic data lengths and plot the full signal and training signal.

        This is mainly for checking that the selected file and column look right.
        """
        if self.sensor_data_total is not None:
            print(f"=== Data summary for {self.target_col} ===")
            print(f"Total length (training + testing): {len(self.sensor_data_total)}")
            print(f"Training length: {len(self.train_data)}\n")

            # Plot total data
            plt.plot(self.sensor_data_total)
            plt.title(f"Target Feature: {self.target_col}")
            plt.show()
            
            # Plot training data
            plt.plot(self.train_data)
            plt.title(f"Training Feature: {self.target_col}")
            plt.show()
            
    def interp_linear(self, x, y):
        """
        Rebuild a signal between selected samples using linear interpolation.

        x contains sample indices and y contains sample values. Indices must be
        in increasing order.
        """
        if len(x) != len(y):
            raise ValueError("Interpolation x and y must have the same length.")

        if len(x) < 2:
            raise ValueError("At least 2 measurement points are required for interpolation.")

        if any(x[i] <= x[i - 1] for i in range(1, len(x))):
            raise ValueError("Measurement indices must be strictly increasing.")

        res = []
        for i in range(1, len(x)):
            slope = (y[i] - y[i - 1]) / (x[i] - x[i - 1])
            l = y[i] - slope * x[i]
            res.extend([slope * x_betw + l for x_betw in range(x[i - 1], x[i])])
        res.append(y[-1])
        return np.array(res)
    
    def interp_quadratic(self, x, y):
        """
        Rebuild a signal between selected samples using quadratic interpolation.

        If only two samples are available, the method falls back to linear
        interpolation.
        """
        if len(x) != len(y):
            raise ValueError("Interpolation x and y must have the same length.")

        if len(x) < 2:
            raise ValueError("At least 2 measurement points are required for interpolation.")

        if any(x[i] <= x[i - 1] for i in range(1, len(x))):
            raise ValueError("Measurement indices must be strictly increasing.")

        if len(x) == 2:
            print('Use linear interpolation instead of polinomial when number of samples equals 2')
            return self.interp_linear(x, y)
        
        a = ((y[2] - y[0]) / ((x[2] - x[0]) * (x[2] - x[1])) - 
             (y[1] - y[0]) / ((x[1] - x[0]) * (x[2] - x[1])))
        b = (a * (x[0] ** 2 - x[1] ** 2) + y[1] - y[0]) / (x[1] - x[0])
        c = y[0] - a * x[0] ** 2 - b * x[0]
        res = [a * x_betw ** 2 + b * x_betw + c for x_betw in range(x[0], x[2])]
        for i in range(1, len(x) - 2):
            a = ((y[i + 2] - y[i]) / ((x[i + 2] - x[i]) * (x[i + 2] - x[i + 1])) - 
                 (y[i + 1] - y[i]) / ((x[i + 1] - x[i]) * (x[i + 2] - x[i + 1])))
            b = (a * (x[i] ** 2 - x[i + 1] ** 2) + y[i + 1] - y[i]) / (x[i + 1] - x[i])
            c = y[i] - a * x[i] ** 2 - b * x[i]
            res.extend([a * x_betw ** 2 + b * x_betw + c for x_betw in range(x[i + 1], x[i + 2])])  
        res.append(y[-1])
        return np.array(res)
    
    def cor(self, f, g):
        """
        Return correlation similarity between two signals as a percentage.

        A higher value means the reconstructed signal is closer to the original.
        """
        denom = math.sqrt(np.dot(f, f)) * math.sqrt(np.dot(g, g))
        if denom == 0:
            raise ValueError("Correlation is undefined for all-zero signals.")

        return 100 * np.dot(f, g) / denom
    
    def MAAPE(self, f,g):
        """
        Return the MAAPE error between two signals as a percentage.

        A lower value means the reconstructed signal is closer to the original.
        """
        EPSILON = 1e-10
        return np.mean(np.arctan(np.abs((f - g) / (f + EPSILON)))) * 100

    def measure(self, params, *other):                                                        
        """
        Return the number of samples used by one E and S pair.

        If the reconstructed signal does not meet the threshold, this returns
        the full data length so the optimizer will avoid that E and S pair.
        """
        data, interpolation, error, min_sim = other
        data = self._validate_data_ready(data)
        E, S = params
        if not all(np.isfinite(value) for value in (E, S)):
            return len(data)

        prev_meas = 0
        new_meas = max(1, int(round(E)))
        measurements = []
        days = []
        slope = 0
        while new_meas < len(data):
            slope = abs((data[new_meas] - data[prev_meas])) / (new_meas - prev_meas) #prev_meas and new_meas are used as an index (days)
            measurements.append(data[prev_meas])                                   
            days.append(prev_meas)                                             
            prev_meas, new_meas = new_meas, new_meas + max(1, int(round(E - S * slope)))
            
        measurements.append(data[prev_meas])
        days.append(prev_meas)
        num_of_meas = len(days)
        
        if prev_meas != len(data) - 1: # to include the last measurement, in case the last point from DSRA is not the last point of the oriognal data (to include the last measurements even it is not considered)
            measurements.append(data[-1])
            days.append(len(data) - 1)
        
        if interpolation == 'linear':
            interp_sampl = self.interp_linear(days, measurements)
        else:
            interp_sampl = self.interp_quadratic(days, measurements)

        if error == 'correlation':
            similarity = self.cor(data, interp_sampl)
            return num_of_meas if similarity >= min_sim else len(data)
        else:
            similarity = self.MAAPE(data, interp_sampl)
            return num_of_meas if similarity <= min_sim else len(data)

    def cal_dsra_grid(self, range_e, range_s):
        """
        Test many E and S pairs and keep the pairs that meet the threshold.

        Returns E values, S values, and the number of selected samples for each
        valid pair.
        """
        z_vals, x_vals, y_vals = [], [], []
        data = self._validate_data_ready(self.train_data, "Training data")
        
        for e_value in range_e:
            for s_value in range_s:
                similarity, _, _, indices, _, _ = self.reconstruct_signal(e_value, s_value, data=data)
                if self.similarity_method == 'correlation':
                    criterion = similarity >= self.similarity_threshold
                else:
                    criterion = similarity <= self.similarity_threshold
                
                if criterion:
                    z_vals.append(len(indices))
                    x_vals.append(e_value)
                    y_vals.append(s_value)
                    
        return x_vals, y_vals, z_vals


    def reconstruct_signal(self, E, S, data=None):
        """
        Sample and reconstruct a signal using DSRA.

        E is the base sampling interval. S controls how much the local slope
        changes the next interval. If data is not provided, training data is
        used.

        Returns the error/similarity value, reconstructed signal, selected
        sample values, selected sample indices, sampling reduction percentage,
        and number of selected samples.
        """
        if data is None:
            data = self.train_data

        data = self._validate_data_ready(data)
        if not all(np.isfinite(value) for value in (E, S)):
            raise ValueError("E and S must be finite numbers.")
            
        prev_meas = 0
        new_meas = max(1, int(round(E))) 
        measurements = []
        indices = [] # to store indices of measurements
        
        # DSRA sampling loop
        while new_meas < len(data):
            denom = max(1, new_meas - prev_meas)
            slope = abs((data[new_meas] - data[prev_meas])) / denom
            measurements.append(data[prev_meas])
            indices.append(prev_meas)
            # Update indices based on E and S.
            prev_meas, new_meas = new_meas, new_meas + max(1, int(round(E - S * slope)))
            
        # Ensure the last points are included
        measurements.append(data[prev_meas])
        indices.append(prev_meas)
        if prev_meas != len(data) - 1:
            measurements.append(data[-1])
            indices.append(len(data) - 1)
            
        # Interpolation
        if self.interpolation_method == 'linear':
            reconstructed = self.interp_linear(indices, measurements)
        else:
            reconstructed = self.interp_quadratic(indices, measurements)
            
        # Metrics
        if len(reconstructed) != len(data):
            raise ValueError("Reconstructed signal length does not match source data length.")

        if self.similarity_method == 'correlation':
            similarity = self.cor(data, reconstructed)
        else:
            similarity = self.MAAPE(data, reconstructed)
        
        # Record number of sampling
        num_samples = len(indices) 
        
        # Caculate reduced percentage
        reduction = abs((round(num_samples / len(data), 2) * 100) - 100)
        
        return similarity, reconstructed, measurements, indices, reduction, num_samples
    
    def plot_reconstruction(self, E, S, data=None, title_prefix="Final Evaluation"):
        """
        Plot the original signal, reconstructed signal, and selected samples.

        If data is not provided, training data is used. Test data should be
        passed in when plotting the final test evaluation.
        """
        # If test data is passed in, use it; otherwise use training data.

        if data is None:
            print("Plotting training data because no data was provided.")
            target_data = self.train_data
        else:
            target_data = data
        
        # Get result
        sim, recon, meas, idx, red, num_samples = self.reconstruct_signal(E, S, data=target_data)
        
        plt.figure(figsize=(12, 5))
        plt.plot(target_data, color='orange', label='Original Signal', alpha=0.8)
        plt.plot(
            recon,
            linestyle=(0, (7, 7)),
            color='blue',
            label=f'DSRA Reconstruction (E={E:.4f}, S={S:.4f})',
        )

        signal_range = np.max(target_data) - np.min(target_data)
        baseline = np.min(target_data) - 0.1 * signal_range
        plt.scatter(
            idx,
            np.full(len(idx), baseline),
            edgecolors='black',
            facecolors='tab:blue',
            s=35,
            label='Sampling Points',
            zorder=3,
        )
        plt.axhline(y=baseline, color='gray', linestyle='--', alpha=0.5)
        
        # Show how many samples are used 
        plt.title(f"Number of samples = {num_samples}, error = {sim} %, sampling reduced by = {red}%")
        plt.xlabel("Time(S)")
        plt.ylabel("Data value")
        plt.legend(loc='upper right')
        plt.grid(ls='--')
        plt.show()
        
        print(f"Testing Results -> Samples: {num_samples}, Reduction: {red:.2f}%, Error: {sim:.4f}%")
        
    def evaluate_test_set(self, E, S, split_ratio=0.4, new_filepath=None):
        """
        Evaluate optimized E and S on the held-out test data.

        By default, the first 40% of the loaded signal is used as testing data.
        The result is printed and plotted.
        """
        # Handle newly passed in file
        if new_filepath:
            print(f"Loading new test file: {new_filepath}")
            
        # Prepare test data
        self._validate_data_ready(self.sensor_data_total, "Total data")
        split_idx = round(len(self.sensor_data_total) * split_ratio)
        test_data = self.sensor_data_total[:split_idx]
        test_data = self._validate_data_ready(test_data, "Test data")

        print(f"\n--- TEST SET EVALUATION (First {int(split_ratio*100)}%) ---")
        print(f"Testing data length: {len(test_data)}")
        print(f"Parameters used: E={E}, S={S}")

        # Call reconstruct_signal logic
        sim, recon, meas, idx, red, num_samples = self.reconstruct_signal(E, S, data=test_data)

        # Print result
        print(f"Samples used in Test Set: {num_samples}")
        print(f"Data reduction in Test Set: {red:.2f}%")
        print(f"MAAPE error in Test Set: {sim:.4f}%")

        # Visulaize 
        self.plot_reconstruction(E, S, data=test_data, title_prefix="Test Evaluation")
    
        return sim, red, num_samples
    
    def _validate_config(self):
        if self.interpolation_method not in {"linear", "quadratic"}:
            raise ValueError("interpolation_method must be 'linear' or 'quadratic'.")

        if self.similarity_method not in {"MAAPE", "correlation"}:
            raise ValueError("similarity_method must be 'MAAPE' or 'correlation'.")

        if not isinstance(self.similarity_threshold, (int, float)) or not np.isfinite(self.similarity_threshold):
            raise ValueError("similarity_threshold must be a finite number.")

        if self.similarity_method == "MAAPE" and self.similarity_threshold <= 0:
            raise ValueError("MAAPE similarity_threshold must be greater than 0.")

        if not isinstance(self.target_col, str) or not self.target_col:
            raise ValueError("target_col must be a non-empty string.")

    def _validate_target_size(self, target_size):
        if target_size is None:
            return

        if not isinstance(target_size, int):
            raise ValueError("target_size must be an integer or None.")

        if target_size < 4:
            raise ValueError("target_size must be at least 4 so both train and test data have enough points.")

    def _validate_data_ready(self, data, label="data"):
        if data is None:
            raise ValueError(f"{label} is not loaded. Call load_data() first.")

        data = np.array(data).flatten()
        if len(data) < 2:
            raise ValueError(f"{label} must contain at least 2 points.")

        if not np.all(np.isfinite(data)):
            raise ValueError(f"{label} contains NaN or infinite values.")

        return data

    def _validate_bounds(self, bounds):
        if bounds is None:
            raise ValueError("Optimization bounds are required.")

        if len(bounds) != 2:
            raise ValueError("Bounds must contain exactly two ranges: one for E and one for S.")

        clean_bounds = []
        for label, bound in zip(("E", "S"), bounds):
            if len(bound) != 2:
                raise ValueError(f"{label} bound must be a pair: (lower, upper).")

            lower, upper = bound
            if not all(isinstance(value, (int, float)) and np.isfinite(value) for value in (lower, upper)):
                raise ValueError(f"{label} bounds must be finite numbers.")

            if lower >= upper:
                raise ValueError(f"{label} lower bound must be less than upper bound.")

            clean_bounds.append((lower, upper))

        return clean_bounds
