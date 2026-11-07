# TOI-732 c：空白聊天轻量交接

更新：2026-11-06。本文件独立可读，不依赖旧聊天。用户自己新建空白窗口；不要创建/分叉聊天，也不要自动读取旧聊天历史。

## 2026-11-07 六项核查与Zotero正式交付接收

已只读核查用户六问并接收Zotero V7QBAMEP(version2667)和8份文本/CSV/模板；对方未生成TP节点/脚本，TP生成仍UNASSIGNED。资料在D:/Codex/downloads/toi732c-handoff-review-20261107，原件不上传Git。本轮0新solver/DeepSeek，旧pilot保持停止。详见docs/workflow/SCIENCE_REVIEW_20261107.md与ZOTERO_STORAGE_RULES.md。

新发现未修：TP步进结点舍入与中间RHS严格TP域检查可能不一致（不能确认8例全由此造成）；hydro部分路径先解引用Phase再判空，需受控失败回归。对方旧mu2/study接口和lnT-lnP插值说明与现有CSV/HHe Y.275及T-lnP不一致，后续不得静默替换。用户要求同时考虑M/R误差的面积，当前24点仍固定M，只是初步工程测试；下一步建议先小回归/防护，再另立有界M维度任务，不能自动花旧余额。规则按用户PDF和实际collection核对，已同步同项目LR profile索引，保护历史items。

## 最新现场（2026-11-07，优先于全部旧段落）

本轮纯铁核+独立水+HHe（Si0）稀疏测试已完成并停止计算；基线26b7b72，开发/发布run，master不变。不要读取旧聊天、创建/分叉聊天或重跑历史实验。当前只收尾归档验收/发布。

实际31/36新前向：run01两次（第一通过、第二界面密度不一致失败）；DeepSeek仅修hydro.cpp组成入口密度调用Tt→y[2]，合成RED.00233805→GREEN0，144探针/mainbuild及独立门通过；run02四代表+首例tight全部获独立实际审核，随后24grid=16PASS/8初始TP上边界试探失败。D:/Codex/downloads/toi732c-pure-fe-pilot-20261106-run01与run02原件不覆盖；保真档案experiments/pure-fe-pilot-20261106/data/。不得用剩余5次继续模型。

最近直接点仅指16通过点中：Fe.2997/water.6993/gas.001，R2.373594761773518RE。中心半径只有一个未确认粗交点，完整组成线尚未得到。8失败查询比TP上限1e10cgs高约1.2e-14相对，可能边界舍入/初始化，不能认定真实解必须更深TP，更不能当观测排除。下一新步骤建议先专门诊断此边界，不自动扩大扫描。

DeepSeek85/88，本段19次，来自真实runner usage，无预留；不再调用API。旧14拟合与旧2桥接合同继续关闭。完整代码门、修复和实际单例门证据在档案evidence；最终数据/发布复核另存final-review.json。运行入口run_pilot.py single/grid；只读verify、verify_archive.py及plot_pilot.py不跑模型。发布只读verify修复不改计算路径/执行保护，实际执行控制器原字节冻结在data/run02/frozen-source/run_pilot.py。

固定示范TP/M8.04/目标R2.39/区间[2.28,2.49]；外部TP仅气层，原水铁热结构保留（表格10、Mazevet2、IceX0等）。physical_acceptance=false，未传播质量误差或算后验。单元日志模拟2.4RE不是实际结果；来源标签明确。DeepSeek写计算代码，Codex负责固定验收编排/测试/诊断/分析存档；portable.py未改。

## 最新状态：外部TP与真实程序已算通（同日后续授权，优先于下文）

用户后来明确授权查相关旧聊天里的代码分析网站，完成TP适配后尝试真实程序，并自行插值取值，只在重大决策/无法继续时询问。本轮已完成，不要重复计算：`workflow/tp_import.py`＋`workflow/tp_query.cpp`经DeepSeek实现、11项固定测试和独立代码门通过。400点原温度均保留，只做Pa→bar；现有TPProfile负责T-lnP，未重写EOS/TP算法。

真实C++从干净源码副本构建，实际运行2次（同组成基准＋加严容差，新的max2x180s合同且账本已关闭）。测试设定M8.04ME、气体0.1%、非气体比例25:55:19、P0=.1bar、T0=350K由用户TP取得、理想gas_fixed_mu2。R=2.148319109/2.148319088RE，相对差1.0085e-8；气层底约4575bar/1052K，未超用户TP范围。两份高精度输出由原检查器和fresh只读Codex审计通过。仍physical_acceptance=false，非真实组成/观测拟合；气层以下沿原内部热结构。

档案：`experiments/external-tp-bridge-20261106/README.md`，只读 `verify_archive.py` 不跑模型；内含原/转换后TP、39项实际编译源/表格和ELF、冻结合同、原始输出、审核与图。代码分析网站已找到并读过相关内容：https://magrathea-code-lab.rainymink8.chatgpt.site/phase-atlas/gas/index.html；它的旧源码快照早于现有外部TP接口，当前源码优先。

项目DeepSeek66/88，本轮后续4次；新真实前向2次另计，旧14次拟合合同关闭、未借余额。未改物理源/EOS、原portable.py或旧实验；全部新文件D盘。下一项重大决定是正式H/He EOS/组成/参考压力及TP元数据，等待用户检视后再定，不自动grid/反演或重放。下文“下一段Pa适配/第一次接真solver”均已完成，勿重复花API/跑数。

