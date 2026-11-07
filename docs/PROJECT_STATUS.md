# Current project state / 当前状态

## 2026-11-07 当前：run稀疏pilot已停止计算

基线26b7b72；纯Fe/独立H2O/HHe、Si0。4代表+1加严实际单例独立审核通过后，固定24点扫描完成：16PASS、8初始TP上边界试探失败（约1.2e-14相对超界，真实解覆盖未知，不能当物理/观测排除）。通过点中最近样本Fe.2997/water.6993/gas.001，R2.373594761773518RE。只有一个未确认中心半径粗交点；完整匹配线、质量误差传播与后验尚未完成。

真实前向31/36：原尝试2+修复后单例5+网格24。已停止，不花余额追加。DeepSeek本段19，项目85/88。hydro组成界面Tt→y[2]单参数修复有RED/GREEN及独立审核；不改EOS公式、表格或阈值。实际执行控制器原字节保存在冻结源中；发布版只读verify的可移植性修复不改变已算结果或执行保护。

原始失败、有效结果、源码/ELF、图、运行与只读核验入口见 [pilot档案](../experiments/pure-fe-pilot-20261106/README.md)。目标发布yt2523/Magrathea的run，master保持26b7b72。下一步只建议诊断TP边界舍入/初始化；本轮不自动补点、加密、加速或推断完整组成线。下文为历史状态，不能据此重启旧实验。

Stage4 completed within a restricted ideal-mu2 engineering fixture; no observed-planet posterior or realistic-EOS inference.

- Original B1%truth→A30 experiment:8individual fits passed checks, overallFAILED at endpoint nonbracketing. That immutable evidence remains in experiments/prescribed-tp-20261028/.
- New user-authorized reciprocal A1%truth→B40 follow-up:PASS_LOCAL_ENGINEERING_RECOVERY. Inferredgasfraction0.0024360387783536647 (0.243603878%), signedbias−0.007563961221646336, relative−75.6396%. This direction was selected after the original failure; it does not rescue that target or prove general invertibility.
- Actual signed numerical interval[0.0024303854921362464,0.0024360387783536647], width5.6533e-6. Nominalradiuserror2.0373e-8; same-fraction tight/refined confirmations pass. Interval is not statisticalconfidence; uniqueness/globalmonotonicity/realEOSvalidity unproved.
-6new full fits,14cumulative of20 ceiling;0new API,author44/44 unchanged. No original8cases rerun, no C++/EOS edits. Twelve pure verifier tests and fresh independent saved-artifact/report audits passed.

Read [new report/figures/rawdata](../experiments/prescribed-tp-reciprocal-20261030/README.md) and [original failure](../experiments/prescribed-tp-20261028/README.md). Archived bytes and scripts are together; verify_archive.py never runs models. Physics source3608c3d unchanged; follow-up plan/contract was committed223374d before its first fit. Source, binary,51 dependency files and80 cached artifacts matched.

Stage5 paper-profile/real-EOS work has not started. The prior read-only H/He table inventory is not physical validation. Confirm source/composition/range and explicit out-of-range failure before a real-EOS/new-experiment contract. Existing HHe_tabulated has a100bar hybrid selector and legacy edge fallback; moving gas_default’s switch changes both thermal law and molar mass3→2.

Do not auto-spend remaining model calls or extend paidAPI budget. The user authorized continuation through Stage4, now fulfilled in this bounded conditional sense. A new operator’s generic workflow uses their own explicit config/budget/run_dir; cloning or doctor never authorizes science runs. The portable API workflow is not claimed to have orchestrated these experiments.

Historical54/8/67 grids and original dirty research checkouts remain preserved; no install/auth repeated. New artifacts remain onD:. [Implementation ledger](TP_IMPLEMENTATION_PROGRESS.md), [acceptance](TP_ACCEPTANCE.md).


## 2026-11-02 operator budget update

