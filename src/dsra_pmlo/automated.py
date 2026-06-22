# src/dsra_pmlo/automated.py
# Automated class for DSRABase, load data automatically without user input
from .base import DSRABase
import numpy as np
from scipy.optimize import dual_annealing

class DSRAAutomated(DSRABase):
    # Receive parameters from user and pass to base class
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def prepare_train_data(self):
        total_len = len(self.sensor_data_total)
        
        # Automated mode uses the same split as manual mode:
        # first 40% for testing, last 60% for training.
        split_limit = round(total_len * 0.4)
        
        self.train_data = self.sensor_data_total[split_limit:]
        print(f"Data prepared: Total={total_len}, Test Boundary={split_limit}, Training Size={len(self.train_data)}")
        
    # Load data automatically
    def load_data(self, target_size=None):
        print("Automated loading...")
        return super().load_data(target_size=target_size)
    
    def find_optimal_params(self, range_k, range_c):
        """
        Iterates through the grid and returns the configuration with the 
        minimum number of measurements that still satisfies the similarity threshold.
        Returns: [Min Measurements, Optimal E, Optimal S]
        """
        # Request calculation results from the base class
        x, y, z = self.cal_dsra_grid(range_k, range_c)
        
        if not z:
            print("Automation failed. No valid parameters found.")
            return []

        # Find the global minimum of measurements
        min_meas = min(z)
        # Identify the index of the first occurrence of the minimum value
        best_idx = z.index(min_meas)
        
        # Return the optimal triplet
        optimal_set = [z[best_idx], x[best_idx], y[best_idx]]
        
        print(f"Optimal parameters found: E={optimal_set[1]}, S={optimal_set[2]} "
              f"with {optimal_set[0]} measurements.")
              
        return optimal_set

    def get_tbm_reconstruction(self, E, S, data=None): # map to reconstruction
        """
        Reconstructs the signal using a Threshold-Based Monitoring (TBM) approach.
        Calculates a dynamic TBM based on the slope between consecutive points.
        """
        if data is None:
            data = self.train_data
            
        current_TBM = 42 # Initial value
        prev_TBM = 1
        reconstructed = []
        
        for i in range(len(data)):
            if i == 0:
                current_TBM = 1
                prev_TBM = current_TBM
            else:
                slope = abs(data[i] - data[i - 1])
                current_TBM = max(1, int(round(E - S * (slope / (prev_TBM + 0.1)))))

                prev_TBM = current_TBM
                current_TBM = round(current_TBM)
                
                # Determine how many values to interpolate
                nb_values = int(current_TBM // 1)
                diff = data[i] - data[i - 1]

                if diff == 0:
                    # Constant signal (fill with the same value)
                    for _ in range(1, nb_values):
                        reconstructed.append(data[i])
                else:
                    # Change signal (linear interpolation between points)
                    step = diff / nb_values
                    for k in range(1, nb_values):
                        reconstructed.append(data[i - 1] + k * step)
            
            # Add actual data point
            reconstructed.append(data[i])

        return np.array(reconstructed)
    
    def my_resize(self, reconstruct, original_size):
        """
        Adjusts the length of the reconstructed signal to match the original data size.
        """
        # Ensure reconstruct is a list for easy padding
        reconstruct_lst = list(reconstruct)
        diff = len(reconstruct_lst) - original_size
        # If the reconstruction is shorter than orginal, pad with the last value
        if diff <= 0 and diff > -500 :
            for _ in range (-diff) :
                reconstruct_lst.append(reconstruct_lst[-1])
            return np.array(reconstruct_lst)
        
        # If the difference is too big
        elif diff >= 500 or diff < -500:
            print("Resize will not be precise, try to change the error threshold.")
            return np.array(reconstruct_lst)
        return np.resize(reconstruct, original_size)
    
    def run_iterative_grid_search(self, rangeK_init=(0, 30, 2), rangeC_init=(0, 450, 5), max_iterations=10):
        """
        Runs the automated notebook coarse-to-fine grid search and returns the final dual
        annealing seed bounds: [measurements, E, S].
        """
        rangeK = rangeK_init
        rangeC = rangeC_init
        iteration = 0
        search_history = []
        best_values = None

        print("Starting coarse-to-fine grid search...")

        while iteration < max_iterations:
            kx, ky, kz = rangeK
            cx, cy, cz_step = rangeC

            optimal_values = self.find_optimal_params(range(kx, ky, kz), range(cx, cy, cz_step))

            if not optimal_values:
                print("Coarse-to-fine grid search failed to find valid parameters. Breaking loop.")
                break

            best_values = optimal_values
            best_k = int(optimal_values[1])
            best_c = int(optimal_values[2])
            search_history.append([iteration, optimal_values[0], best_k, best_c])

            print(f"\n--- Iteration {iteration} ---")
            print(f"Search Range E: [{kx}, {ky}] Step: {kz}")
            print(f"Search Range S: [{cx}, {cy}] Step: {cz_step}")

            rangeK = (max(0, best_k - 4), best_k + 4, 1)
            rangeC = (max(0, best_c - 4), best_c + 4, 1)

            if kz == 1 and cz_step == 1:
                break

            iteration += 1

        if best_values is None:
            return search_history, []

        seeds = [best_values[0], int(best_values[1]), int(best_values[2])]
        print(f"\nCoarse-to-fine grid search finished. Seeds found: E={seeds[1]}, S={seeds[2]}")
        return search_history, seeds
    
    def optimize_and_reconstruct(self, seed_values):
        """
        seed_values: [measurements, E, S]
        """
        if not seed_values:
            raise ValueError("No seed values available. Run coarse-to-fine E/S search first.")

        bounds = [(max(0, seed_values[1] - 2), seed_values[1] + 2), 
                  (max(0, seed_values[2] - 2), seed_values[2] + 2)]
        
        arg_package = (self.train_data, self.interpolation_method, 
                       self.similarity_method, self.similarity_threshold)

        # Optimization using dual annealing
        resdual = dual_annealing(
            self.measure,
            bounds,
            args=arg_package,
            maxiter=1000,
            initial_temp=5230.0,
            restart_temp_ratio=2e-5,
            visit=2.62,
            accept=-5.0,
        )
        E_opt, S_opt = resdual.x

        sim, recon, meas, idx, red, num_samples = self.reconstruct_signal(
            E_opt, S_opt, data=self.sensor_data_total
        )
        
        inter_data = [recon[day] for day in idx]
        reconstructed_full = self.my_resize(
            self.get_tbm_reconstruction(E_opt, S_opt, data=inter_data),
            len(self.sensor_data_total),
        )
        
        return E_opt, S_opt, red, sim, reconstructed_full

  
