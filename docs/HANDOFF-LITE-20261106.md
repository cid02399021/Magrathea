# TOI-732 c：空白聊天轻量交接

更新：2026-11-06。本文件独立可读，不依赖旧聊天。用户自己新建空白窗口；不要创建/分叉聊天，也不要自动读取旧聊天历史。

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
