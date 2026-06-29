from pathlib import Path
import contextlib
import io
import os
import sys
import tempfile

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/mplconfig")

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from dsra_pmlo.automated import DSRAAutomated
from dsra_pmlo.manual import DSRAManual
from dsra_pmlo.use_case import config, main


DATA_FILE = ROOT_DIR / "src" / "dsra_pmlo" / "data" / "motor_no_load.txt"


def write_temp_file(directory, name, content):
    path = Path(directory) / name
    path.write_text(content, encoding="utf-8")
    return path


def expect_exception(name, expected_exception, expected_text, action):
    try:
        action()
    except expected_exception as exc:
        message = str(exc)
        if expected_text and expected_text not in message:
            print(f"FAIL | {name} | wrong message: {message}")
            return False
        print(f"PASS | {name} | {type(exc).__name__}: {message}")
        return True
    except Exception as exc:
        print(f"FAIL | {name} | wrong exception {type(exc).__name__}: {exc}")
        return False

    print(f"FAIL | {name} | expected {expected_exception.__name__}, but no exception was raised")
    return False


def expect_success(name, action):
    try:
        result = action()
    except Exception as exc:
        print(f"FAIL | {name} | unexpected {type(exc).__name__}: {exc}")
        return False

    print(f"PASS | {name} | {result}")
    return True


