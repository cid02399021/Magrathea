# [AI] Reference/source — 深层 H/He 绝热线延伸适用性 — 2026-11-12

## 任务和版本 / Task and version

**中：** 判断示范 TP 到 10000 bar 后能否沿真实 H/He 绝热线延伸，核查 MAGRATHEA 他人实践。生产基线 manual-run=f7bb58c2399866fca3be723a057d5d8ea213bffc；当前研究分支核查点 fb62774e64bebf87f243c28b14f38c23855ac8a4。只做文献与只读算术；没有新行星结果，未改 TP/EOS，DeepSeek 调用 0。

**EN:** Assessed a real-H/He adiabatic continuation beyond the example TP endpoint and published MAGRATHEA practice. Production baseline: manual-run f7bb58c2399866fca3be723a057d5d8ea213bffc; checked research revision fb62774e64bebf87f243c28b14f38c23855ac8a4. Literature/read-only arithmetic only: no new planetary output, no TP/EOS edits, zero DeepSeek calls.

## 参数、假设和未知 / Quantities, assumptions and unknowns

**中：** 测试输入 P_end=10000 bar=1 GPa、T_end=1258.359116298232 K。最后一段 d ln T/d ln P=0.2383073；本地 EOS 表在接点给出 (dT/dP)_S=503.1489005 K/GPa，对应绝热斜率 0.3998452。这些是代码输入/查表量，不是观测量，无观测误差声明。文件来源、对流边界和辐射输运条件未确认。局部表与官方文件统一换行后一致，不等于原始 EOS 物理复核。结论：方法有依据，当前接点存疑，按用户要求先讨论。

**EN:** Test input: P_end=10000 bar=1 GPa and T_end=1258.359116298232 K. The last-segment gradient is 0.2383073; the local EOS derivative is 503.1489005 K/GPa, corresponding to 0.3998452. These are input/table quantities, not observations with measured uncertainties. TP provenance, convective boundary and radiative transport are unresolved. Upstream file identity is verified, not independent EOS physics. The method is supported, but the matching point requires discussion.

## 原始出处与详细笔记 / Sources and detailed notes

|来源 / Source|DOI / URL|Zotero key|用途 / Use|
|---|---|---|---|
|Rigby & Madhusudhan|10.1093/mnras/staf1969|DPX9K7GU|§2.2 温度延伸 / TP extension|
|Huang et al.|10.1093/mnras/stac1133|5I8L47YV|§3.3.4 原版热结构 / Native thermal closure|
|Rice et al.|https://arxiv.org/abs/2510.23733|AAZH3A9T|v2 表格接口 / Table interface|
|Desai et al.|10.3847/1538-3881/ad29ee|6TJSU4T2|§5.2 实际使用案例 / Actual application|
|Acuña et al.|10.1051/0004-6361/202450559|M2SX3N9T|§2.1/3.1 连接及对流判据 / Matching and stability|
|Leconte et al.|10.1051/0004-6361/201629140|U8ZCS9IP|§2/4 对流抑制条件 / Convective inhibition|
|Chabrier & Debras|10.3847/1538-4357/abfc48|3ZAT3T6W|§3 熵与绝热线 / Entropy and adiabats|
|官方文档 / Official docs|https://magrathea.readthedocs.io/en/latest/models/phasediagrams.html|7SXTN49W|现有气体接口 / Gas interfaces|
|官方讨论 / Official issues|https://github.com/Magrathea-model/Magrathea/issues|R7XAQIAN|#11/#12 温度和熵问题 / Thermal/entropy issues|

**中：** 综合报告在 Main → Magrathea theory → Theories_detailed（key 86NGGPHP），并交叉索引 AI-Notes/PT-Inversion-2026；阅读笔记挂对应论文。这一条只作为 Data 顶层的本任务来源索引，不把文献核查冒充 solver Output data。

**EN:** The synthesis is in Main → Magrathea theory → Theories_detailed (key 86NGGPHP), cross-indexed in AI-Notes/PT-Inversion-2026; reading notes are paper children. This Data-level record is a source index, not solver Output data.
