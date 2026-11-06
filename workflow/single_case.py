"""Single-case engineering smoke workflow.

This module implements a mock engineering smoke workflow for a single planetary
case. It reads a JSON config, validates it strictly, optionally runs a mock
solver adapter, and persists snapshots plus a report. The mock solver produces
no real physics; it only labels origin=MOCK_SOLVER and uses an arbitrary radius.

No subprocess, model launch, or real science execution is performed here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from check_tp_model import finite_tree  # noqa: E402

SCHEMA_VERSION = 1
REQUIRED_CONFIG_KEYS = {
    "schema_version",
    "origin",
    "units",
    "mass_earth",
    "fractions",
    "outer_pressure_bar",
    "outer_temperature_K",
    "tp_profile_file",
}
REQUIRED_UNIT_KEYS = {"mass", "pressure", "temperature"}
REQUIRED_FRACTION_KEYS = {"iron", "silicate", "water", "hhe"}
REQUIRED_RESULT_KEYS = {
    "origin",
    "mass_earth",
    "radius_earth",
    "physical_acceptance",
}

# Private sentinel for "adapter returned no result" vs "adapter returned JSON null"
_NO_RESULT = object()


def _is_number(value: Any) -> bool:
    """Return True if value is a real number and not a bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _finite_positive(value: Any) -> bool:
    """Return True if value is a finite positive number and not bool."""
    return _is_number(value) and math.isfinite(value) and value > 0


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _snapshot_file(path: Path, dest_dir: Path, name: str) -> None:
    dest = dest_dir / name
    dest.write_bytes(path.read_bytes())


def _safe_json_dump(payload: Dict[str, Any], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, allow_nan=False, indent=2)


