# [AI] TOI-732 c — 深层绝热线延伸：适用性与连接疑点 — 2026-11-12

## 判断 / Decision

**中：** 真实 H/He EOS 绝热线延伸有直接文献依据，适合作为条件性热结构模型；但当前证据不足以把示范 TP 的 10000 bar 截止认作已确认的对流连接点。按用户“有犹豫先讨论”的要求，本轮不改生产代码、不接 ideal gas、不启动原生行星计算、不调用 DeepSeek。保留严格 TP 模式和旧失败记录。疑点是物理连接条件，非技能要求的审批。

**EN:** A real-H/He EOS adiabat is a literature-supported conditional thermal model. Current evidence does not establish the example TP endpoint as a convective matching point. Following the user's instruction to discuss uncertainty first, no production code, ideal-gas switch, native planet run, or DeepSeek call was made. The uncertainty concerns physical matching, not a skill-imposed approval gate.

## 何时合理 / Conditions of validity

**中：** 深层光学厚并不自动保证对流；在组成近似均匀、对流有效输热的区域，温度可接近等熵绝热线。需有辐射输热要求的梯度超过绝热梯度的证据，或明确将深层对流作为待检验模型假设。若存在稳定组分梯度、凝结抑制、辐射层或相分离，就不能直接使用单一均匀干绝热线。Leconte 的含水限制不等于本项目纯 H/He 测试已经发生该效应。[Leconte2017, §2.1–2.2; Acuna2024, §3.1]

**EN:** Optical thickness alone does not ensure convection. Efficient convection in a nearly homogeneous layer permits an approximately isentropic profile. Convective stability must be evaluated, or convection explicitly declared as a model assumption. Composition gradients, condensation inhibition, radiative zones and phase separation can invalidate a homogeneous dry adiabat. The water-related caveat is not a diagnosis of our pure-H/He test. [Leconte2017, §2.1–2.2; Acuna2024, §3.1]

**中：** 若采用该假设，应沿同一 H/He EOS 给出的 (dT/dP)_S 积分，以连接点温度作边界；不把 gamma 固定为理想气体值。压力、温度、密度连续要检查，且只延伸气层，不把气层绝热线直接套进水层和铁核。连续并不能代替能量输运验证。[Chabrier2021, §3; 项目推断]

**EN:** Integrate the same H/He EOS adiabatic derivative from the matching temperature, rather than imposing a fixed ideal-gas gamma. Check pressure, temperature and density continuity. Continue only the gas layer; water and iron retain their own thermal closures. Continuity does not establish energetic consistency. [Chabrier2021, §3; project inference]

## 本项目数值核对 / Local numerical check

|量 / Quantity|结果 / Value|
|---|---|
|示范 TP 末端 / TP endpoint|P = 10000 bar = 1 GPa; T = 1258.359116298232 K|
|最后一段 T–lnP 左侧斜率 / Left-sided last-segment gradient|d ln T/d ln P = 0.23830726173199773|
|现有表格绝热导数 / Existing tabulated adiabatic derivative|503.1489004817865 K/GPa|
|对应绝热斜率 / Corresponding adiabatic gradient|0.3998452381081172|
|H/He 密度 / H/He density|0.12202316523805336 g/cm³|

**中：** 以上为只读算术核对：用与 C++ 相同的双线性方式，轴值按 loader 的 float 精度处理；不是新行星积分。0.238 与 0.400 的差异表明当前曲线末段不接近该表的绝热线。对均匀组分的局部判据，这是亚绝热斜率；不能据此声称末端已经对流。也不能由此推断更深处永远不对流。任意接上绝热线可以保证温度连续，但会引入斜率折点；折点不是数学上禁止，而是未经验证的热结构选择。

**EN:** These are read-only calculations using the existing bilinear table and loader float-axis precision, not a new planet integration. The last TP segment is substantially shallower than the tabulated adiabat. In the homogeneous local criterion it is subadiabatic; this neither establishes convection at the endpoint nor excludes it deeper down. A continuous-temperature splice would introduce a slope change: mathematically possible, physically unverified.

**中：** 目前缺少该示范文件的生成来源、连接点的对流判据，以及评估辐射输运所需的对应不透明度/内部通量条件。此前 grid20 的初始低半径试探到 10000 bar 时还有约 18.3% 气层质量未积分；那不是最终物理解。热结构补全与“域外初始试探导致整组提前失败”是两个独立问题。

**EN:** Missing information includes the TP provenance, convective matching criterion, and opacity/internal-flux conditions needed for radiative transport assessment. In the earlier grid20 low-radius initial trial, about 18.3% of the gas remained at 10000 bar; that trial was not a final solution. Thermal coverage and premature termination from an invalid initial trial are separate issues.

