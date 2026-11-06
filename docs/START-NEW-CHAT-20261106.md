请接手TOI-732 c主程序开发。先只读以下交接文件，并按其中要求最少量读取开工规则：
D:/Codex/downloads/subneptune-research-workflow/docs/HANDOFF-LITE-20261106.md

这是全新空白聊天，不读取旧聊天历史，不创建或分叉其他聊天，不一开始加载完整研究报告/历史实验。

固定工作仓库D:/Codex/downloads/subneptune-research-workflow，所有新文件放D盘。先核对Git状态，保护现有改动。

同学的TP/完整参数尚未交付；先复用现有代码，用标明SYNTHETIC_FIXTURE的输入和MOCK_SOLVER，逐段实现。你先简述最小架构及复用点，随后让DeepSeek实现第一段：配置校验→可替换solver接口→单案例执行→独立检查→新目录存档。Codex负责决策和独立验收。

本轮只做这个离线工程闭环，不调用真实行星solver，不跑grid/拟合，不改物理EOS，不重跑历史实验。跑通并独立验收、演示和存档后，给我看第一段成果及下一段最小改动，再逐步增加复杂度。
