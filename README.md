# BakeTool

BakeTool 是一个面向 Blender 的快速贴图烘焙插件。

> [!CAUTION]
> **严正申明与风险公示 (Project Disclaimer)**
>
> 1. **开发背景**：本项目目前由 **lastraindrop** 一人利用业余时间维护。代码逻辑大量依赖 **vibecode (AI 辅助开发)** 完成。虽然通过了 150+ 自动化测试，但 AI 生成的逻辑在极端边缘场景或复杂生产环境下可能存在不可预知的行为。
> 2. **稳定性状态**：BakeTool 尚处于**早期验证阶段 (Experimental Prototype)**。虽然它在“实验室环境”下表现良好，但严重缺乏大规模、多类型的用户实战验证。
> 3. **核心警告**：**极有可能出现“测试全过，实战报错”的情况**。它目前还远远达不到工业级的稳定性。
> 4. **使用建议**：**在将其应用于正式生产资产前，请务必对 .blend 场景进行手工备份。** 开发者不承担因插件故障导致的任何数据丢失责任。

## 当前定位

- 面向 Blender 3.3 到 5.x 的贴图烘焙原型工具
- 适用于单对象、Selected-to-Active、UDIM 等基础流程验证
- 支持基于 vibecode 工作流的快速迭代修复

## 核心能力

- 非破坏式流程：尽量自动创建和清理临时图像、节点和上下文状态
- 批量作业：同一场景可维护多个 Bake Job，逐个启停、保存和复用
- 多种目标模式：单对象、合并对象、Selected-to-Active、拆材质、UDIM
- 通道控制：常见 PBR、光照、辅助图和自定义贴图可混合使用
- 通道打包：支持将多个烘焙结果合并到一个 RGBA 贴图
- 自定义贴图：支持按通道来源组装灰度或 RGBA 结果，并可继续参与打包
- 节点烘焙：在节点编辑器中直接对当前激活节点输出烘焙
- 导出联动：可在烘焙后配合 FBX、GLB、USD 导出资产
- 崩溃恢复：使用 `state_manager.py` 记录上一次未完成任务的状态
- 自动化验证：内置 CLI 套件、跨版本矩阵验证和 headless 入口

## 版本与兼容性

- 插件版本：`1.0.0`
- Manifest：`blender_manifest.toml`
- 最低 Blender 版本：`3.3.0`
- 当前验证覆盖：`3.3.21`、`3.6.23`、`4.2.14 LTS`、`4.5.3 LTS`、`5.0.1`

兼容策略并不是简单靠条件分支堆出来的。BakeTool 将 Blender 版本相关差异集中在 `core/compat.py` 和少量调用层，并依赖自动化测试持续验证关键路径。正式发布前，建议至少在一个 LTS 版本和一个新版本上各跑一轮验证。

## 安装

### 从发布包安装

1. 下载发布 ZIP。
2. 在 Blender 中打开 `Edit > Preferences > Add-ons`。
3. 点击 `Install...`，选择 ZIP。
4. 启用 `BakeTool`。

### 从源码目录安装

1. 将仓库目录放入 Blender 的 add-ons 目录，或者将其作为开发目录加载。
2. 确保目录名为 `baketool`，或者保持包导入路径能被 Blender 正常解析。
3. 启用插件后，在 `3D View > N Panel > Baking` 中访问主界面。

## 快速开始

1. 打开 `3D View`，在 `N Panel` 找到 `Baking` 面板。
2. 创建一个新的 Job。
3. 在 `SETUP & TARGETS` 中指定对象、模式、分辨率和基础目标。
4. 在 `BAKE CHANNELS` 中勾选需要的通道。
5. 在 `OUTPUT & EXPORT` 中设置保存路径、图像格式、导出联动、打包和动画参数。
6. 如需从已有贴图拼装额外结果，在 `CUSTOM MAPS` 中添加自定义通道。
7. 点击 `START BAKE PIPELINE`。
8. 在结果面板或图像编辑器中检查输出。

如果只是想快速生成最常见的 PBR 基础贴图，可以先使用 `One-Click PBR`。当前实现会直接启用 `Base Color`、`Roughness` 和 `Normal` 三个通道；金属度、AO 等其他通道仍然需要按具体项目需求手动启用。

## 典型工作流

### 单对象贴图烘焙

适合低模对象已有目标材质、希望直接生成基础贴图的场景。常见步骤是新建 Job、指定目标对象、选择 `SINGLE_OBJECT`、设置分辨率与保存路径、勾选颜色/粗糙度/法线后直接执行。

### Selected-to-Active

