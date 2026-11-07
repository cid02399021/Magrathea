# Pure-Fe/water/H-He coarse pilot on run

Base26b7b72. User authorized work on run, stop after a sparse-grid test/initial matching. No acceleration, final inference or large grid.
- Si mass=0; pure Fe + independent water + H/He. Existing four computational slots retained, skipped slot audited.
- Adopt Fe_default/water_default conditionally. Check actual pointer dispatch, density consistency, table domains and thermal_type; do not certify empirical phase stability or a common thermodynamic potential across seams.
- Uniform existing ChabrierHHe0275 under native external T-lnP, selector gas_hhe_prescribed. No100bar hybrid; no EOS formula changes. Preserve legacy float-loaded axes in independent table reconstruction.
- Opt-in strict table density AND gradient bounds, returning NaN rather than edge values. Record rejected numerical trials separately; all accepted states must be in domain.
- Fixed example TP, M8.04ME, P0=.1bar/T0=350K from native query. Conditional scenario. TP-unsupported cases are not observational exclusions.
- Pilot comparison Rtarget2.39RE, radius-only axis interval[2.28,2.49] at fixed mass; no mass-error propagation/posterior bands.
- DeepSeek bounded exact-replacement proposal, fixed Codex tests, fresh reviewer on applied source before integration. Large files are not blindly rewritten.
- New audit API, stable pointer IDs (display names can collide), schema2 diagnostics with per-row material/actual and expected EOS IDs, density re-evaluation, thermal_type, phase-boundary tolerance1e-7, density/gradient counters, rejected table count. Si must have no density queries or accepted rows.
- Representative compositions(Fe,water,gas):(.30,.699,.001),(.10,.8999,.0001),(.9999,0,.0001),(.50,.49999,.00001); tight baseline confirmation. Must pass the single-case gate before grid.
- Sparse24points: gas[1e-5,1e-4,1e-3,.003], nongas core share u[.1,.3,.5,.7,.9,1]; fFe=(1-fgas)u, fWater=(1-fgas)(1-u). Dry branch included. No zero-HHe substitution.
- Max36NEW planet launches including probes/confirmations/diagnosis, <=180s each, serial. Closed14-fit and2-forward contracts not reused.
- Preserve holes/failures. Report best actual sample and coarse adjacent-valid crossings only, all branches; interpolated candidates explicitly unconfirmed. Ternary plus log gas/core panel. Stop after sparse pilot.
- Runnable validated release/config/README on run; master unchanged. DeepSeek cap88/current66 remains binding.
Ruling (2026-11-06): use DeepSeek for all EOS/main diagnostics and pure
composition/CFG/interpolation implementation. The experiment run_pilot.py is
Codex's predeclared deterministic scientific verification controller per AGENTS:
freeze bytes, build identified existing solver, execute the fixed case catalogue,
count launches before execution, call the independent checker, save evidence.
It implements no EOS, TP interpolation, composition formula, or fitting method.
A fresh read-only reviewer must approve the complete combined code before use.
The single stage stops before grid for independent actual-result audit.
