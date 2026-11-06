# Single-case engineering smoke implementation plan

Spec: docs/HANDOFF-LITE-20261106.md. Authorized implementation: DeepSeek; independent acceptance: Codex. No science execution.

Architecture: Python standard-library single-case entry workflow/single_case.py, callable adapter solve(config), separate check_result. Reuse tests/check_tp_model.py finite_tree; retain exact P_bar,T_K format. Existing C++ entry/TP evaluator/physical checker remain intact. The real checker cannot certify this mock schema.

- [ ] Codex freezes tests/test_single_case.py and fixture config/TP. Run RED before builder.
- [ ] DeepSeek implements only workflow/single_case.py in D: staging, never tests/contracts.
- [ ] Codex runs fixed tests; diagnose failures and return bounded repairs to DeepSeek.
- [ ] Run CLI demonstration in a fresh experiments/main-smoke-20261106 directory. Preserve source/config/TP SHA256, snapshots, checks and failure reason. Reject existing output paths.
- [ ] Read-only independent review, archive evidence; scoped commit and verify remote upload.

Interface: run_case(config_path, output_dir, solver=None) -> persisted report dict. Adapter object has solve(config) -> dict, default MockSolver. main CLI --config --output. Result keys origin=MOCK_SOLVER, mass_earth, radius_earth, physical_acceptance=false. Reports status=ENGINEERING_SMOKE_PASS/FAILED, physical_acceptance=false, reason, checks, identities. Files config.json, tp.csv, result.json (if returned), report.json. Input label must SYNTHETIC_FIXTURE; schema_version=1; units mass=M_earth, pressure=bar, temperature=K; positive mass_earth and outer P/T; fractions exactly iron/silicate/water/hhe, each finite [0,1], sum within 1e-12; hhe>0 and some solid. TP required relative to config, strict header/two columns, >=2 positive finite increasing nodes, cover outer_pressure_bar and match outer_temperature_K by T-lnP interpolation. Test values are arbitrary fixtures, never production defaults.

Review focus: bool/nonfinite numbers; malformed/duplicate TP; missing files; malformed/false-result adapter; no overwrite including preexisting empty directory; input mutation during adapter; no mock physical pass. Adapter failures produce FAILED report. Invalid config must not invoke adapter. No subprocess/model launch in smoke controller. Future real adapter requires separate bounded runtime contract and genuine diagnostics; not enabled now.
