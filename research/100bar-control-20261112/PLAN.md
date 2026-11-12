# 100-bar native thermal-control implementation plan

**Goal:** Test the already-authorized isothermal/adiabatic HHe_tabulated approximation at 100 bar on the old grid14 success and grid20 failure, without changing production physics or claiming a physical RCB determination.

**Architecture:** Reuse the unchanged native CLI/solver and EOS tables. DeepSeek authors two manual configurations and a small C++ audit wrapper that includes the unchanged main.cpp with its entry point renamed, enabling strict table audit before calling that CLI. A separate wrapper mode checks saved profiles against native EOSs and probes the switch. Codex owns orchestration, fixed criteria and independent result review.

**Tech stack:** Existing C++0x/GSL/WSL build; Python standard-library controller outside the user release. No dependencies installed.

## Scope and limits

- Preserve repo production src, tabulated, input, run, Makefile and old output bytes; build a fresh source copy under this D-drive task directory.
- HHe_tabulated remains the original hybrid: P<100 bar ideal isothermal gas with molar mass 3; P>=100 bar tabulated real H/He with its adiabatic gradient. Do not silently change molar mass or EOS.
- Use existing example boundary P0=0.1 bar and T0=350 K, mass=8.04 Earth masses, zero silicate, zero T gaps. These are conditional example inputs.
- grid14 mass fractions Fe=.2997, water=.6993, gas=.001; grid20 Fe=.2991, water=.6979, gas=.003. Use exact old configuration masses, not independently rounded reconstructions.
- New task budget: exactly max1 DeepSeek API launch; current tracked87/88 -> at most88/88. No automatic API repair after exhaustion.
- New task budget: max4 native planet launch attempts, each180 seconds, ordered grid14 baseline, grid20 baseline, then each tighter repeat only for a baseline with an actual saved converged solution. Invalid launches count. Max2 compile attempts, no physics repair or grid expansion. EOS probes/profile checks do not integrate planets.
- Tight repeat: ode_eps_rel0=1e-8, ode_eps_rel1=1e-11, ode_eps_rel2=1e-11, R_eps_rel=2e-6, P_eps_rel=1e-11, fit_eps_rel=1e-7; all masses, material choices and outer boundaries fixed.
- No 30/300-bar exploration, no no-water/mass-uncertainty scan, no composition inversion, no new formal TP.

## Review focus

1. Native CLI can exit0 without a solution: require newly saved nonempty model and positive finite output, not exit0 alone.
2. The 100-bar switch changes EOS/composition approximation: measure one-sided and common-P densities; do not conceal a finite jump or call it a physical phase transition.
3. Final dat has8 significant digits: use predeclared density tolerance2e-6, no precision claims copied from full-double TP sidecars.
4. Strict table audit must be enabled before native integration; no silent nearest-edge EOS fallback. Report rejected trial queries separately from final-state coverage.
5. Water/Fe thermal phases and transitions may change under the new thermal model: list phases, check stored density at stored P/T, report suspect joins rather than patching them.

## Tasks

- [ ] Freeze plan/contract and production file identities; retain the old cases and radii as comparisons, not numerical targets.
- [ ] One DeepSeek call: write only native_audit.cpp plus grid14.cfg/grid20.cfg. No production edits. Codex checks proposal paths and diff before applying.
- [ ] Compile fresh native objects and wrapper. Probe at 100 bar from both sides and at exactly100 bar; preserve raw results. If source cannot be compiled from a valid proposal within2 attempts, stop without self-coding.
- [ ] Execute two baseline cases under the four-attempt ledger. On failure retain logs and stop that case; no repair loop.
- [ ] For each saved baseline, check all rows and perform one tight repeat. Independently compare radius and representative gas P/T states. No pass threshold changes after seeing results.
- [ ] Fresh uninvolved Codex reviewer reads exact proposal, frozen criteria, source hashes, actual outputs and conclusions; reports passed/failed/insufficient evidence with limitations.
- [ ] Save example configs and concise report/evidence to research branch; keep large raw outputs outside Git with byte identities. Zotero: Data source index, Output data new task collection for actual summaries, theory cross-link; no overwriting prior items. Verify pushed SHA and manual-run/master unchanged.

## Fixed acceptance and classifications

- Engineering run success: actual nonempty output, all rows finite; r>=0, m>=0, P>0, T>0, rho>0; total mass agrees within1e-7 relative; surface P/T agree within1e-7 relative; both Fe/water and expected gas EOS branches present.
- Stored-state EOS check: all phase labels resolve; native reevaluation relative density error<=2e-6; final gas queries inside HHe table rectangle; near-switch selector disagreements confined to relative pressure1e-6 and explicitly counted.
- Low-pressure gas temperature relative deviation<=2e-6 from350K; no forced isothermal claim for other material layers.
- Deep gas thermal-law residual is a diagnostic with pressure intervals/cell crossings reported, not an invented global smoothness guarantee.
- Numerical convergence: baseline vs tighter radius relative difference<=1e-5; if final profiles allow common gas pressure1000bar, also temperature relative difference<=1e-3. Report endpoints/switch P/T differences and failures even if radius passes.
- Artificial-switch physical consistency flag: at common100bar/350K densities differing by>1% gives FAIL_HYBRID_DENSITY_CONTINUITY, regardless of solver convergence. This flag does not prohibit the authorized two-case exploratory control, and must prevent publication as a physically certified production model.
- Overall status can be CONDITIONAL_NUMERICAL_PASS_WITH_HYBRID_LIMITATION, NUMERICAL_FAIL, or INSUFFICIENT_EVIDENCE. Physical_acceptance remains false; no threshold is chosen to fit observed radius.