def _load_json_config(config_bytes: Optional[bytes], config_path: Path) -> Dict[str, Any]:
    """Read and parse config from captured bytes. Return dict or raise ValueError."""
    if config_bytes is None:
        try:
            config_bytes = config_path.read_bytes()
        except OSError as exc:
            raise ValueError(f"cannot read config: {exc}")
    try:
        config = json.loads(config_bytes.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed JSON config: {exc}")
    if not isinstance(config, dict):
        raise ValueError("config must be a JSON object")
    return config


def _capture_declared_tp(config: Dict[str, Any], config_path: Path, config_bytes: Optional[bytes]) -> tuple[Optional[Path], Optional[bytes], Optional[str], Optional[str]]:
    """Attempt to capture declared TP bytes BEFORE full validation.
    
    Returns:
        (tp_path, tp_bytes, tp_identity, tp_error)
    If the declared TP reference is missing/unreadable, tp_identity is a
    string describing the failure and tp_error is populated.
    """
    tp_profile_file = config.get("tp_profile_file")
    if not isinstance(tp_profile_file, str) or not tp_profile_file:
        return None, None, None, "tp_profile_file must be a non-empty string"
    try:
        tp_path = Path(tp_profile_file)
        if not tp_path.is_absolute():
            tp_path = config_path.parent / tp_path
        tp_bytes = tp_path.read_bytes()
        identity = _sha256_bytes(tp_bytes)
        return tp_path, tp_bytes, identity, None
    except (OSError, ValueError) as exc:
        return None, None, None, f"cannot read declared TP file: {exc}"


def _validate_config(
    config: Dict[str, Any],
    config_path: Path,
    checks: list[str],
    tp_bytes: Optional[bytes] = None,
) -> tuple[Path, Optional[bytes], list[str]]:
    """Validate config strictly. Append to checks and return tp_path and tp_bytes."""

    if set(config) != REQUIRED_CONFIG_KEYS:
        missing = REQUIRED_CONFIG_KEYS - set(config)
        extra = set(config) - REQUIRED_CONFIG_KEYS
        raise ValueError(
            f"config keys invalid; missing={sorted(missing)}, extra={sorted(extra)}"
        )

    if type(config["schema_version"]) is not int or config["schema_version"] != SCHEMA_VERSION:
        raise ValueError(
            f"schema_version must be integer {SCHEMA_VERSION}, got "
            f"{config['schema_version']!r}"
        )

    if config["origin"] != "SYNTHETIC_FIXTURE":
        raise ValueError("origin must be 'SYNTHETIC_FIXTURE'")

    units = config["units"]
    if not isinstance(units, dict) or set(units) != REQUIRED_UNIT_KEYS:
        raise ValueError(
            "units must be an object with exactly keys "
            f"{sorted(REQUIRED_UNIT_KEYS)}"
        )
    if units["mass"] != "M_earth":
        raise ValueError("units.mass must be 'M_earth'")
    if units["pressure"] != "bar":
        raise ValueError("units.pressure must be 'bar'")
    if units["temperature"] != "K":
        raise ValueError("units.temperature must be 'K'")
    checks.append("units valid")

    mass = config["mass_earth"]
    if not _finite_positive(mass):
        raise ValueError("mass_earth must be a finite positive non-bool number")
    checks.append("mass_earth positive finite")

    outer_p = config["outer_pressure_bar"]
    outer_t = config["outer_temperature_K"]
    if not _finite_positive(outer_p):
        raise ValueError(
            "outer_pressure_bar must be a finite positive non-bool number"
        )
    if not _finite_positive(outer_t):
        raise ValueError(
            "outer_temperature_K must be a finite positive non-bool number"
        )
    checks.append("outer boundary positive finite")

    fractions = config["fractions"]
    if not isinstance(fractions, dict) or set(fractions) != REQUIRED_FRACTION_KEYS:
        raise ValueError(
            "fractions must be an object with exactly keys "
            f"{sorted(REQUIRED_FRACTION_KEYS)}"
        )
    total = 0.0
    for key in REQUIRED_FRACTION_KEYS:
        value = fractions[key]
        if not _is_number(value) or not math.isfinite(value) or not (0.0 <= value <= 1.0):
            raise ValueError("fractions values must be finite numbers in [0,1]")
        total += value
    if abs(total - 1.0) > 1e-12:
        raise ValueError("fractions must sum to 1 within 1e-12")
    if fractions["hhe"] <= 0:
        raise ValueError("fractions.hhe must be positive")
    if fractions["iron"] <= 0 and fractions["silicate"] <= 0 and fractions["water"] <= 0:
        raise ValueError("at least one solid fraction must be positive")
    checks.append("fractions valid")

    tp_profile_file = config["tp_profile_file"]
    if not isinstance(tp_profile_file, str) or not tp_profile_file:
        raise ValueError("tp_profile_file must be a non-empty string")
    tp_path = Path(tp_profile_file)
    if not tp_path.is_absolute():
        tp_path = config_path.parent / tp_path
    if not tp_path.is_file():
        raise ValueError(f"tp_profile_file does not exist: {tp_path}")
    if tp_bytes is None:
        try:
            tp_bytes = tp_path.read_bytes()
        except OSError as exc:
            raise ValueError(f"cannot read TP profile: {exc}")
    checks.append("TP profile path found")

    try:
        finite_tree(config)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"config contains non-finite values: {exc}")

    return tp_path, tp_bytes, checks