The operator doubled the tracked project DeepSeek ceiling44→88; see `workflow/project-budget.json`. Historical TP implementation44/44 records describe that closed phase; they are not the current global authorization gate. This conversation’s authorized work may use DeepSeek without per-call confirmation; do not ask repeatedly about the superseded44-call ceiling. Generic per-run max_model_calls values were doubled (fallback12→24, live example6→12, offline demo12→24); that counter includes coder and reviewer logical launches, not DeepSeek-only billing. Project88 policy does not automatically aggregate independent operators/portable runs. Scientific fit ceiling20 and closed historical contracts remain unchanged; no new physics experiment is authorized by increasing API budget.


## 2026-11-06 main-program first slice

DeepSeek implemented `workflow/single_case.py`; Codex fixed the contracts/tests, diagnosed failures, and obtained independent complete-code approval. 24 fixed tests plus the transport compatibility test passed after byte-identical integration. Mock success, invalid composition, intentional adapter failure and overwrite refusal were freshly demonstrated. Archive: [engineering smoke](../experiments/main-smoke-20261106/README.md), including read-only hash verification and original controller verdicts/summaries. All outputs remain engineering fixtures; physical_acceptance=false. No new full planetary solve/grid/fit or EOS changes; historical experiments unchanged.

The current API's default thinking behavior exhausted two bounded response budgets. DeepSeek authored a separately reviewed `deepseek_nonthinking.py` compatibility CLI that reuses the entire existing Runner and only sets explicit disabled thinking for DeepSeek requests; original portable.py bytes unchanged. This milestone used12DeepSeek launches including failed transports/proposals, project tracked total62/88; new scientific full fits0 (historical14 unchanged).

User-provided example TP inspected locally:400rows, Pa/K whitespace text, pressure1–1e9Pa; requires explicit Pa-to-bar CSV adaptation before existing interface use. Raw example remains in D:/Codex/downloads/toi732c-inputs/20261106, not uploaded. Next proposed minimal slice: explicit format/unit adapter with original/converted identities and the same mock pipeline; production boundaries/parameters and real-solver runtime contract still pending. Stop after publication for user inspection; no further complexity automatically started.


## 2026-11-06 external TP and real forward-engineering bridge

User authorized finishing the Pa/K importer then trying the real calculator using interpolation. The new importer and native TPProfile query helper passed11fixed tests and independent code gate. All400source temperatures/points were retained, Pa divided by100000 to bar,400native-node and6reference-pressure checks passed, and the converted profile passed existing mock integration.

A clean unmodified physics-source build then executed2new authorized forward engineering calls (baseline plus tighter numerical confirmation) under a separately frozen max2x180s contract. The same test composition used M8.04ME, gas0.001, prior nongas proportions25:55:19, P0=.1bar/T0=350K from userTP, idealgas_fixed_mu2 and existing solid EOS. Radii2.1483191091726397/2.148319087507168RE differ relatively1.0084847984849868e-8. Both original independent check_tp_model verifications and a fresh read-only Codex result audit passed;12163gas rows each, gasbase~4575.4bar/~1051.64K, inside supplied1e-5–1e4bar. Gas uses externalTP; deeper water/rock/iron retain original thermal model.

[Self-contained archive](../experiments/external-tp-bridge-20261106/README.md) includes exact original/converted TP, frozen contracts, actual ELF and39compiled dependency byte identities/snapshots, real logs/diagnostics, pure read-only verification and TP-use figure. Original run contracts remain unchanged; derived archive-local source paths retain all39hashes and every numeric criterion. No extra solver run for archiving. The real ledger is closed at2; old14-fit study remains closed and separate. DeepSeek this follow-up4calls, project66/88; no physics/EOS source edits, grid or composition inversion.

Engineering pass only, physical_acceptance=false: formal H/He density EOS, composition, radius reference pressure and userTPphysical provenance remain major user decisions. Stop after publication; no automatic expansion.
