# TOI-732 c 第一段：单案例工程烟测

范围：测试配置 → 输入校验 → 可替换 `solve(config)` adapter → `MOCK_SOLVER` → 独立结果检查 → 全新目录保存。所有测试输入标记 `SYNTHETIC_FIXTURE`，所有假结果标记 `MOCK_SOLVER`；`physical_acceptance=false`。固定假半径2.0只是任意工程数值，不是预测或观测拟合。

复用现有 `tests/check_tp_model.py` 的 `finite_tree` 和既有 `P_bar,T_K` 格式；原 C++ 入口、TP evaluator、EOS 与历史实验字节不变。`workflow/single_case.py` 由 DeepSeek 编写，Codex负责合同、固定测试、诊断和独立验收。配置校验、adapter、单例控制、结果检查、身份与输出五个职责保持在单案例模块中，不预建网格平台。

实际证据：`evidence/tests-24.log` 记录24项测试；`success/` 为成功烟测；`rejected-input/` 为组成不守恒；`failed-adapter/` 为有意抛错的假adapter；`evidence/refuse-overwrite.log` 和 `demo-summary.json` 记录重复输出路径退出1、旧文件哈希保持不变。每个案例保留可读配置/TP及源码快照、哈希、已完成检查和失败原因。缺失输入不伪造身份。

`evidence/whole-code-review.json` 是独立代码集成门的结论摘要，来源为控制器保存的真实状态，并非伪造原始provider响应。`controller-state.json` 保留原始控制器状态，不将“缺少归档/Git证据”的拒绝改写为通过。后续集成判断与原始结论分开记录。`red-baseline-reproduction.log` 是从冻结的pre-builder副本重新运行得到，明确不是伪装成当时原始日志；当时已观察到缺少实现的RED。

## 只验档案，不跑模型

```powershell
python -B experiments/main-smoke-20261106/verify_archive.py
```

## 手动新建一次假solver演示

从仓库根目录执行，输出路径必须尚不存在，父目录须已存在：

```powershell
python -B workflow/single_case.py --config experiments/main-smoke-20261106/inputs/main-smoke.json --output D:/Codex/downloads/toi732c-smoke-NEW
python -B tests/test_single_case.py
```

结果目录包括原始配置/TP、返回结果（若已返回且可序列化）、执行源码/复用检查器快照，以及带身份和检查的report。adapter返回null也保留；非有限结果被拒绝。主报告与fallback都写失败时抛错，CLI非零退出，不重试成成功。

当前DeepSeek API默认thinking模式与旧控制器输出预算发生兼容问题。由DeepSeek编写并经独立审核的 `workflow/deepseek_nonthinking.py` 只显式设置DeepSeek请求的thinking disabled，其余隔离、预算、测试和只读审核逻辑仍复用 `portable.Runner`，原 `portable.py` 不变。官方参数依据：https://api-docs.deepseek.com/guides/thinking_mode/ 。两次输出协议失败及所有返修均计入项目账本，未有效解析的请求不冒充代码修复证据。

## 限制与下一段最小改动

本段没有调用真实行星solver、grid、拟合或修改物理EOS，也没有重跑封存实验。真实TOI-732 c参数、TP生成原理、EOS适用范围与生产边界尚未验收；工程通过不表示物理或观测拟合通过。

用户新给的 `pt_profile.txt` 为400点空白分隔示范，表头P(Pa)/T(K)，压力1–1e9 Pa，温度约350–1258 K；格式检查为正有限、压力严格递增。原始示范文件仅保存在D盘本地输入目录，没有上传原始内容。它不是已批准的生产TP。

下一段建议只增加显式输入格式适配：Pa除以100000转bar、保留原始与转换后TP身份、验证两者点值一致，再用同一mock单例闭环验收。不改变controller，不选生产P0/T0，不启动真实solver；待正式参数交付后另立有界真实solver单例合同。
