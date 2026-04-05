# Simple Bake Tool (SBT) - 现阶段重构与改进计划 (Refactoring Roadmap)

## 1. 当前架构分析与存在的问题

经过对代码库的深入审查，Simple Bake Tool (SBT) 目前已经实现了良好的 **UI-Engine-Core** 三层解耦，并且在单元测试和跨版本兼容（Blender 3.6 - 5.0）方面打下了坚实的基础。然而，随着功能的不断增加，代码库中也积累了一些“技术债务”，主要体现在以下几个方面，这些问题如果不及早解决，将阻碍未来的扩展（如完整的 Headless 支持和更复杂的节点图分析）。

### 1.1 违背 KISS 原则与稳定性隐患：上下文劫持 (Context Hijacking)
*   **位置**: `core/image_manager.py` 中的 `robust_image_editor_context`。
*   **问题**: 为了调用 `bpy.ops.image.tile_add`（添加 UDIM Tile），代码强行修改了用户当前的 UI Area (`area.type = 'IMAGE_EDITOR'`)，甚至在找不到合适窗口时强行借用。这在无头模式 (Headless) 或者用户后台渲染时极易导致不可预知的崩溃或上下文丢失。
*   **重构目标**: 使用 Blender 的底层数据 API 直接操作，摒弃对 UI Operator 的依赖。

### 1.2 违背 DRY 原则：状态与上下文管理的割裂
*   **位置**: `core/engine.py` 中的 `BakeContextManager`，以及散落在各处的 `try...finally` 和原生的 `bpy.context.temp_override`。
*   **问题**: `BakeContextManager` 使用了一个手动的 `self.stack` 列表来管理不同层级的设置（scene, cycles, image）。这不够 Pythonic，且在多层嵌套和异常抛出时容易导致状态恢复不完全。
*   **重构目标**: 引入 Python 标准库 `contextlib.ExitStack`，建立统一、原子的上下文恢复栈。

### 1.3 违背解耦原则：UI 层的逻辑渗透与硬编码
*   **位置**: `ui.py` 中的 `draw_active_channel_properties` 和相关的 `SPECIAL_CHANNEL_DRAWERS`。
*   **问题**: 虽然使用了字典分发，但字典中直接绑定了特定通道的绘制函数（如 `_draw_normal`, `_draw_combine`），并且 UI 代码中依然存在如 `if channel.id == 'rough':` 这样的业务逻辑硬编码。这意味着如果我要添加一个需要特定 UI 的新通道，我必须修改 `ui.py`。
*   **重构目标**: 将所有关于“如何绘制”的元数据（Metadata）完全迁移到 `constants.py` 的 `CHANNEL_UI_LAYOUT` 中，使 `ui.py` 成为真正的“哑视图”（Dumb View）。

### 1.4 魔法字符串与常量未收敛 (Magic Strings)
*   **位置**: `core/math_utils.py`, `core/common.py` 等。
*   **问题**: 代码中散落着诸如 `"BT_ATTR_ELEMENT"`, `"BT_Protection_Dummy"`, `"Baked_Results"` 等硬编码的字符串。这不仅容易拼写错误，也让后期的集中管理（比如改名、清理）变得困难。
*   **重构目标**: 在 `constants.py` 中建立全局常量字典。

---

## 2. 详细执行计划 (Task Breakdown)

我们将重构划分为三个连续的 Sprint，每个 Sprint 结束后必须保证现有的 110+ 测试用例全部通过，保证业务逻辑的“零退化”。

### 🔴 Sprint 1: 消除技术债务与危险逻辑 (High Priority)

**目标：** 解决可能导致崩溃的核心风险点，尤其是对上下文的劫持。

*   **Task 1.1: 移除 `image_manager.py` 中的上下文劫持**
    *   **位置**: `core/image_manager.py`
    *   **行动**: 移除 `robust_image_editor_context` 及其相关调用。
    *   **替换方案**: 在处理 UDIM Tile 添加时，直接使用底层的 `image.tiles.new(tile_number=t_idx)`。对于需要填充颜色的需求，直接生成指定大小的 numpy 数组并使用 `tile.pixels.foreach_set()` 进行像素级写入，彻底避开 `bpy.ops.image.tile_add`。

