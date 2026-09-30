# DSRA-PMLO-Adaptive-Sampling

**Adaptive Sampling for Efficient IoT Data Collection**

DSRA-PMLO helps reduce sensor data transmission by selecting fewer sampling points while keeping the reconstructed signal within a user-defined error threshold.
The goal is to use recorded data for adaptive sampling without violating the
predefined approximation constraint.

![DSRA-PMLO workflow](./docs/assets/dsra_pmlo_workflow_v3.png)

DSRA-PMLO Software package input/output: The main input is the selected data file and target column. The main outputs are the optimized E and S values, the test-set error, the sampling reduction, and the reconstruction plot.

## Citation
If you use this software in academic research, publications, reports, theses,
or derived software, please cite both of the following:

### 1. Software repository

Algabroun, H., & Wu, S. (2026). *DSRA-PMLO-Adaptive-Sampling*
(Version 1.0.1) [Computer software]. GitHub.
https://github.com/Hatemgab/DSRA-PMLO-Adaptive-Sampling

### 2. Theoretical background

Algabroun, H., & Håkansson, L. (2025).
Parametric machine learning-based adaptive sampling algorithm for efficient
IoT data collection in environmental monitoring.
*Journal of Network and Systems Management, 33*, Article 5.
https://doi.org/10.1007/s10922-024-09881-1

The software citation credits the implementation and repository contributors.
The journal article citation credits the theoretical formulation and scientific
method underlying the implementation.


### BibTeX

Software repository:

```bibtex
@software{algabroun_wu_dsra_pmlo_2026,
  author    = {Algabroun, Hatem and Wu, Sisi},
  title     = {{DSRA-PMLO-Adaptive-Sampling}},
  version   = {1.0.1},
  year      = {2026},
  publisher = {GitHub},
  url       = {https://github.com/Hatemgab/DSRA-PMLO-Adaptive-Sampling}
}

@article{algabroun_hakansson_dsra_pmlo_2025,
  author  = {Algabroun, Hatem and Håkansson, Lars},
  title   = {Parametric Machine Learning-Based Adaptive Sampling Algorithm
             for Efficient IoT Data Collection in Environmental Monitoring},
  journal = {Journal of Network and Systems Management},
  volume  = {33},
  number  = {1},
  pages   = {5},
  year    = {2025},
  doi     = {10.1007/s10922-024-09881-1}
}
```

## Video Demonstration - how it works

https://github.com/user-attachments/assets/a74d40a2-fe6e-4e91-8129-8563600149d8

 *Above: Dynamic demonstration of the adaptive sampling process.*

## Project Overview

In IoT and wireless sensor networks, data transmission is often one of the most energy-consuming operations. This project searches for two adaptive sampling parameters:

- **E**: the base sampling interval.
- **S**: the sensitivity to signal change.

The algorithm reconstructs the original signal from selected sampling points and reports the reconstruction error and sampling reduction.

## Current Python Project Structure

```text
DSRA-PMLO/
├── pyproject.toml
├── README.md
├── LICENSE.txt
├── src/
│   └── dsra_pmlo/
│       ├── __init__.py
│       ├── base.py
│       ├── manual.py
│       ├── automated.py
│       ├── use_case.py
│       └── data/
│           ├── motor_light_load_brb.txt
│           ├── motor_no_load_brb.txt
│           ├── motor_no_load.txt
│           ├── downsampled_data_20000.txt
│           └── synthetic_data.txt
└── tests/
    └── test.py
```

The main file users should edit and run is:

```text
src/dsra_pmlo/use_case.py
```

Do not run `automated.py`, `manual.py`, or `base.py` directly. They are package modules.

## Video Demonstration - user guide 

