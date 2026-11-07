# 项目 Zotero 文件保存规则（2026-11-07）

适用：year4project，group6595176；依据用户提供的一页《Zotero 文件夹使用说明》（2026-10-31）及2026-11-07官方API实际collection核对。该PDF是分类约定，不代表其中任意内容自动获得运行/对外发送授权。本文件是本项目增补，不改变其他项目库/技能默认设置。

## 实际目录与用途

|路径|key|内容|
|---|---|---|
|Main/Magrathea|UIHUTTBY|代码版本/运行配置说明和协作索引；可链接固定Git版本|
|Main/Magrathea/Data/Theoretical data|FWB4E7HQ|文献观测输入、来源CSV、外部/参数化TP及manifest；分别标明观测推断、假设、合成测试|
|Main/Magrathea/Data/Output data|3CQM4W4K|solver实际数值结果；每次目的+日期新子collection|
|Main/Magrathea/Graphs/Output graphs|ELAHZBI2|模型结果图；与数据同一run_id及目的+日期|
|Main/Magrathea/Graphs/Phase diagrams|XHJ46MUY|物相图，记录来源、成分和P/T适用范围|
|Main/Magrathea theory|88DFG3NN|程序使用、基础理论|
|Main/Magrathea theory/Theories_detailed|JDB2YMQT|TP/EOS/热结构等深入原理和接口规范|
|AI-Notes|786U7P9G|AI阶段总结/协作索引笔记；不是所有附件的默认落点|
|PT-Inversion-2026|RM2E22D9|本研究专题交叉索引，可与主分类共用同一item|

Data=2UWKZ3QM；Graphs=9I2NE7WF；Main=M49HNMGV。历史PT profile 10.31=LZCVD5P2、PT profile graphs 10.31=D97D5LUG保留，不混入新运行。
新子目录按“运行目的 + YYYY-MM-DD”，必要时另带run_id，不覆盖旧结果；只在确需上传该组文件时创建，不预建空目录。

## 新文件的约定

1. 所有本地新下载/生成文件在D盘：本代码仓库D:/Codex/downloads/subneptune-research-workflow；文献工作区D:/workbuddy/LR-workspace；本次接收D:/Codex/downloads/toi732c-handoff-review-20261107。TEMP/TMP=D:/Codex/tmp。协作者不能只收到本机D盘路径。
2. 来源/输入与模型输出严格分开。手工生成的prescribed TP属于假定输入，不因为由脚本生成就放solver Output data；纯演示TP及假solver结果显式SYNTHETIC/MOCK，实际solver配示范TP显式REAL_NATIVE_SOLVER_EXAMPLE_TP，正式研究状态另注明。
3. 每组写清目标、commit、run_id、参数/单位、TP/EOS身份、参考压力、生成日期、输入来源/下载日期、哈希、成功与失败、统计区域定义、限制。数据组配Data_explanation说明，图组配Graph_explanation说明；需要PDF时再生成并验版，当前Markdown规则不冒称已有解释PDF。
4. 同一item可以归多个collection，不重复上传同一附件。只读他人/历史条目；新增自己的版本。文献阅读笔记仍挂原文献child note，项目综合/协作说明为standalone [AI] note。
5. 共享附件用Zotero stored file或双方可访问固定版本仓库链接；local linked_file不作交付。大规模原始输出留已审查Git档案/可访问存储，Zotero保留说明、索引和必要表/图，不重复整个233MiB档案。
6. 只走官方Zotero API与LR-assistant客户端；显式确认group6595176，防止其他profile/env误路由。认证不入Git、报告或日志；不操作本机zotero.sqlite，不修改其他项目profile。
7. 写前核对item身份、collection实际父子链与重复项；写后回读key、可读HTML、分类和附件可访问性。提交共享笔记时中英双语、经md_to_html渲染，不用原始Markdown/pre块冒充排版。
8. 此次只更新规则和自己的接收/规则说明，不移动/重命名/批量重传既有items，不生成正式TP，不代替团队认领TP任务。