def _validate_tp(
    tp_bytes: bytes, outer_pressure_bar: float, outer_temperature_K: float, checks: list[str]
) -> list[str]:
    """Validate TP CSV from captured bytes. Append to checks and return them."""
    if tp_bytes.startswith(b"\xef\xbb\xbf"):
        raise ValueError("TP CSV must not have BOM")
    try:
        text = tp_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"TP CSV is not valid UTF-8: {exc}")
    lines = text.splitlines()
    if not lines:
        raise ValueError("TP CSV is empty")
    header = lines[0]
    if header != "P_bar,T_K":
        raise ValueError("TP CSV header must be exactly 'P_bar,T_K'")
    checks.append("TP header valid")
    rows: list[list[str]] = []
    for idx, line in enumerate(lines[1:], start=2):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(",")
        if len(parts) != 2:
            raise ValueError(f"TP CSV row {idx} must have exactly two columns")
        rows.append(parts)
    if len(rows) < 2:
        raise ValueError("TP CSV must have at least two data rows")

    pressures: list[float] = []
    temperatures: list[float] = []
    for idx, (p_str, t_str) in enumerate(rows, start=2):
        try:
            p = float(p_str)
            t = float(t_str)
        except ValueError:
            raise ValueError(f"TP CSV row {idx} has non-numeric values")
        if not _finite_positive(p) or not _finite_positive(t):
            raise ValueError(
                f"TP CSV row {idx} must have positive finite values"
            )
        pressures.append(p)
        temperatures.append(t)

    for idx in range(1, len(pressures)):
        if pressures[idx] <= pressures[idx - 1]:
            raise ValueError("TP pressures must be strictly increasing")
    checks.append("TP rows >=2 and strictly increasing")

    if outer_pressure_bar < pressures[0] or outer_pressure_bar > pressures[-1]:
        raise ValueError(
            "outer_pressure_bar is outside TP pressure range; no extrapolation"
        )
    checks.append("outer boundary inside TP range")

    log_outer = math.log(outer_pressure_bar)
    matched = False
    for idx in range(1, len(pressures)):
        if pressures[idx - 1] <= outer_pressure_bar <= pressures[idx]:
            log_low = math.log(pressures[idx - 1])
            log_high = math.log(pressures[idx])
            frac = (log_outer - log_low) / (log_high - log_low)
            interpolated = temperatures[idx - 1] + frac * (
                temperatures[idx] - temperatures[idx - 1]
            )
            tol = 1e-12 * max(1.0, abs(outer_temperature_K))
            if abs(interpolated - outer_temperature_K) > tol:
                raise ValueError(
                    "outer_temperature_K does not match TP interpolation at "
                    "outer_pressure_bar"
                )
            matched = True
            break
    if not matched:
        raise ValueError("outer_pressure_bar interpolation failed")
    checks.append("outer T matches T-lnP interpolation")

    return checks


def check_result(result: Any, checks: Optional[list[str]] = None) -> list[str]:
    """Validate adapter result independently. Raise ValueError on invalid.

    If checks is provided, append successful checks to the shared list;
    otherwise create and return a new list. On success, return checks.
    """
    if checks is None:
        checks = []
    if not isinstance(result, dict):
        raise ValueError("solver result must be a dict")
    checks.append("result is dict with required keys")
    if set(result) != REQUIRED_RESULT_KEYS:
        missing = REQUIRED_RESULT_KEYS - set(result)
        extra = set(result) - REQUIRED_RESULT_KEYS
        raise ValueError(
            f"result keys invalid; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if result["origin"] != "MOCK_SOLVER":
        raise ValueError("result origin must be 'MOCK_SOLVER'")
    checks.append("origin MOCK_SOLVER")
    if result["physical_acceptance"] is not False:
        raise ValueError("result physical_acceptance must be exactly False")
    checks.append("physical_acceptance false")
    if not _finite_positive(result["mass_earth"]):
        raise ValueError(
            "result mass_earth must be a finite positive non-bool number"
        )
    if not _finite_positive(result["radius_earth"]):
        raise ValueError(
            "result radius_earth must be a finite positive non-bool number"
        )
    checks.append("mass_earth and radius_earth positive finite")
    try:
        finite_tree(result)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"result contains non-finite values: {exc}")
    return checks


class MockSolver:
    """Default mock adapter. No science; fixed arbitrary radius."""

    def solve(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "origin": "MOCK_SOLVER",
            "mass_earth": config["mass_earth"],
            "radius_earth": 2.0,
            "physical_acceptance": False,
        }


