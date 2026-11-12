# [AI] Reference/source — 100 bar 分界依据与本项目候选值 — 2026-11-12

## 结论 / Conclusion

**中：** 不能从已有 24 点组成网格反推出真实辐射—对流分界。全部 24 个配置固定 surface_temp=350 K、同一 profile.csv 和 gas_hhe_prescribed。温度曲线是输入，不是由能量方程推断出的输出。如果要把这条示范 TP 简化为等温+绝热形式，约 100 bar 是有依据的首个有效折点候选，不是已验证的对流边界。已有来源与端点疑点仍保留；不是在 10000 bar 直接接绝热线的同一个方案。

**EN:** The existing 24-point composition grid cannot identify the physical radiative–convective boundary: every configuration fixes 350 K, the same profile.csv, and gas_hhe_prescribed. Temperature is an input, not an energy-transport prediction. Around 100 bar is a defensible first effective breakpoint for simplifying this example TP, not a validated convective boundary. This differs from appending an adiabat at 10000 bar.

## Desai 的依据 / What supports Desai's choice

**中：** Desai2024 §5.2.2 采用 100 bar 并引用 Nixon2021，没有在该节单独求解此行星的对流边界。Nixon2021 §2.4/Fig.6 用 GENESIS 自洽曲线检验近似，给一般 sub-Neptune 探索约 1–1000 bar 的依据。因此近似形式有比较证据，100 bar 不是普适定律。

**EN:** Desai2024 §5.2.2 adopts 100 bar and cites Nixon2021, without independently calculating this planet's convective boundary in that section. Nixon2021 §2.4/Fig.6 compares against GENESIS profiles and motivates roughly 1–1000 bar exploration for generic sub-Neptunes. The approximation has comparative support; 100 bar is not universal.

## 现有示范 TP 的只读核算 / Read-only check of the example TP

|P/bar|T/K|d ln T / d ln P|Local EOS adiabatic gradient|
|---|---|---|---|
|30|350.000|0.0000|0.3004|
|100|369.358|0.1514|0.2981|
|300|485.049|0.2945|0.2955|
|1000|689.117|0.2867|0.2821|
|3000|939.248|0.2740|0.1881|
|10000|1258.359|0.2383|0.3998|

**中：** TP 温度与斜率使用原代码的 T–lnP 分段关系；EOS 绝热梯度用现有表的双线性插值，轴按 C++ loader 的 float 精度。30 bar 仍接近 350 K；100 bar 已平滑升温；300–1000 bar 的局部斜率接近表中绝热斜率。因此它不是精确的锐利两段模型，但过渡位于百 bar 量级，比把 10000 bar 末行当作起点更有形状依据。深处斜率仍不一致，尚未验证单一绝热线能匹配整条曲线。

**EN:** Temperatures/slopes use the existing piecewise T–lnP relation; EOS gradients use the current bilinear table with loader float-axis precision. The curve is nearly 350 K at 30 bar, warms smoothly by 100 bar, and locally approaches the tabulated adiabat around 300–1000 bar. This motivates a hundred-bar effective transition, not a sharp physical boundary. Deeper slope mismatches remain; no full-profile adiabatic fit was performed.

**中：** 辅助估算：把 300 和 1000 bar 附近的局部斜率临时视为常数，回延到 350 K，交点约 99 和 94 bar。公式为 P_eff=P*(350/T)^(1/nabla)。这是局部幂律形状估算，不是实际 EOS 绝热线积分、不更换原 T–lnP 插值、不构成拟合或行星求解。

**EN:** A descriptive local power-law back-projection to 350 K gives about 99 and 94 bar from the 300- and 1000-bar points: P_eff=P*(350/T)^(1/nabla). This is a local shape estimate, not EOS adiabatic integration, a TP interpolation change, a fitted transition or a planetary solution.

## 建议与限制 / Recommendation and limits

**中：** 若进行原生近似对照，首试 100 bar；30 和 300 bar 可作为相邻对数尺度的敏感性点，均不是物理置信区间。350 K 继续明确为示范输入。不能挑“半径最接近观测”或“让叉消失”的分界作为对流边界证据；组成和热结构之间存在简并。当前没有新计算、扫描、程序修改或 DeepSeek 调用。

**EN:** For an explicitly approximate control, start at 100 bar; 30 and 300 bar can bracket a sensitivity comparison in log pressure, not a physical confidence interval. 350 K remains an example input. Agreement with radius or removal of failed points cannot identify convection because composition and thermal structure are degenerate. No new planet run, scan, source edit or DeepSeek call occurred.

## Reference/source

- Desai2024 §5.2.2: DOI 10.3847/1538-3881/ad29ee; Zotero 6TJSU4T2.
- Nixon2021 §2.4/Fig.6: DOI 10.1093/mnras/stab1500; Zotero 8GC5W4HV; https://arxiv.org/pdf/2106.02061 .
- Code baseline manual-run f7bb58c2399866fca3be723a057d5d8ea213bffc; read-only production inputs, no source changes.
- Original pilot: toi732c-pure-fe-pilot-20261106-run02, grid-01..24/run.cfg, all share the same TP input.
- Example TP CSV SHA256: 304680f64db554b665bc9fbc1563b5814cef435d1da58ad1c03deed3565281bf.
- Full local evidence: D:/Codex/downloads/toi732c-adiabat-literature-20261112/break-pressure.

**中：** 此项放在 Data 顶层作任务来源索引，并交叉列入 Theories_detailed 与 AI-Notes；未归入 solver Output data。

**EN:** Filed as a Data-level task source index, cross-listed in Theories_detailed and AI-Notes, not solver Output data.