*   **Task 1.2: 重构 `BakeContextManager` (使用 ExitStack)**
    *   **位置**: `core/engine.py` -> `BakeContextManager`
    *   **行动**: 引入 `contextlib.ExitStack`。将各种临时设置（分辨率、引擎、图像格式）打包为独立的上下文管理器对象，通过 `ExitStack.enter_context()` 统一管理。这能保证即使在深层逻辑中触发了系统级中断，环境依然能 100% 恢复。

### 🟡 Sprint 2: 架构纯化与常量收敛 (Medium Priority)

**目标：** 将 UI 层与业务逻辑彻底物理隔离，收敛所有魔法字符串，实现 DRY。

*   **Task 2.1: 提取全局系统常量**
    *   **位置**: `constants.py`, `core/cleanup.py`, `core/common.py`, `core/math_utils.py`, `core/node_manager.py`
    *   **行动**: 在 `constants.py` 中新增一个 `SYSTEM_NAMES` 字典，例如：
        ```python
        SYSTEM_NAMES = {
            'TEMP_UV': "BT_Bake_Temp_UV",
            'DUMMY_IMG': "BT_Protection_Dummy",
            'RESULT_COLLECTION': "Baked_Results",
            'ATTR_PREFIX': "BT_ATTR_"
        }
        ```
        全局替换所有相关文件中的硬编码字符串。

*   **Task 2.2: 数据驱动 UI (完全移除 UI 中的条件判断)**
    *   **位置**: `ui.py`, `constants.py`
    *   **行动**: 修改 `CHANNEL_UI_LAYOUT`，将所有需要特殊绘制的属性（如 Roughness 的反转开关、Normal 的 XYZ 轴向选择）抽象为布局指令。重写 `ui.py` 的 `draw_active_channel_properties`，使其仅通过解析 `CHANNEL_UI_LAYOUT` 字典来渲染输入框，移除所有 `if channel.id == '...'`。

### 🟢 Sprint 3: 弹性和崩溃恢复增强 (Robustness)

**目标：** 确保在复杂生产环境下，插件具备自动排错和更健壮的清理能力。

*   **Task 3.1: 改进 `NodeGraphHandler` 的清理机制**
    *   **位置**: `core/node_manager.py`
    *   **行动**: 目前是通过 `name` 和 `label` 匹配保护节点进行清理。这不够安全（用户可能恰好有同名节点）。重构为：在注入临时节点时，将其引用（或内部名称 UUID）存储在插件的运行时内存中。在 `cleanup()` 时，精确制导销毁，绝不误伤用户原有的节点。

*   **Task 3.2: 增强的日志与状态恢复**
    *   **位置**: `state_manager.py`, `ops.py`
    *   **行动**: 当前仅记录了最后崩溃的物体。增强 `BakeStateManager`，使其记录整个 `bake_queue` 的简要状态。如果发生崩溃，下次启动时不仅仅是提示，还可以在 UI 上提供一个 **"Resume Interrupted Bake" (恢复中断的烘焙)** 按钮。

---

## 3. 验收标准 (Definition of Done)

对于每一个 Sprint 和 Task，其验收标准必须包含：
1. **代码审查通过**：改动完全符合 DRY 和 KISS 原则，无硬编码。
2. **本地测试绿灯**：执行 `automation/multi_version_test.py`（跨越 Blender 3.6, 4.2, 5.0），必须 100% PASS，无报错。
3. **手动回归测试**：
   - 包含 UDIM 模型的烘焙不应产生报错（验证 Task 1.1）。
   - 用户界面的通道设置切换流畅且布局正确（验证 Task 2.2）。
   - 使用 `Ctrl+C` 强行打断终端后，Blender 场景不会出现 `BT_` 开头的残留物（验证 Task 3.1 和 1.2）。

---
**本计划将作为下一步代码实现的蓝图。请审阅此方案。若您同意，我们将严格按照 Task 的顺序执行编码。**