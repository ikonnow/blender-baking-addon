# BakeTool 开发者指南

本文档面向维护者、贡献者和需要把 BakeTool 接入外部流程的开发者。它描述当前版本的结构边界、执行链、关键约束、扩展方式以及本轮发布前收尾后形成的稳定规范。请把它理解成“当前版本如何被正确维护”的说明，而不是一篇泛泛而谈的 Blender 插件教程。

## 1. 设计目标

BakeTool 的工程目标有三条：

1. 把 Blender 原生烘焙流程中重复而脆弱的步骤收敛成可复用的执行链。
2. 保持 UI、operator、核心引擎和自动化验证之间有清晰边界。
3. 在 Blender 3.3 到 5.x 范围内维持可测试、可发布、可解释的行为。

这意味着代码里的很多“看起来绕一点”的保护逻辑并不是多余的，它们通常对应 Blender 上下文、版本差异、导出副作用、图像颜色空间或测试可复现性问题。

## 2. 仓库结构与职责划分

```text
baketool/
  automation/       本地 CLI 测试入口、跨版本验证、headless 入口
  core/             执行引擎、图像/节点/UV/兼容层等核心模块
  dev_tools/        开发辅助工具
  docs/             用户文档、开发文档、路线图、检查清单
  test_cases/       unittest 套件与测试帮助函数
  __init__.py       注册入口、bl_info、偏好设置与模块加载
  constants.py      参数、UI 布局和映射元数据
  ops.py            面向 UI 的 operator
  property.py       PropertyGroup、枚举、Job/Setting 结构
  preset_handler.py 预设序列化、迁移与自动加载
  state_manager.py  崩溃恢复状态管理
  ui.py             主面板、结果面板、节点烘焙面板
```

### 2.1 `ui.py`

只负责绘制界面、读取上下文和把用户操作委托给 operator。UI 不应直接承载复杂业务逻辑。对维护者来说，一个重要判断标准是：如果某段逻辑无法在 headless 或测试环境中复用，那么它大概率不应该塞进 UI 绘制代码里。

### 2.2 `ops.py`

operator 层是 UI 与核心执行之间的桥。它可以做：

- 基础上下文检查
- 将 UI 状态整理成调用参数
- 调用 `core/engine.py` 或其他核心模块
- 反馈结果到 UI

它不应承担难以测试的复杂状态机。当前版本已经补齐缺失 operator，并通过测试保证 UI 引用与注册状态一致。

### 2.3 `property.py`

定义 Job、Setting、自定义图、节点烘焙设置等 Blender RNA 属性。这个模块的稳定性很重要，因为它直接关系到：

- 界面显示
- 预设序列化
- 默认值和范围
- 引擎读取参数

如果你修改属性名或结构，必须同步考虑：

- `constants.py` 映射
- `preset_handler.py` 迁移逻辑
- 测试
- 文档

### 2.4 `constants.py`

这里不是“便于复制粘贴的常量池”，而是 BakeTool 的参数元数据中心。很多 UI 配置、通道信息和映射关系都依赖这个模块。维护时应优先把规则放到这里，而不是在 UI 和引擎两边各写一份。

### 2.5 `core/`

这是 BakeTool 的执行核心。原则上，越靠近 `core/` 的逻辑越应具备以下特征：

- 可测试
- 尽量少依赖 UI
- 有明确输入输出
- 对 Blender 版本差异有集中处理

## 3. 执行链总览

BakeTool 的典型执行过程可以概括为：

1. UI 或脚本选择 Job。
2. operator/API/headless 入口收集上下文。
3. `JobPreparer` 校验 Job 并构建执行队列。
4. `BakeStepRunner` 逐步执行队列。
5. `BakePassExecutor` 为每个通道准备图像、节点上下文和 bake 参数。
6. 如有需要，执行自定义图组装、通道打包、后处理和导出。
7. `state_manager.py` 在过程中记录状态，便于异常恢复。

这条链路的关键点在于：BakeTool 不是直接“点一下按钮就调用 Blender bake”，而是把输入验证、资源准备、状态保护和输出整理都放进了执行链里。也正因为如此，很多修复都必须落到 `core/engine.py` 而不是 UI 层。

## 4. 核心组件

### 4.1 `JobPreparer`

主要负责：

- 校验 Job 是否可执行
- 解析对象和模式
- 生成执行队列
- 为 quick bake 或 API 使用准备简化队列

它的职责是“决定要做什么”，不是“真正去做”。如果一个问题出现在错误对象进入队列、空队列、模式解释不正确等阶段，优先检查这里。

### 4.2 `BakeStepRunner`

它是队列执行控制器，主要负责：

- 逐步骤执行
- 管理执行过程中的上下文
- 调用 `BakePassExecutor`
- 收集本步骤结果
- 触发自定义图、通道打包和导出等后续动作

本轮修复中，自定义图结果键统一和打包支持就落在这条路径上。

### 4.3 `BakePassExecutor`

这是单通道执行的关键组件。主要职责包括：

- 创建或获取目标图像
- 确认 bake 类型和通道策略
- 处理 Blender bake 参数
- 调用原生 `bpy.ops.object.bake`
- 对自定义图执行 NumPy 组装路径
- 返回当前通道生成的图像结果

本轮修复后的几个关键规则：

- 自定义图优先走 `_try_custom_channel`，不再退回默认黑图
- 自定义图结果键使用 `BT_CUSTOM_<name>`
- 打包源通过 `normalize_source_id()` 统一处理
- pass filter 通过 `_get_pass_filter_settings()` 映射到 Blender bake 设置

### 4.4 `ModelExporter`

