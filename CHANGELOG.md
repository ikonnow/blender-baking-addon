# 更新日志

本文件记录 BakeTool 在正式发布前的主要版本变化。这里不追求逐提交流水账，而是保留对用户、开发者和验证流程有实际意义的版本信息。

## 1.0.0 - 2026-04-21

这是发布前的关键收尾版本，重点是修复会直接影响发布质量和自动化可信度的缺陷。

### 修复

- 补齐了 UI 已经引用但未注册的三个 operator：
  - `bake.set_save_local`
  - `bake.selected_node_bake`
  - `bake.refresh_udim_locations`
- 修复了 `automation/headless_bake.py` 在干净 Blender 背景会话中不能初始化插件属性的问题，脚本现在会先尝试注册 BakeTool，再访问 `scene.BakeJobs`。
- 将自定义通道真正接入执行管线，不再在执行阶段退回默认黑色结果。
- 统一了自定义通道结果键命名，执行结果和通道打包统一使用 `BT_CUSTOM_<name>`，消除了自定义图可烘焙但不可打包的问题。
- 将 diffuse、glossy、transmission 和 combined 的 pass filter 选项实际映射到 Blender bake 设置，不再是“界面可改但执行不生效”的状态。
- 修复导出流程只恢复 `hide_set()` 不恢复 `hide_viewport` 的问题，避免导出后对象可见性被污染。
- 增加颜色空间枚举与 Blender 实际 colorspace 名称的映射，避免 `NONCOL`、`LINEAR` 等内部值直接写入 RNA 导致的异常。

### 自动化

- 重写 UI operator 完整性测试，改用 `get_rna_type()` 验证注册状态，避免 `hasattr(bpy.ops...)` 带来的假阳性。
- 新增和补强以下回归测试：
  - headless 初始化测试
  - 自定义通道结果键规范测试
  - 自定义通道 NumPy 组装测试
  - 自定义结果参与通道打包测试
  - pass filter 映射测试
  - 导出可见性恢复测试
- 在 Blender 4.5.3 LTS 上通过了 `unit`、`export`、`ui_logic`、`verification` 和 `production_workflow` 关键套件。
- 通过了 `3.3.21`、`3.6.23`、`4.2.14 LTS`、`4.5.3 LTS`、`5.0.1` 的跨版本 verification 验证。

### 文档与发布准备

- 更新 `__init__.py` 中的 `doc_url` 和 `tracker_url`，替换占位链接。
- 重写 `README.md`、用户手册、开发者文档和自动化说明，移除乱码与旧脚本引用。
- 增加发布检查清单，统一正式打包前需要执行的验证和人工验收动作。
- 修正 `MANIFEST.in`，使其与当前仓库布局一致。

## 1.0.0-pre - 2026-04-17

这是 1.0 线的稳定化节点，主要目标是让插件在 Blender 3.3 到 5.x 范围内具备可持续验证和维护的基本条件。

### 变化

- 稳定化核心执行链与异常处理。
- 收敛 UI、属性和引擎参数映射。
- 清理部分未使用导入和维护性问题。
- 完成多份基础文档与测试脚本的初版整理。

## 0.9.5 - 2024-01-20

### 变化

- 增加 GLB/USD 导出联动支持。
- 增加降噪后处理相关流程。
- 持续调整执行引擎与资源清理逻辑。

## 0.9.0 - 2023-09-01

### 变化

- 将烘焙执行逻辑重构为更清晰的模块化核心组件。
- 引入更明确的 UI、operator、engine 分层。
- 开始形成自动化套件与开发规范。
