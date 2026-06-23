# Main entiry point for running DSRA PMLO models
from dsra_pmlo.manual import DSRAManual
from dsra_pmlo.automated import DSRAAutomated
from scipy.optimize import dual_annealing

# Only change paramaters from config
config = {
    "file": "src/dsra_pmlo/data/synthetic_data_50Hz.txt",
    "mode": "automated", # change 'automated' to 'manual' for setting search ranges manually
    "target_col": "Amplitude",
    "target_size": 400,
    "threshold": 2,
    # Manual mode Step 1 ranges. Edit these for the first broad search.
    "manual_step1_e": (0, 30, 2),
    "manual_step1_s": (0, 450, 5),
}


def parse_range(user_text, fallback):
    """
    Parse a range entered as start,stop,step. Empty or invalid input uses fallback.
    """
    if not user_text.strip():
        return fallback

    try:
        start, stop, step = [int(value.strip()) for value in user_text.split(",")]
        if step <= 0 or stop <= start:
            raise ValueError
        return (start, stop, step)
    except ValueError:
        print(f"Invalid range. Using suggested range: {fallback}")
        return fallback


def prompt_range(label, fallback):
    raw = input(f"{label} range as start,stop,step [suggested {fallback}]: ")
    return parse_range(raw, fallback)


def suggest_zoom_ranges(plot_result, fallback_e, fallback_s, padding=4):
    if not plot_result:
        return fallback_e, fallback_s

    samples, e_values, s_values = plot_result
    best_index = samples.index(min(samples))
    best_e = int(e_values[best_index])
    best_s = int(s_values[best_index])

    suggested_e = (max(0, best_e - padding), best_e + padding, 1)
    suggested_s = (max(0, best_s - padding), best_s + padding, 1)
    return suggested_e, suggested_s

# Main flow
def main():
    # --- AUTOMATED MODE ---
    if config["mode"] == "automated":
        model = DSRAAutomated(
            filepath=config["file"],
            similarity_threshold=config["threshold"],
            target_col=config["target_col"],
        )
        model.load_data(target_size=config["target_size"])
        
        # Execute coarse-to-fine grid search
        _, seeds = model.run_iterative_grid_search()
        E_opt, S_opt, _, _, _ = model.optimize_and_reconstruct(seeds)
        
        # Evaluate test result
        model.evaluate_test_set(E=E_opt, S=S_opt)
        
    # --- MANUAL MODE ---
    elif config["mode"] == "manual":
        model = DSRAManual(
            filepath=config["file"],
            similarity_threshold=config["threshold"],
            target_col=config["target_col"],
        )
        model.load_data(target_size=config["target_size"])
        model.get_data_summary()

        print("\n--- Step 1: Coarse Grid Search ---")
        broad_e = config["manual_step1_e"]
        broad_s = config["manual_step1_s"]
        broad_result = model.plot2d(range(*broad_e), range(*broad_s))

        step2_e, step2_s = suggest_zoom_ranges(
            broad_result,
            fallback_e=(1, 5, 1),
            fallback_s=(0, 10, 1),
        )

        print("\nLook at the Step 1 plot and choose the area to zoom into for Step 2.")
        print("Press Enter to use the suggested range, or type your own.")
        step2_e = prompt_range("Step 2 E", step2_e)
        step2_s = prompt_range("Step 2 S", step2_s)

        print("\n--- Step 2: Zoomed Grid Search ---")
        step2_result = model.plot2d(range(*step2_e), range(*step2_s))
        step3_e, step3_s = suggest_zoom_ranges(
            step2_result,
            fallback_e=step2_e,
            fallback_s=step2_s,
            padding=2,
        )

        print("\nLook at the Step 2 plot and choose the area to zoom into for Step 3.")
        print("Press Enter to use the suggested range, or type your own.")
        step3_e = prompt_range("Step 3 E", step3_e)
        step3_s = prompt_range("Step 3 S", step3_s)

        print("\n--- Step 3: Fine Grid Search ---")
        model.plot2d(range(*step3_e), range(*step3_s))

        arg_package = (model.train_data, model.interpolation_method, 
                       model.similarity_method, model.similarity_threshold)
        
        manual_bounds = [(step3_e[0], step3_e[1]), (step3_s[0], step3_s[1])]
        
        print(f"Starting Dual Annealing Optimization with E/S bounds: {manual_bounds}")
        resdual = dual_annealing(model.measure, manual_bounds, args=arg_package, maxiter=10000)
        E_optimized, S_optimized = resdual.x

        # Plot and evaluate test result
        model.evaluate_test_set(E=E_optimized, S=S_optimized)
if __name__ == "__main__":
    main()