负责烘焙后导出对象和贴图。这个模块必须特别注意“副作用管理”。当前版本已经明确：

- 导出前会记录对象选择和可见性状态
- 导出后恢复 `hide_set()` 和 `hide_viewport`
- 不能把导出过程留下的场景污染视为可接受代价

任何新的导出相关改动，都应首先问自己一句：它会不会把场景状态改坏。

## 5. 关键数据约定

### 5.1 自定义结果键

自定义通道统一使用：

```text
BT_CUSTOM_<name>
```

这不是随便取的命名，而是执行结果、通道打包、测试和文档共同依赖的协议。若修改这一规范，必须同步改动：

- `BakePassExecutor.get_result_key()`
- `BakePassExecutor.normalize_source_id()`
- 打包逻辑
- 测试用例
- 用户文档

### 5.2 颜色空间映射

属性层使用枚举值，Blender 图像对象需要实际 colorspace 名称。当前版本通过 `core/image_manager.py` 将例如 `NONCOL`、`SRGB`、`LINEAR` 等值映射到 Blender 实际可识别名称。不要再把内部枚举直接写入 `image.colorspace_settings.name`。

### 5.3 状态记录

`state_manager.py` 会在系统临时目录写入：

```text
sbt_last_session.json
```

记录内容包括 Job 名称、当前步骤、当前对象、当前通道和最后错误。恢复机制依赖这个文件，因此若你调整字段命名或写入时机，也需要同步检查 UI 恢复入口和测试。

## 6. Headless、API 与 UI 的边界

### 6.1 UI 路径

适用于交互式 Blender 会话。优势是可视化和即时反馈，代价是更多依赖当前界面上下文。

### 6.2 Headless 路径

`automation/headless_bake.py` 现在会在干净会话中自动注册插件，然后从当前 `.blend` 中读取已保存的 Job 配置并执行。这一路径适用于：

- 后台批处理
- 管线自动化
- 无界面验证

限制也要写清楚：

- 它不会自动创建 Job
- 它不是通用批量调度系统
- 它依赖当前场景文件已有 BakeTool 数据

### 6.3 API 路径

`core/api.py` 暴露了最基础的对外接口：

- `bake(objects, use_selection=True)`
- `get_udim_tiles(objects)`
- `validate_settings(job)`

API 适合外部脚本或其他插件集成。如果某个功能只能通过 UI operator 访问，而无法通过 API 或核心模块调用，那通常说明结构还不够干净。

## 7. 测试策略

### 7.1 基础原则

- 先修 bug，再补回归测试
- 测试应尽量验证真实协议，而不是伪信号
- 涉及 Blender operator 注册的验证不能只用 `hasattr`
- 对跨版本行为要优先依赖自动化，而不是记忆

### 7.2 当前关键套件

- `suite_unit.py`：核心逻辑、协议和回归测试
- `suite_export.py`：导出安全与状态恢复
- `suite_ui_logic.py`：UI/属性联动
- `suite_verification.py`：综合验证
- `suite_production_workflow.py`：端到端工作流

### 7.3 本轮新增或强化的重点

- UI operator 完整性测试改为 `get_rna_type()`
- 自定义图执行与打包测试
- headless 初始化测试
- pass filter 映射测试
- `hide_viewport` 恢复测试

如果后续再出现“文档写得有，UI 也画出来了，但执行没接上”的问题，说明测试还不够贴近真实链路。

## 8. 修改代码时的工作方法

### 8.1 修改属性前

先检查：

- `property.py`
- `constants.py`
- `preset_handler.py`
- 对应 UI
- 对应测试
- 对应文档

### 8.2 修改执行链前

先明确变化落在哪一层：

- 输入验证
- 队列构建
- 单通道执行
- 打包/导出/后处理

不要用“临时补一个 if”把层级边界打乱。短期看似快，长期成本很高。

### 8.3 修改 UI 前

任何新增按钮或操作入口都至少应检查三件事：

1. 对应 operator 是否存在并注册。
2. 是否有最基本的测试覆盖。
3. 用户文档是否需要更新。

本轮缺失 operator 的问题已经说明，UI 引用和实际注册状态不一致是非常容易漏掉、但用户一上手就会踩到的错误。

## 9. 文档维护要求

BakeTool 当前已经重写了主说明文件，后续不应再回到“代码先变，文档长期欠债”的状态。建议强制执行以下规则：

- 新增用户可见功能时，同步更新 `README` 和用户手册
- 新增开发约束或接口变化时，同步更新开发文档
- 新增或删除自动化脚本时，同步更新自动化参考
- 每次发布前检查 changelog、路线图和任务看板

文档不是附属品，它直接决定后续维护成本和外部使用误差。

## 10. 后续重构建议

当前最值得做但不适合在 1.0 发布前推进的，是对 `core/engine.py` 的渐进式拆分。建议的拆分思路是：

- 保持外部接口稳定
- 先提炼纯函数和局部模块
- 先以测试保护现有行为，再做拆分
- 不用“为了更优雅”而一次性重写

同理，预设 schema、导出链和高级自定义图能力也应采取“先护栏、后扩展”的方式。

## 11. 结论

BakeTool 当前已经从“功能还在快速堆叠的试验脚本”转向“可以被持续维护的 Blender 插件项目”。对开发者而言，最重要的不是继续快速加代码，而是守住下面这组基本原则：

- UI、operator、核心引擎分层清晰
- 参数和命名协议统一
- 新行为必须有测试和文档
- 发布前靠自动化和清单，而不是凭印象

只要这四点保持住，BakeTool 后续的迭代就会越来越稳，而不是越做越难维护。