## 第一段完成状态（2026-11-06，优先于下文原始任务描述）

第一段已实现并经独立完整代码门通过：`workflow/single_case.py`，24项固定测试＋1项API传输测试通过。正式档案 `experiments/main-smoke-20261106/` 已实际演示mock成功、坏组成、adapter失败及拒绝覆盖；36个档案文件同时核对了工作树与Git blob哈希。源码/配置/TP字节按本段局部gitattributes保留。未调用真实solver/grid/拟合或改EOS，physical_acceptance始终false。

DeepSeek负责全部产品代码；Codex负责合同/测试/诊断/独立验收/归档。当前API兼容入口 `workflow/deepseek_nonthinking.py` 复用原portable.Runner，不重写工作流。项目DeepSeek总账62/88，本轮12次，含两次协议失败与返修；历史科学拟合仍14次，新增0。

用户示范 `pt_profile.txt` 已只读检查并原样保存在 `D:/Codex/downloads/toi732c-inputs/20261106/`：400点，Pa/K空白文本，P=1–1e9Pa；不是已批准的生产TP，原始内容未上传。下一段只建议显式Pa→bar/CSV适配＋原始/转换后身份＋同一mock闭环。先等用户检视本段成果，不自动扩大到真实solver。上传目标为用户指定 `yt2523/Magrathea` 的master；固定开发仓库仍为本仓库main。源代码/档案验证提交为2852e26，其后仅交接与预算next_action文档更新；发布完成以远端SHA核对记录为准。

下文“当前任务/第一段”保留为原始规格，勿据此重复编码、重跑封存实验或再花API做已完成工作。实际结果和审核界限见档案README与evidence，下一步是用户检视。

## 当前任务

同学尚未交付TP及完整输入。我们先用明确标注的测试输入，逐段实现主程序：小架构→最小闭环→真实solver单例→真实数据→小批次→grid/拟合。当前只实施第一段，完成后让用户检视，再增加复杂度。

工作仓库：D:/Codex/downloads/subneptune-research-workflow，现有main分支。先核对Git状态和是否有其他会话写入；保护已有改动。所有新增文件、日志、临时目录放D盘，不重新安装/认证，不打印密钥。

## 第一段的最小架构和验收

先查看现有入口，说明哪些复用，再用DeepSeek实现；不要从零重写求解器/TP解析器，也不要只回计划。

五个职责：输入配置与校验、可替换solver适配接口、单案例控制、独立结果校验、输出/身份记录。先用假solver验证流程，未来换真实adapter时保持下游不变。不预建复杂平台。

验收：
- SYNTHETIC_FIXTURE输入→校验→MOCK_SOLVER→检查→全新输出目录，完整跑通。
- 组成不守恒、输入单位不符、缺少必要TP等错误被拒绝；adapter失败记录原因。
- 保留配置/TP身份及检查结果，拒绝覆盖旧输出；换测试输入无需改控制器。
- 状态明确为工程烟测；假输出不能通过真实物理验收，不能叫观测拟合成功。

本段不调用真实行星solver，不做grid、反演或主图，不改物理EOS。后续接真实solver时另写有界工程运行合同；不重启旧封存实验。首段独立验收、实际演示、存档后，报告下一段最小变更。

## 已确认的研究与分工

TOI-732 c，Bonfanti2024基准M=8.04(+0.50/-0.48)ME、R=2.39(+0.10/-0.11)RE。第一版铁核+硅酸盐+独立H2O层+H/He，比较严格无水，不考虑水气混合。真实EOS、TP、P0/T0仍待核验，测试参数不得变成生产默认值。

同学AI：输入数据与来源、TP设计/生成原理。我们：主代码、运行、grid/拟合。实际TP生成待认领，不要重复做。

Codex负责决策、规格、诊断及独立验收；DeepSeek主要编码和返修。遵守AGENTS.md的角色与局部接管规则。正常已授权调用无需逐次询问；项目总上限88，以workflow/project-budget.json和实际账本为准。旧44/44是已关闭阶段，不是当前全项目上限；portable每run默认24个logical launches不是项目总账。新调用要持久化计数。

## 可复用成果和不能重跑的历史

现有mode0可选TP接口、T-lnP插值、共同有效温度、高精度诊断和独立检查器已存在；先查tests/check_tp_model.py及相关测试。固定mu2只是工程fixture。gas_default在100bar同时改变热结构和分子量，不能移动切换点冒充纯热实验。

历史54/8/67批次及新TP14次拟合已封存。原方向8次整体失败，反向6次仅局部工程通过；不重跑，也不使用旧20次合同剩余额度。不要触碰原D:/GPT/projects/Sub-Neptune/Magrathea的脏改动/旧二进制。

## 按需定位，不要一次加载

- 开工规则：AGENTS.md及它要求的当前状态/短规则；预算workflow/project-budget.json。
- 真正涉及TP适配时：docs/TP_INTERFACE_SPEC.md、tests/check_tp_model.py和实际相关入口。
- 涉及科学方案时：docs/superpowers/plans/2026-11-03-toi732c-grand-grid-research.md。
- 同学交付后才需Zotero：year4project/group6595176，计划5M2AJHDU，交接VCDGPDSU。

不要初始读取完整总报告、整套历史输出、私有模型响应或全部技能。每次只传DeepSeek当前需要的代码片段与验收；不用按数值案例开agent。每个通过的里程碑继续main存档并核对远端；不覆盖旧结果。