def run_tests():
    tests = []

    with tempfile.TemporaryDirectory() as tmpdir:
        empty_file = write_temp_file(tmpdir, "empty.txt", "")
        missing_col_file = write_temp_file(tmpdir, "missing_col.txt", "Other\n1\n2\n3\n4\n")
        non_numeric_file = write_temp_file(tmpdir, "non_numeric.txt", "Amplitude\n1\nbad\n3\n4\n")
        nan_file = write_temp_file(tmpdir, "nan.txt", "Amplitude\n1\nNaN\n3\n4\n")
        short_file = write_temp_file(tmpdir, "short.txt", "Amplitude\n1\n2\n3\n")

        tests.extend(
            [
                (
                    "missing data file",
                    lambda: expect_exception(
                        "missing data file",
                        FileNotFoundError,
                        "Data file not found",
                        lambda: DSRAAutomated(filepath=str(Path(tmpdir) / "missing.txt")).load_data(target_size=400),
                    ),
                ),
                (
                    "empty data file",
                    lambda: expect_exception(
                        "empty data file",
                        ValueError,
                        "empty",
                        lambda: DSRAAutomated(filepath=str(empty_file)).load_data(target_size=400),
                    ),
                ),
                (
                    "missing target column",
                    lambda: expect_exception(
                        "missing target column",
                        ValueError,
                        "Target column",
                        lambda: DSRAAutomated(filepath=str(missing_col_file)).load_data(target_size=400),
                    ),
                ),
                (
                    "non numeric target column",
                    lambda: expect_exception(
                        "non numeric target column",
                        ValueError,
                        "numeric",
                        lambda: DSRAAutomated(filepath=str(non_numeric_file)).load_data(target_size=400),
                    ),
                ),
                (
                    "nan target column",
                    lambda: expect_exception(
                        "nan target column",
                        ValueError,
                        "NaN or infinite",
                        lambda: DSRAAutomated(filepath=str(nan_file)).load_data(target_size=400),
                    ),
                ),
                (
                    "too-short source data",
                    lambda: expect_exception(
                        "too-short source data",
                        ValueError,
                        "at least 4 points",
                        lambda: DSRAAutomated(filepath=str(short_file)).load_data(),
                    ),
                ),
            ]
        )

        tests.extend(
            [
                (
                    "invalid target_size type",
                    lambda: expect_exception(
                        "invalid target_size type",
                        ValueError,
                        "target_size must be an integer",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE)).load_data(target_size=400.0),
                    ),
                ),
                (
                    "too-small target_size",
                    lambda: expect_exception(
                        "too-small target_size",
                        ValueError,
                        "target_size must be at least 4",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE)).load_data(target_size=3),
                    ),
                ),
                (
                    "invalid MAAPE threshold",
                    lambda: expect_exception(
                        "invalid MAAPE threshold",
                        ValueError,
                        "greater than 0",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE), similarity_threshold=-1).load_data(target_size=400),
                    ),
                ),
                (
                    "invalid interpolation method",
                    lambda: expect_exception(
                        "invalid interpolation method",
                        ValueError,
                        "interpolation_method",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE), interpolation_method="cubic").load_data(target_size=400),
                    ),
                ),
                (
                    "invalid similarity method",
                    lambda: expect_exception(
                        "invalid similarity method",
                        ValueError,
                        "similarity_method",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE), similarity_method="MSE").load_data(target_size=400),
                    ),
                ),
                (
                    "invalid target column name",
                    lambda: expect_exception(
                        "invalid target column name",
                        ValueError,
                        "target_col",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE), target_col="").load_data(target_size=400),
                    ),
                ),
                (
                    "reconstruct before load",
                    lambda: expect_exception(
                        "reconstruct before load",
                        ValueError,
                        "not loaded",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE)).reconstruct_signal(1, 1),
                    ),
                ),
                (
                    "quadratic too few points",
                    lambda: expect_exception(
                        "quadratic too few points",
                        ValueError,
                        "At least 2 measurement points",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE)).interp_quadratic([0], [1.0]),
                    ),
                ),
                (
                    "duplicate interpolation indices",
                    lambda: expect_exception(
                        "duplicate interpolation indices",
                        ValueError,
                        "strictly increasing",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE)).interp_linear([0, 0], [1.0, 2.0]),
                    ),
                ),
                (
                    "all-zero correlation",
                    lambda: expect_exception(
                        "all-zero correlation",
                        ValueError,
                        "undefined",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE)).cor([0.0, 0.0], [0.0, 0.0]),
                    ),
                ),
            ]
        )

        def loaded_auto():
            model = DSRAAutomated(filepath=str(DATA_FILE), similarity_threshold=1)
            model.load_data(target_size=400)
            return model

        tests.extend(
            [
                (
                    "normal load and reconstruct",
                    lambda: expect_success(
                        "normal load and reconstruct",
                        lambda: (
                            lambda model: (
                                lambda result: (
                                    f"total={len(model.sensor_data_total)}, train={len(model.train_data)}, "
                                    f"samples={len(result[3])}, recon={len(result[1])}"
                                )
                            )(model.reconstruct_signal(4, 2))
                        )(loaded_auto()),
                    ),
                ),
                (
                    "invalid E/S values",
                    lambda: expect_exception(
                        "invalid E/S values",
                        ValueError,
                        "finite",
                        lambda: loaded_auto().reconstruct_signal(float("nan"), 1),
                    ),
                ),
                (
                    "invalid bounds order",
                    lambda: expect_exception(
                        "invalid bounds order",
                        ValueError,
                        "lower bound",
                        lambda: DSRAManual(filepath=str(DATA_FILE))._validate_bounds([(5, 1), (-1, 1)]),
                    ),
                ),
                (
                    "malformed bounds",
                    lambda: expect_exception(
                        "malformed bounds",
                        ValueError,
                        "exactly two ranges",
                        lambda: DSRAManual(filepath=str(DATA_FILE))._validate_bounds([(1, 2)]),
                    ),
                ),
                (
                    "invalid grid range step",
                    lambda: expect_exception(
                        "invalid grid range step",
                        ValueError,
                        "step",
                        lambda: DSRAAutomated(filepath=str(DATA_FILE)).run_iterative_grid_search(range_e_init=(0, 10, 0)),
                    ),
                ),
                (
                    "empty seeds",
                    lambda: expect_exception(
                        "empty seeds",
                        ValueError,
                        "No seed values",
                        lambda: loaded_auto().optimize_and_reconstruct([]),
                    ),
                ),
                (
                    "invalid use_case mode",
                    lambda: expect_exception(
                        "invalid use_case mode",
                        ValueError,
                        "mode",
                        invalid_mode_main,
                    ),
                ),
            ]
        )

        passed = 0
        print("DSRA-PMLO guardrail tests")
        print("=" * 28)
        for _, test in tests:
            if test():
                passed += 1

        total = len(tests)
        print("=" * 28)
        print(f"Result: {passed}/{total} passed")
        return passed == total


def invalid_mode_main():
    old_mode = config.get("mode")
    config["mode"] = "invalid"
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            main()
    finally:
        config["mode"] = old_mode


if __name__ == "__main__":
    success = run_tests()
    raise SystemExit(0 if success else 1)
