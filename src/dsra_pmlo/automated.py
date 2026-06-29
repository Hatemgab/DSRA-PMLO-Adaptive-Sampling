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
        """
        Split the loaded signal for automated mode.

        The first 40% is kept for testing. The last 60% is used for training.
        """
        total_len = len(self.sensor_data_total)
        
        # First 40% is reserved for testing; the remaining 60% is used for training.
        split_limit = round(total_len * 0.4)
        
        self.train_data = self.sensor_data_total[split_limit:] # len(data) is the total length of training data
        self._validate_data_ready(self.train_data, "Training data")
        print(f"Data prepared: Total={total_len}, Test Boundary={split_limit}, Training Size={len(self.train_data)}")
        
    # Load data automatically
    def load_data(self, target_size=None):
        """
        Load data for automated mode.

        target_size can resize the signal before the train/test split.
        """
        print("Automated loading...")
        return super().load_data(target_size=target_size)
    
    def find_optimal_params(self, range_e, range_s):
        """
        Find the best E and S pair inside one grid search.

        The best pair uses the fewest samples while still meeting the error
        threshold. Returns [number of samples, E, S].
        """
        # Request calculation results from the base class
        x, y, z = self.cal_dsra_grid(range_e, range_s)
        
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

    def run_iterative_grid_search(
        self,
        range_e_init=(0, 30, 2),
        range_s_init=(-20, 450, 5),
        max_iterations=10,
    ):
        """
        Run coarse-to-fine E and S grid search.

        The search starts with broad ranges, then zooms in around the best pair.
        Returns the search history and final seed values [samples, E, S].
        """
        range_e = self._validate_grid_range(range_e_init, "E")
        range_s = self._validate_grid_range(range_s_init, "S")
        if max_iterations <= 0:
            raise ValueError("max_iterations must be greater than 0.")

        iteration = 0
        search_history = []
        best_values = None

        print("Starting coarse-to-fine grid search...")

        while iteration < max_iterations:
            e_start, e_stop, e_step = range_e
            s_start, s_stop, s_step = range_s

            optimal_values = self.find_optimal_params(
                range(e_start, e_stop, e_step),
                range(s_start, s_stop, s_step),
            )

            if not optimal_values:
                print("Coarse-to-fine grid search failed to find valid parameters. Breaking loop.")
                break

            best_values = optimal_values
            best_e = int(optimal_values[1])
            best_s = int(optimal_values[2])
            display_iteration = iteration + 1
            search_history.append([display_iteration, optimal_values[0], best_e, best_s])

            print(f"\n--- Iteration {display_iteration} ---")
            print(f"Search Range E: [{e_start}, {e_stop}] Step: {e_step}")
            print(f"Search Range S: [{s_start}, {s_stop}] Step: {s_step}")

            range_e = (max(0, best_e - 4), best_e + 4, 1)
            range_s = (best_s - 4, best_s + 4, 1)

            if e_step == 1 and s_step == 1:
                break

            iteration += 1

        if best_values is None:
            return search_history, []

        seeds = [best_values[0], int(best_values[1]), int(best_values[2])]
        print(f"\nCoarse-to-fine grid search finished. Seeds found: E={seeds[1]}, S={seeds[2]}")
        print("Starting final optimization around the selected E and S seed...")
        return search_history, seeds
    
    def optimize_and_reconstruct(self, seed_values=None, bounds=None):
        """
        Optimize E and S after the grid search.

        If seed_values are provided, bounds are centered around the selected
        E and S seed. If bounds are provided, those bounds are used directly.
        """
        if bounds is None:
            if seed_values is not None:
                if not seed_values:
                    raise ValueError("No seed values available. Run coarse-to-fine E and S search with a wider range or looser threshold.")

                if len(seed_values) != 3:
                    raise ValueError("seed_values must be [measurements, E, S].")

                bounds = [
                    (max(0, seed_values[1] - 2), seed_values[1] + 2),
                    (seed_values[2] - 2, seed_values[2] + 2),
                ]
            else:
                bounds = [(1, 8), (-1, 15)]

        bounds = self._validate_bounds(bounds)
        
        arg_package = (self.train_data, self.interpolation_method, 
                       self.similarity_method, self.similarity_threshold)

        resdual = dual_annealing(
            self.measure,
            bounds,
            args=arg_package,
            maxiter=10000,
        )
        E_opt, S_opt = resdual.x

        sim, recon, meas, idx, red, num_samples = self.reconstruct_signal(
            E_opt, S_opt, data=self.train_data
        )
        
        return E_opt, S_opt, red, sim, recon

    def _validate_grid_range(self, range_values, label):
        if not isinstance(range_values, (list, tuple)):
            raise ValueError(f"{label} search range must be (start, stop, step).")

        if len(range_values) != 3:
            raise ValueError(f"{label} search range must be (start, stop, step).")

        start, stop, step = range_values
        if not all(isinstance(value, int) for value in (start, stop, step)):
            raise ValueError(f"{label} search range values must be integers.")

        if step <= 0:
            raise ValueError(f"{label} search range step must be greater than 0.")

        if stop <= start:
            raise ValueError(f"{label} search range stop must be greater than start.")

        return range_values

  