def _write_report(
    output_dir: Path,
    report: Dict[str, Any],
    config_bytes: Optional[bytes],
    tp_path: Optional[Path],
    tp_bytes_before: Optional[bytes],
    adapter_result: Any,
) -> None:
    """Persist snapshots and report, handling serialisation failures.
    
    If writing result.json fails, update report to FAILED while preserving
    the primary reason and append the persistence diagnostic. If writing
    report.json fails, update the original report object in place to the
    fallback BEFORE writing it, so return and persisted report agree.
    Propagate OSError if fallback itself fails.

    adapter_result is written only when it is not the private _NO_RESULT
    sentinel; JSON null, bool, list, and scalar results are preserved.
    """
    try:
        if config_bytes is not None:
            (output_dir / "config.json").write_bytes(config_bytes)
        if tp_path is not None and tp_bytes_before is not None:
            (output_dir / "tp.csv").write_bytes(tp_bytes_before)
        if adapter_result is not _NO_RESULT:
            try:
                result_json = json.dumps(adapter_result, allow_nan=False, indent=2)
                (output_dir / "result.json").write_text(result_json, encoding="utf-8")
            except (TypeError, ValueError, OSError) as exc:
                # Preserve primary reason, mark report FAILED.
                prefix = report.get("reason", "")
                report["status"] = "FAILED"
                report["reason"] = (prefix + " " if prefix else "") + f"result serialization failed: {exc}"
                report["physical_acceptance"] = False
        report_json = json.dumps(report, allow_nan=False, indent=2)
        (output_dir / "report.json").write_text(report_json, encoding="utf-8")
    except (TypeError, ValueError, OSError) as exc:
        # Build fallback, update original report in place BEFORE writing.
        try:
            fallback = {
                "status": "FAILED",
                "physical_acceptance": False,
                "reason": (report.get("reason", "") + " " if report.get("reason") else "") + f"report write failed: {exc}",
                "checks": report.get("checks", []),
                "identities": report.get("identities", {}),
            }
            # Update the original report object so returned and persisted agree.
            report.clear()
            report.update(fallback)
            (output_dir / "report.json").write_text(
                json.dumps(report, allow_nan=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            # If even fallback fails, propagate the original OSError.
            raise


def run_case(
    config_path: Path | str,
    output_dir: Path | str,
    solver: Optional[Callable[[Dict[str, Any]], Any]] = None,
) -> Dict[str, Any]:
    """Run a single-case engineering smoke workflow.

    Parameters
    ----------
    config_path: path to JSON config file.
    output_dir: directory for snapshots and report. Must not exist.
    solver: object with solve(config) -> result. Defaults to MockSolver.

    Returns report dict persisted to output_dir/report.json.
    Raises FileExistsError/ValueError only when output_dir already exists.
    """
    config_path = Path(config_path)
    output_dir = Path(output_dir)

    # Must raise if output exists; do this outside failure-report handling.
    output_dir.mkdir(exist_ok=False)

    adapter = MockSolver() if solver is None else solver
    report: Dict[str, Any] = {
        "status": "ENGINEERING_SMOKE_PASS",
        "physical_acceptance": False,
        "reason": "",
        "checks": [],
        "identities": {},
    }

    source_dir = output_dir / "source"
    current_file = Path(__file__).resolve()
    check_tp_model_path = Path(__import__("check_tp_model").__file__).resolve()

    identities: Dict[str, Any] = {}
    config_bytes: Optional[bytes] = None
    tp_path: Optional[Path] = None
    tp_bytes_before: Optional[bytes] = None
    tp_identity: Optional[str] = None
    tp_error: Optional[str] = None
    checks: list[str] = []
    adapter_result: Any = _NO_RESULT

    def _fail(reason: str, extra_checks: Optional[list[str]] = None) -> Dict[str, Any]:
        """Set failure state and return report."""
        report["status"] = "FAILED"
        report["reason"] = reason
        if extra_checks:
            for c in extra_checks:
                if c not in report["checks"]:
                    report["checks"].append(c)
        report["checks"] = checks
        report["identities"] = identities
        _write_report(output_dir, report, config_bytes, tp_path, tp_bytes_before, adapter_result)
        return report

    try:
        # Snapshot source files.
        source_dir.mkdir()
        _snapshot_file(current_file, source_dir, "single_case.py")
        _snapshot_file(check_tp_model_path, source_dir, "check_tp_model.py")

        # Initialize source/checker SHA256 identities from snapshot bytes
        # immediately after source snapshots, BEFORE config read.
        # This ensures missing/unreadable config preserves source identities.
        identities = {
            "source/single_case.py": hashlib.sha256(
                (source_dir / "single_case.py").read_bytes()
            ).hexdigest(),
            "source/check_tp_model.py": hashlib.sha256(
                (source_dir / "check_tp_model.py").read_bytes()
            ).hexdigest(),
        }

        # Read original config bytes.
        try:
            config_bytes = config_path.read_bytes()
        except OSError as exc:
            return _fail(f"cannot read config: {exc}")

        # Add config identity after config bytes available.
        identities.update({
            "config": {
                "path": str(config_path.resolve()),
                "sha256": _sha256_bytes(config_bytes),
            },
        })

        # Load config from captured bytes.
        try:
            config = _load_json_config(config_bytes, config_path)
        except ValueError as exc:
            return _fail(str(exc))

        # Attempt to capture declared TP BEFORE full validation.
        tp_path, tp_bytes_before, tp_identity, tp_error = _capture_declared_tp(
            config, config_path, config_bytes
        )
        if tp_identity is not None:
            identities["tp"] = {
                "path": str(tp_path.resolve()),
                "sha256": tp_identity,
            }
        elif tp_error is not None:
            identities["tp"] = {
                "path": str(tp_path.resolve()) if tp_path else "",
                "error": tp_error,
            }

        # Validate config and TP using captured bytes where possible.
        try:
            tp_path, tp_bytes_before, checks = _validate_config(
                config, config_path, checks, tp_bytes_before
            )
            if tp_bytes_before is None:
                raise ValueError("TP bytes unavailable for validation")
            if "tp" not in identities and tp_identity is None:
                identities["tp"] = {
                    "path": str(tp_path.resolve()),
                    "sha256": _sha256_bytes(tp_bytes_before),
                }
            checks = _validate_tp(
                tp_bytes_before,
                float(config["outer_pressure_bar"]),
                float(config["outer_temperature_K"]),
                checks,
            )
        except (ValueError, OSError) as exc:
            return _fail(str(exc))

        report["checks"] = checks

        # Deep copy validated config before adapter.
        solver_input = copy.deepcopy(config)
        try:
            adapter_result = adapter.solve(solver_input)
        except Exception as exc:
            return _fail(f"adapter error: {exc}", ["adapter invocation failed"])

        # Validate result separately; preserve partial checks on failure.
        try:
            result_checks = check_result(adapter_result, checks)
        except Exception as exc:
            return _fail(f"result validation failed: {exc}", [])

        report["checks"] = checks

        if abs(float(adapter_result["mass_earth"]) - float(config["mass_earth"])) > 1e-12:
            return _fail(
                "adapter mass_earth does not match config mass_earth",
                result_checks,
            )

        # Check original files unchanged after adapter.
        try:
            config_hash_after = _sha256_bytes(config_path.read_bytes())
            tp_hash_after = _sha256_bytes(tp_path.read_bytes())
        except OSError as exc:
            return _fail(f"cannot verify input files after adapter: {exc}", result_checks)

        if config_hash_after != identities["config"]["sha256"]:
            return _fail("adapter mutated config file", result_checks)
        if tp_hash_after != identities["tp"]["sha256"]:
            return _fail("adapter mutated TP file", result_checks)

        checks.append("adapter success and validated result")
        report["checks"] = checks
        report["identities"] = identities
        _write_report(output_dir, report, config_bytes, tp_path, tp_bytes_before, adapter_result)

    except OSError:
        # Explicit boundary: persistence OSError must propagate to caller,
        # including failure of initial AND fallback report writes.
        raise
    except (FileExistsError, ValueError):
        # output_dir.mkdir(exist_ok=False) already raises FileExistsError for existing dir.
        raise
    except Exception as exc:
        # Unexpected failure; attempt to write a failed report.
        return _fail(f"unexpected error: {exc}")

    return report


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Engineering smoke mock workflow")
    parser.add_argument("--config", required=True, help="Path to input JSON config")
    parser.add_argument("--output", required=True, help="Output directory (must not exist)")
    args = parser.parse_args(argv)

    try:
        report = run_case(args.config, args.output)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "ENGINEERING_SMOKE_PASS" else 1
    except (FileExistsError, ValueError) as exc:
        print(f"output path error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