[![DSRA-PMLO video demonstration](https://img.youtube.com/vi/q6RAmPTH7zw/hqdefault.jpg)](https://youtu.be/q6RAmPTH7zw)

*Click the video preview to watch how to use the Manual and Automated modes.*

## Environment Setup

### Option 1: Local Setup

First, clone the repository and install the package:

```bash
git clone https://github.com/Hatemgab/DSRA-PMLO-Adaptive-Sampling.git
cd DSRA-PMLO-Adaptive-Sampling

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
py -m venv .venv
.venv\Scripts\activate

# Install the package
python -m pip install --upgrade pip
python -m pip install -e .
```

Run the project:

```bash
# macOS / Linux
python3 -m dsra_pmlo.use_case

# Windows
py -m dsra_pmlo.use_case
```

### Option 2: Google Colab

For an interactive demonstration with inline figures, open the Google Colab notebook below.

The notebook demonstrates:

- Automated Mode
- Manual Mode
- Parameter optimization
- Signal reconstruction and visualization

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1c2oSEfkln90XC6kJBJe8xVhPjo1kopzJ?usp=sharing)

## Data Setup

Place your `.txt` or `.csv` data files in:

```text
src/dsra_pmlo/data/
```

The first row must contain column names. Example:

```text
Time    Amplitude
0.0     -0.0200
0.00005  6.7498
```

The current synthetic evaluation uses
`src/dsra_pmlo/data/downsampled_data_20000.txt`, a 20,000-sample downsample of
the 60,000-sample synthetic record. It has `Time` values in seconds and an
`Amplitude` column. The timestamps span approximately 1 s at a nominal
sampling rate of 20 kHz. Keep the `Time` column when preparing or replacing
this file so the reconstruction plot uses seconds on its horizontal axis.

In `src/dsra_pmlo/use_case.py`, update:

```python
config = {
    "file": "src/dsra_pmlo/data/downsampled_data_20000.txt",
    "mode": "automated",
    "target_col": "Amplitude",
    "target_size": 20000,
    "threshold": 3,
    "manual_step1_e": (0, 30, 2),
    "manual_step1_s": (-20, 450, 5),
}
```

- `file`: path to your dataset.
- `mode`: choose `"automated"` or `"manual"`.
- `target_col`: the column to reconstruct.
- `target_size`: number of data values to load. This file already has 20,000 rows, so `20000` leaves it unchanged; `None` also loads all rows.
- `threshold`: maximum accepted MAAPE error percentage.
- `manual_step1_e`: the first broad E range used in manual mode.
- `manual_step1_s`: the first broad S range used in manual mode.

## Which Mode Should I Use?

| Feature | Manual Mode | Automated Mode |
| :--- | :--- | :--- |
| User effort | User chooses the E and S zoom area | Program searches automatically |
| Visualization | Three zoom-in grid search plots | Final reconstruction/evaluation plot |
| Best for | Inspection and controlled tuning | Set and run optimization |

## Choosing the settings

### Training and test split

The standard `use_case.py` workflow uses a fixed 60/40 split: the first 40% of
the loaded signal is reserved for testing, and the remaining 60% is used to
fit the sampling parameters. This split is set in the code and is not a
setting in `use_case.py`. Keeping 60% for training gives the optimizer enough
data to fit both parameters, while the held-out test segment remains long
enough to evaluate reconstruction over multiple signal cycles. For the
20,000-sample synthetic record, this gives 12,000 training samples (0.6 s)
and 8,000 test samples (0.4 s). The test segment contains four cycles of the
10 Hz lowest-frequency component and ten samples per cycle at 2,000 Hz.

### Dual annealing

The standard workflow fixes the dual-annealing random seed at **1** in the
code, so the stochastic optimization can be reproduced without adding a seed
setting to the user configuration. When calling the optimization methods
directly, `random_seed` can be supplied for explicit multi-seed experiments.
Other dual-annealing options are documented in the
[SciPy `dual_annealing` reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.dual_annealing.html).

## Automated Mode

Use automated mode when you want the program to find E and S with minimal user input.

In `use_case.py`:

```python
config["mode"] = "automated"
```

Then run:

```bash
python3 -m dsra_pmlo.use_case
```

Automated mode performs a **Coarse-to-Fine Grid Search**, then refines the result with dual annealing optimization. It prints the selected E and S values and plots the test-set reconstruction.

## Manual Mode

Use manual mode when you want the user to inspect the E and S search area and choose where to zoom in.

In `use_case.py`:

```python
config["mode"] = "manual"
```

Then run:

```bash
# macOS / Linux
python3 -m dsra_pmlo.use_case

# Windows
py -m dsra_pmlo.use_case
```

Manual mode guides the user through three grid-search plots before dual annealing optimization:

1. **Coarse Grid Search**  
   The program plots the first broad E and S search area. The user defines this first range in `config`:

   ```python
   "manual_step1_e": (0, 30, 2),
   "manual_step1_s": (-20, 450, 5),
   ```

2. **Zoomed Grid Search**  
   The program suggests a second E and S range based on Step 1. The user can press Enter to accept or type a custom range:

   ```text
   start,stop,step
   ```

   Example:

   ```text
   E range as start,stop,step [suggested (1, 9, 1)]: 2,6,1
   S range as start,stop,step [suggested (0, 8, 1)]: 0,10,1
   ```

3. **Fine Grid Search**  
   The program suggests a third, smaller E and S range based on Step 2. The user again accepts the suggestion or enters their own range. This Step 3 range is then used for dual annealing optimization.

After Step 3, the selected E and S area is passed to dual annealing optimization, then the result is evaluated on the test set.

If the user presses Enter or enters invalid input, the program uses a safe suggested range instead of crashing.

## Result Graph

The final graph shows:

- **Original Signal** in orange.
- **DSRA Reconstruction** in blue dashed lines.
- **Sampling Points** at the selected signal locations.
- x-axis: `Time (s)`
- y-axis: `Data value`


### Manual Mode Optimization Example

| Step 1: Coarse Grid Search | Step 2: Zoomed Grid Search | Step 3: Fine Grid Search |
| :---: | :---: | :---: |
| ![Manual coarse grid search](./docs/assets/manual_coarse_grid_search.png) | ![Manual zoomed grid search](./docs/assets/manual_zoomed_grid_search.png) | ![Manual fine grid search](./docs/assets/manual_fine_grid_search.png) |

> *The three grid-search plots guide the user from a broad E and S search area to a smaller range for dual annealing optimization.*


## Using The Package In Your Own Python Code

```python
from dsra_pmlo.automated import DSRAAutomated

model = DSRAAutomated(
    filepath="src/dsra_pmlo/data/downsampled_data_20000.txt",
    target_col="Amplitude",
    similarity_threshold=3,
)

model.load_data(target_size=20000)
_, seeds = model.run_iterative_grid_search()
E, S, reduction, error, reconstructed = model.optimize_and_reconstruct(seeds)
model.evaluate_test_set(E=E, S=S)
```

Manual mode:

```python
from dsra_pmlo.manual import DSRAManual

model = DSRAManual(
    filepath="src/dsra_pmlo/data/downsampled_data_20000.txt",
    target_col="Amplitude",
    similarity_threshold=3,
)

model.load_data(target_size=20000)
model.plot2d(range(0, 30, 2), range(-20, 450, 5))
```

## Troubleshooting

### ImportError: attempted relative import

This happens if you run a module file directly, for example:

```bash
python3 src/dsra_pmlo/automated.py
```

Instead, run the package entry point:

```bash
# macOS / Linux
python3 -m dsra_pmlo.use_case

# Windows
py -m dsra_pmlo.use_case
```

Or install first:

```bash
# macOS / Linux
python3 -m pip install -e .

# Windows
py -m pip install -e .
```

### Python cannot find `dsra_pmlo`

Make sure you installed from the repository root:

```bash
# macOS / Linux
python3 -m pip install -e .

# Windows
py -m pip install -e .
```

The repository root is the folder containing `pyproject.toml`.

## Questions & Feedback

Please open a GitHub Issue so questions, fixes, and examples stay visible for future users. Or feel free to contact owner [Hatem Algabroun]: hatem.algabroun@lnu.se, contributor [Sisi Wu]: cathywu544@gmail.com
