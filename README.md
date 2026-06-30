# DSRA-PMLO: Parametric Adaptive Sampling for Efficient IoT Data Collection

**A parametric adaptive sampling algorithm for efficient IoT data collection.**

DSRA-PMLO helps reduce sensor data transmission by selecting fewer sampling points while keeping the reconstructed signal within a user-defined error threshold.
The goal is to use recorded data for adaptive sampling without violating the
predefined approximation constraint.

![DSRA-PMLO workflow](./docs/assets/dsra_pmlo_workflow.png)

DSRA-PMLO Software package input/output: The main input is the selected data file and target column. The main outputs are the optimized E and S values, the test-set error, the sampling reduction, and the reconstruction plot.

## Copyrights And Citation
This project is based on the adaptive sampling method described in this reference:

- Algabroun, H., & Håkansson, L. (2025). Parametric Machine Learning-Based Adaptive Sampling Algorithm for Efficient IoT Data Collection in Environmental Monitoring. *Journal of Network and Systems Management, 33*(1). https://doi.org/10.1007/s10922-024-09881-1

Related background paper:

- *Dynamic sampling rate algorithm (DSRA) implemented in self-adaptive software architecture: a way to reduce the energy consumption of wireless sensors through event-based sampling*


If you use this algorithm for research, cite those two papers. The code is released under the MIT
license, but citation is still requested for academic use.

## Result Demonstration

https://github.com/user-attachments/assets/a74d40a2-fe6e-4e91-8129-8563600149d8

> *Above: Dynamic demonstration of the adaptive sampling process.*

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
│           ├── motor_light_load.txt
│           ├── motor_no_load_brb.txt
│           ├── motor_no_load.txt
│           └── synthetic_data.txt
└── tests/
    └── test.py
```

The main file users should edit and run is:

```text
src/dsra_pmlo/use_case.py
```

Do not run `automated.py`, `manual.py`, or `base.py` directly. They are package modules.

## Video Demonstration

[![Video Demo](https://img.shields.io/badge/Video-Demo-red)](https://youtu.be/q6RAmPTH7zw?si=GKjFMcR7Is5H-a_S)

> *Click the badge above to watch a short video on how to use the Manual and Automated modes.*

## Environment Setup

### Option 1: Local Setup

First, clone the repository and install the package:

```bash
git clone https://github.com/Hatemgab/DSRA-PMLO-Adaptive-Sampling.git
cd DSRA-PMLO-Adaptive-Sampling

python3 -m venv .venv  # windows: py -m venv .venv
source .venv/bin/activate  # windows: .venv\Scripts\activate.bat

python -m pip install --upgrade pip
python -m pip install -e .
```

Run the project:

```bash
python -m dsra_pmlo.use_case
```

You can also use the installed command:

```bash
dsra-use-case
```

### Option 2: Google Colab Setup

In Colab, install the project as a Python package before importing it.

```python
!git clone https://github.com/Hatemgab/DSRA-PMLO-Adaptive-Sampling.git
cd DSRA-PMLO-Adaptive-Sampling
python -m pip install -e .
%cd src
```

Then import the package:

```python
from dsra_pmlo.manual import DSRAManual
from dsra_pmlo.automated import DSRAAutomated
```

Or run the configured use case:

```python
!python -m dsra_pmlo.use_case
```

The output text and final chart appear directly below the Colab cell that runs
the use case. The chart is not saved to a file unless you add save code yourself.

In Google Colab, use a full data path in `use_case.py` to avoid file path errors:

```python
config["file"] = "/content/DSRA-PMLO/src/dsra_pmlo/data/synthetic_data.txt"
```

If you upload the project folder manually to Colab instead of cloning from GitHub, make sure the current working directory is the repository root, the folder that contains `pyproject.toml`, before running:

```python
!python -m pip install -e .
```

After installation, move into `src` before running the use case:

```python
%cd src
```

## Data Setup

Place your `.txt` or `.csv` data files in:

```text
src/dsra_pmlo/data/
```

The first row must contain column names. Example:

```text
Time    Amplitude
0.0     -0.0200
0.1      2.3366
```

In `src/dsra_pmlo/use_case.py`, update:

```python
config = {
    "file": "src/dsra_pmlo/data/synthetic_data.txt",
    "mode": "automated",
    "target_col": "Amplitude",
    "target_size": 400,
    "threshold": 2,
    "manual_step1_e": (0, 30, 2),
    "manual_step1_s": (-20, 450, 5),
}
```

- `file`: path to your dataset.
- `mode`: choose `"automated"` or `"manual"`.
- `target_col`: the column to reconstruct.
- `target_size`: resize the dataset for testing; set to `None` to use the full file.
- `threshold`: maximum accepted MAAPE error percentage.
- `manual_step1_e`: the first broad E range used in manual mode.
- `manual_step1_s`: the first broad S range used in manual mode.

## Which Mode Should I Use?

| Feature | Manual Mode | Automated Mode |
| :--- | :--- | :--- |
| User effort | User chooses the E and S zoom area | Program searches automatically |
| Visualization | Three zoom-in grid search plots | Final reconstruction/evaluation plot |
| Best for | Inspection and controlled tuning | Set and run optimization |

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
python3 -m dsra_pmlo.use_case
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
- **Sampling Points** along the bottom baseline.
- x-axis: `Time(S)`
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
    filepath="src/dsra_pmlo/data/synthetic_data.txt",
    target_col="Amplitude",
    similarity_threshold=2,
)

model.load_data(target_size=400)
_, seeds = model.run_iterative_grid_search()
E, S, reduction, error, reconstructed = model.optimize_and_reconstruct(seeds)
model.evaluate_test_set(E=E, S=S)
```

Manual mode:

```python
from dsra_pmlo.manual import DSRAManual

model = DSRAManual(
    filepath="src/dsra_pmlo/data/synthetic_data.txt",
    target_col="Amplitude",
    similarity_threshold=2,
)

model.load_data(target_size=400)
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
python3 -m dsra_pmlo.use_case
```

Or install first:

```bash
python3 -m pip install -e .
```

### Python cannot find `dsra_pmlo`

Make sure you installed from the repository root:

```bash
python3 -m pip install -e .
```

The repository root is the folder containing `pyproject.toml`.

## Questions & Feedback

Please open a GitHub Issue so questions, fixes, and examples stay visible for future users. Or feel free to contact owner [Hatem Algabroun]: Hatem.algabroun@lnu.com, contributor [Sisi Wu]: cathywu544@gmail.com