## 别人怎样做 / Published practice and upstream reports

|来源 / Source|已核查内容 / Verified scope|对当前问题的意义 / Implication|
|---|---|---|
|Rigby2025 §2.2|GENESIS 到 1000 bar，之后接 H/He 绝热线 / GENESIS to 1000 bar, then H/He adiabat|支持方法，未验证我们的接点 / Supports method, not our matching point|
|Huang2022 §3.3.4|默认低压等温、100 bar 以上绝热 / Default isothermal upper atmosphere, adiabatic deeper than 100 bar|不依赖有限外部 TP / Does not depend on a finite external TP file|
|Rice2025 Major updates|新增真实 H/He 与四列热力学表 / Adds real H/He and four-column thermodynamic tables|已有可复用接口 / Existing reusable interface|
|Desai2024 §5.2, Fig.7|实际用 MAGRATHEA、真实 H/He、100 bar 以上绝热 / Actual MAGRATHEA use with real H/He and deeper adiabat|直接使用实例，非我们的端点 bug 修复 / Application, not our endpoint repair|
|Acuna2024 §2.1, §3.1|大气与内部在 1000 bar 连接；大气检查对流 / Atmosphere/interior matching and stability checks|方法借鉴；非 8.04 M⊕ 的直接验证 / Method reference, not validation at our mass|

**中：** 官方 GitHub 本次返回 42 条 issues API 记录，其中真正 issue 8 条、PR 34 条（单页少于 100，没有下一页）。未找到与本项目自定义外部 TP 在 10000 bar 截止完全相同的公开报告，这不证明别人从未遇到。Issue #11/#12 记录过新增 EOS 的温度/熵插值问题：维护者建议正确提供梯度或熵、检查导数与热标签、验证插值光滑性；#12 最终以确认找到问题而关闭，但没有公布一个可等同我们当前错误的具体补丁。

**EN:** The upstream issues API returned 42 records: 8 issues and 34 PRs, with no next page. No exact report of our custom 10000-bar external-TP cutoff was found; this is not proof nobody encountered it. Issues #11/#12 concern custom-EOS thermal/entropy interpolation. Advice includes correct thermal interfaces, derivative/tag checks and smooth interpolation. Issue #12 was closed after confirmation that the problem was found, without an exact equivalent patch for our endpoint failure.

**中：** 本地 ChabrierHHe0275 四列表与官方同名文件统一换行后一致。这只核查 repository 来源，不是作者原始 EOS 表的逐点物理验收；表格数值范围也不等于所有物态范围有效。

**EN:** The local four-column table matches its upstream namesake after line-ending normalization. This verifies repository provenance, not pointwise physical validation against the EOS authors' original distribution or every phase in the numerical rectangle.

## 下一步选择 / Next decision

**中：** 建议先保持原 TP 修好域受限的半径初始化；若需要检验“深层均匀 H/He 对流”假设，可另做显式开关的条件性试验：原 TP 到 10000 bar 原样保留，之后沿同一真实 EOS 延伸，只重试 grid20 与一个旧成功点，并检查连接连续性、步长收敛和新高压状态。不自动改默认模式或重跑网格。该试验若算通，只能证明这个新增假设下可计算，不能宣称原 TP 已获补全验证。

**EN:** Prefer retaining the original TP while repairing domain-aware radius initialization. A separately approved conditional experiment could preserve all original TP nodes, continue homogeneous H/He adiabatically with the same real EOS, and test only grid20 plus one successful control, checking matching continuity, numerical convergence and the new deep states. It would test an additional thermal assumption, not validate the unknown original TP. No experiment or implementation was launched in this literature task.

## 来源 / Sources

- Rigby & Madhusudhan: https://doi.org/10.1093/mnras/staf1969 ; https://arxiv.org/html/2511.16722v1#S2.SS2
- Huang et al. 2022: https://doi.org/10.1093/mnras/stac1133
- Rice et al. 2025: https://arxiv.org/html/2510.23733v1
- Desai et al. 2024: https://doi.org/10.3847/1538-3881/ad29ee
- Acuña et al. 2024: https://doi.org/10.1051/0004-6361/202450559
- Leconte et al. 2017: https://doi.org/10.1051/0004-6361/201629140
- Chabrier & Debras 2021: https://doi.org/10.3847/1538-4357/abfc48
- Official phase options: https://magrathea.readthedocs.io/en/latest/models/phasediagrams.html
- Upstream issue #11: https://github.com/Magrathea-model/Magrathea/issues/11
- Upstream issue #12: https://github.com/Magrathea-model/Magrathea/issues/12
