#!/usr/bin/env python3
"""Convert native T(P) table to external TP profile format."""

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path


def _sha256_bytes(data):
    """Compute SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def _write_bytes_atomic(path, data):
    """Write bytes to path atomically (write temp then rename)."""
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    with open(tmp_path, 'wb') as f:
        f.write(data)
    os.replace(tmp_path, path)


def _fail(report, reason):
    """Mark report as FAILED with reason."""
    report['status'] = 'FAILED'
    report['reason'] = reason
    report['physical_acceptance'] = False
    if 'point_count' in report:
        del report['point_count']
    return report


def convert_profile(source, output_dir):
    """Convert source profile to external TP format.

    Args:
        source: Path to input file.
        output_dir: Path to output directory (must not exist).

    Returns:
        dict: Manifest report.
    """
    source = Path(source)
    output_dir = Path(output_dir)

    report = {
        'status': 'READY_FOR_EXTERNAL_TP',
        'physical_acceptance': False,
        'input_unit': 'Pa',
        'output_unit': 'bar',
        'identities': {
            'source': {},
            'converted': {},
            'converter': {},
        },
    }

    # Single ownership boundary: create output directory exclusively
    output_dir.mkdir(parents=True, exist_ok=False)

    # Initialize converter identity before any input read
    converter_path = Path(__file__).resolve()
    converter_bytes = converter_path.read_bytes()
    report['identities']['converter']['sha256'] = _sha256_bytes(converter_bytes)

    # Save converter snapshot using captured bytes
    snapshot_dir = output_dir / 'source'
    snapshot_dir.mkdir(exist_ok=False)
    _write_bytes_atomic(snapshot_dir / 'tp_import.py', converter_bytes)

    # Try to read source
    try:
        source_bytes = source.read_bytes()
    except Exception as e:
        report = _fail(report, f"Cannot read source: {e}")
        _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
        return report

    # Save source bytes (preserve original)
    _write_bytes_atomic(output_dir / 'source.pt', source_bytes)
    report['identities']['source']['sha256'] = _sha256_bytes(source_bytes)

    # Parse input
    try:
        text = source_bytes.decode('ascii')
    except UnicodeDecodeError as e:
        report = _fail(report, f"Source is not ASCII: {e}")
        _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
        return report

    lines = text.splitlines()
    if not lines:
        report = _fail(report, "Empty source")
        _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
        return report

    # Parse header
    header_tokens = lines[0].split()
    expected_tokens = ['#', 'P', '(Pa)', 'T', '(K)']
    if header_tokens != expected_tokens:
        reason = f"Header must be exactly '# P (Pa) T (K)' with arbitrary whitespace, got: {lines[0]!r}"
        report = _fail(report, reason)
        _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
        return report

    # Successful header validation
    report['checks'] = ['header']

    data_lines = []
    for i, line in enumerate(lines[1:], start=2):
        line = line.strip()
        if not line:
            continue
        data_lines.append((i, line))

    if len(data_lines) < 2:
        report = _fail(report, "Need at least 2 data rows (blank lines allowed)")
        _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
        return report

    pressures_pa = []
    temperatures_k = []
    for i, line in data_lines:
        parts = line.split()
        if len(parts) != 2:
            reason = f"Line {i}: expected exactly 2 whitespace-separated numeric columns, got {len(parts)}"
            report = _fail(report, reason)
            _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
            return report
        try:
            p_pa = float(parts[0])
            t_k = float(parts[1])
        except ValueError:
            report = _fail(report, f"Line {i}: non-numeric value")
            _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
            return report
        if not (math.isfinite(p_pa) and math.isfinite(t_k)):
            report = _fail(report, f"Line {i}: non-finite value")
            _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
            return report
        if p_pa <= 0 or t_k <= 0:
            report = _fail(report, f"Line {i}: values must be positive")
            _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
            return report
        pressures_pa.append(p_pa)
        temperatures_k.append(t_k)

    # Check strictly increasing pressure
    for j in range(1, len(pressures_pa)):
        if not pressures_pa[j] > pressures_pa[j-1]:
            report = _fail(report, f"Pressure not strictly increasing at row {j+1}")
            _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
            return report

    # Convert to bar
    pressures_bar = []
    for p_pa in pressures_pa:
        p_bar = p_pa / 100000.0
        # Check underflow/overflow
        if p_bar == 0.0 or not math.isfinite(p_bar):
            report = _fail(report, f"Pressure bar underflow/overflow for P_Pa={p_pa}")
            _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
            return report
        # Check that p_bar * 1e6 is representable finite positive
        p_cgs = p_bar * 1e6
        if not (math.isfinite(p_cgs) and p_cgs > 0):
            report = _fail(report, f"Pressure cgs not finite positive for P_Pa={p_pa}")
            _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
            return report
        pressures_bar.append(p_bar)

    # Check no lost order after conversion
    for j in range(1, len(pressures_bar)):
        if not pressures_bar[j] > pressures_bar[j-1]:
            report = _fail(report, f"Pressure order lost after conversion to bar at row {j+1}")
            _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))
            return report

    # Build CSV content
    csv_lines = ['P_bar,T_K']
    for p_bar, t_k in zip(pressures_bar, temperatures_k):
        csv_lines.append(f"{p_bar:.17g},{t_k:.17g}")
    csv_content = '\n'.join(csv_lines) + '\n'

    # Write profile.csv
    csv_bytes = csv_content.encode('ascii')
    _write_bytes_atomic(output_dir / 'profile.csv', csv_bytes)
    report['identities']['converted']['sha256'] = _sha256_bytes(csv_bytes)

    report['point_count'] = len(pressures_bar)
    report['physical_acceptance'] = False
    report['status'] = 'READY_FOR_EXTERNAL_TP'

    # Write manifest
    _write_bytes_atomic(output_dir / 'manifest.json', json.dumps(report, indent=2).encode('utf-8'))

    return report


def main():
    parser = argparse.ArgumentParser(description='Convert native T(P) table to external TP profile format.')
    parser.add_argument('--source', required=True, help='Input source file path')
    parser.add_argument('--output', required=True, help='Output directory path (must not exist)')
    args = parser.parse_args()

    try:
        report = convert_profile(args.source, args.output)
        return 0 if report['status'] == 'READY_FOR_EXTERNAL_TP' else 1
    except FileExistsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