适合高模到低模烘焙。将高模和低模对象准备好后，在 Job 中选择 `SELECT_ACTIVE`，确保激活对象是低模目标，并根据需要设置 cage、extrusion 和 margin。BakeTool 会通过执行队列把对象上下文整理到可烘焙状态，再调用 Blender 原生 bake。

### 拆材质与 UDIM

对多材质物体可以使用 `SPLIT_MATERIAL`，对基于 UDIM 的资产可以使用 `UDIM` 模式并结合 `udim_mode` 进行检测、重排或自定义处理。UI 中也提供了刷新 UDIM 位置的 operator，用于在对象集变化后同步 tile 信息。

### 自定义贴图与通道打包

BakeTool 的自定义贴图并不是简单复制一张图，而是可以从既有结果中选取单通道或整张颜色信息，生成新的灰度或 RGBA 图，再继续参与通道打包。最新修复已经把自定义通道真正接入执行链，并统一使用 `BT_CUSTOM_<name>` 作为结果键，保证打包时可以稳定识别这些输出。

### 节点烘焙

在节点编辑器中，激活一个可烘焙节点后，可以使用节点面板执行 Selected Node Bake。当前版本已经补齐 UI 所需 operator，界面按钮与注册逻辑一致，不会再出现按钮存在但 operator 未注册的情况。

## 自动化与验证

### 统一 CLI 测试入口

```bash
blender -b --factory-startup --python automation/cli_runner.py -- --suite unit
blender -b --factory-startup --python automation/cli_runner.py -- --suite verification
blender -b --factory-startup --python automation/cli_runner.py -- --category integration
```

### 跨版本验证

```bash
python automation/multi_version_test.py --verification
python automation/multi_version_test.py --suite unit
python automation/multi_version_test.py --list
```

### Headless 烘焙

```bash
blender -b scene.blend -P automation/headless_bake.py -- --job "JobName"
blender -b scene.blend -P automation/headless_bake.py -- --output "C:/baked"
```

注意两点：

- `headless_bake.py` 现在会在干净会话里自动注册插件，不再要求你先手工初始化属性。
- 它不会替你凭空创建 Job，必须基于当前 `.blend` 文件中已保存的 BakeTool 作业配置运行。

## 文档导航

- [用户手册](docs/USER_MANUAL.md)：面向实际使用者的完整操作说明
- [开发者指南](docs/dev/DEVELOPER_GUIDE.md)：架构、执行链、扩展点和开发约束
- [自动化参考](docs/dev/AUTOMATION_REFERENCE.md)：测试入口、命令行参数和验证建议
- [生态说明](docs/dev/ECOSYSTEM_GUIDE.md)：仓库结构、工具链关系和交付边界
- [标准化指南](docs/dev/STANDARDIZATION_GUIDE.md)：编码、接口、命名和发布规范
- [路线图](docs/ROADMAP.md)：当前版本定位与后续演进方向
- [任务看板](docs/task.md)：发布前后任务状态汇总
- [发布检查清单](docs/RELEASE_CHECKLIST.md)：打包、验证和文档同步的最终检查项
- [更新日志](CHANGELOG.md)：版本变更记录

## 仓库结构概览

```text
baketool/
  automation/       自动化入口、跨版本验证、headless CLI
  core/             执行引擎、图像管理、节点处理、兼容封装
  dev_tools/        开发辅助脚本
  docs/             用户文档、开发文档、路线图与清单
  test_cases/       unittest 套件与辅助工具
  __init__.py       插件注册入口与 `bl_info`
  ops.py            操作符
  property.py       PropertyGroup 与枚举/设置定义
  ui.py             面板与界面布局
  constants.py      常量、配置映射和 UI/参数元数据
  preset_handler.py 预设序列化与自动加载
  state_manager.py  任务状态与崩溃恢复
```

## 当前发布候选状态

最近一轮收尾工作已经完成以下内容：

- 清理了 `__pycache__`、旧报告、发布产物、崩溃日志和其他运行期残留
- 重写了核心用户文档与开发文档，去除了乱码和失效引用
- 更新了 `bl_info` 链接和发布元数据
- 补充了 `CHANGELOG.md`、发布检查清单、路线图与任务看板
- 修复了 View Layer 预检、失败通道图像清理和调试测试隔离执行等收尾阻断问题
- 通过了本地关键套件验证，以及 `negative` / `verification` 的跨版本验证

剩余工作主要集中在最终安装烟测、发布说明和对外发布动作，而不是大规模功能修复。

## 许可

本项目随仓库中的 `LICENSE` 一起分发。发布或集成到外部流程前，请先阅读许可条款并确认与所在团队的交付要求一致。
