# Simple Bake Tool 开发者指引 (Developer Guide)

本文件旨在为 Simple Bake Tool 的后续开发提供架构说明、技术规范及已知问题的记录。

## 1. Architecture (v0.9.0)

The project follows a strict **UI-Engine-Core** three-layer decoupling principle:

1.  **UI/Operator Layer** (`ops.py`, `ui.py`): 
    *   **Data-Driven UI** (**v0.9.0**): 通道属性绘制完全由 `constants.py` 中的 `CHANNEL_UI_LAYOUT` 配置驱动，实现了真正的 100% 哑视图 (Dumb View)。
    *   **UI Hardening (v1.0.0)**: 引入 `draw_env_status` 环境健康监测逻辑，主动拦截导出插件缺失、路径无效等环境配置错误。
    *   **UI Dispatch Pattern**: 针对特殊通道的绘制（如 Normal, Combine），使用 `CHANNEL_UI_LAYOUT` 字典进行逻辑分发。
    *   **Smart Object List (v1.0.0)**: 列表控件具备动态诊断能力，可实时显示 Missing UV 等关键错误图标。
    *   **Thin Operators**: Operator 仅作为入口，具体的数据操作已迁移至 Core 层。新增 `Resume Interrupted Bake` 机制。
2.  **Engine Layer** (`core/engine.py`): The orchestrator.
    *   `JobPreparer`: 验证输入并准备执行队列。支持 Proxy 模式用于 Quick Bake。
    *   `BakePassExecutor` (**v0.9.0**): 彻底拆分巨型逻辑。采用流水线策略（Pipe-lining），将图像创建、Numpy 处理、Blender 原生调用与参数组装隔离为私有原子方法，极大地降低了核心路径的条件耦合。
    *   **Post-Processing Pipeline** (**v0.9.3**): 引入 `BakePostProcessor`。通过隔离场景 (Scene Isolation) 实现 OIDN 降噪，确保后处理逻辑不干扰主烘焙任务。
    *   `BakeStepRunner`: 异步烘焙主控。支持分段性能采样 (`bake_time`, `save_time`)。
    *   **Cage Analysis Engine** (**v0.9.5**): `CageAnalyzer` 模块实现了基于 NumPy 射线追踪的低模-高模间距预判。支持生成热力图 (Heatmap) 式的诊断报告。
    *   **Delivery Pipeline** (**v0.9.5**): `ModelExporter` 实现了基于 GLB/USD 的一键交付功能。核心逻辑包含 PBR 材质重组、坐标空间转换与 VRAM 深度清理。
    *   **Context Management**: `BakeContextManager` 全面迁移至 `contextlib.ExitStack`。所有的场景临时设置都能保证 100% 原子级回滚。
3.  **Core Layer** (`core/`): 无状态工具模块。
    *   **Standardized Properties**: 核心属性名已统一为 `snake_case`，并通过 `PRESET_MIGRATION_MAP` 保持向后兼容。
    *   **Global SYSTEM_NAMES** (**v0.9.0**): 引入统一的常量字典 `constants.SYSTEM_NAMES`，彻底消除散落各处的 `BT_` 魔法字符串。
    *   `compat.py`: 版本兼容层 (3.6 - 5.0+)。

---

## 2. Technical Feature Breakdown

### 2.1 Principled BSDF Analysis
`NodeGraphHandler` 自动识别 Principled BSDF 节点。支持 4.0+ 的插槽更名适配。

### 2.2 NumPy Acceleration
PBR 转换和通道打包使用 NumPy 向量化计算。支持在 8K 分辨率下保持极低 CPU 开销。

### 2.3 Smart Property Migration
`PropertyIO` 包含一个内置的映射表,当加载旧版本的 `.json` 预设时,会自动将扁平属性映射到新的嵌套设置结构中,确保向后兼容性。

### 2.4 Smart Object Reuse (Post-Bake)
`apply_baked_result` 会检测现有的 `_Baked` 结果物体并执行 `refresh_mesh` 原地更新材质，而非创建重复的 Object 容器。

### 2.5 Select to Active (High-to-Low)
`SELECT_ACTIVE` 工作流由 `JobPreparer` 智能处理。仅验证 Active 物体的 UV,允许高模源物体无需 UV 坐标。

### 2.6 Version Compatibility Layer
`core/compat.py` 提供统一的版本兼容接口:
- `IS_BLENDER_5`, `IS_BLENDER_4`, `IS_BLENDER_3`: 版本检测标志
- `get_bake_settings(scene)`: 统一访问烘焙设置 (处理 5.0 的 `render.bake` vs 旧版本)
- `configure_bake_settings()`: 一站式配置所有烘焙参数

### 2.9 Visual Cage Analysis Heatmap (**v0.9.5**)
`CageAnalyzer` 自主分析低模与高模的几何重叠度。
- **Heatmap 算法**: 计算顶点到最近表面的距离，并将错误（Error Count）反馈至 UI 列表。
- **无 UI 依赖**: 算法完全基于 `bvhtree.ray_cast`，支持 Headless 模式运行。

### 2.10 Zero-Friction Delivery Pipeline (**v0.9.5**)
`ModelExporter` 接管了烘焙后的资产分发。
- **PBR 封装**: 自动将烘焙好的 Map 封装为符合 Khronos 标准的 PBR 材质。
- **清理机制**: 导出后立即执行 `img.gl_free()`，防止在循环烘焙大型资产时发生 VRAM 溢出崩溃。

### 2.7 Modal Execution Layer & State Recovery
`core/execution.py` provides `BakeModalOperator` Mixin and the standalone `add_bake_result_to_ui` function.
- **`add_bake_result_to_ui` [New]**: Decoupled from the Modal context. Used by both the operator and the E2E test suite to ensure consistent, head-less compatible result reporting and metadata calculation (duration, resolution, file size).
**新功能**: `BakeStateManager` 现在记录执行队列的游标 (`current_queue_idx`)。系统可据此提供断点续烘功能。

### 2.8 Atomic Emergency Cleanup (**v1.0.0**)
`core/cleanup.py` 的 `BAKETOOL_OT_EmergencyCleanup` Operator 用于崩溃后的清理。
**安全性强化**: 系统在生成保护节点等临时对象时，会打上底层标记（如 `n["is_bt_temp"] = True`），清理过程优先依据此 GUID 标签销毁，杜绝误伤同名的用户资产。

---

## 3. Testing Suite
### 3.1 核心套件 (`test_cases/suite_*.py`)
- **`suite_unit.py`**: 核心逻辑测试，通过 `self.subTest` 实现参数化 Extension 验证，补备了降噪器流程覆盖。
- **`suite_ui_logic.py`**: 验证 N 面板与图像编辑面板的绘制逻辑。
- **`suite_api.py`**: 验证 `core/api.py` 的公共函数稳定性。
- **`suite_preset.py`**: 验证预设序列化、崩溃恢复状态机、场景属性对称性及通道生成完整性。
- **`suite_production_workflow.py`** (**v0.9.5 强化**): 真正的端到端 (E2E) 流程验证。引入了基于 `DataLeakChecker` 的防泄漏监控 (`with assert_no_leak`)。
- **`suite_parameter_matrix.py`**: 穷举矩阵测试。使用 `constants` 动态提取通道列表，彻底取代硬编码验证。

### 3.2 运行方式
1.  **UI 运行**: 在 Blender N 面板 → Baking → 开启 **Debug Mode** → 点击 **Run Test Suite**。结果将直接显示在面板上。
2.  **CLI 运行**: 使用 `automation/suite_runner.py` 或 `automation/multi_version_test.py` 进行跨版本验证。

### 3.3 跨版本自动化测试 (`automation/`) - **金标准**
- **要求**: 在发布重构（如 `BakeModalOperator` 改动）后，必须运行全量跨版本测试。

## 4. 开发规范与踩坑记录 (Pitfalls)

### 4.1 属性类型安全
*   **EnumProperty**: 当 `items` 参数使用函数回调时，`default` **必须是整数索引**。

### 4.2 统一日志规范
*   **Logger**: 必须使用 `logging.getLogger(__package__)` 获取的 logger。
*   **Error Reporting**: 使用 `core/common.py` 中的 `log_error` 函数，确保错误同时记录到控制台、场景 UI 状态和崩溃恢复日志中。
*   **IDProperty Security**: **严禁**直接将 `bpy.types.ID` (如 Material) 存入 IDProperty (`obj["key"]`)。必须存储 `.name` 并在使用时动态获取，以防无效指针崩溃。
*   **Iterator Safety**: 在使用 `next()` 获取 Active Object 等集合元素时，必须提供默认值 fallback，以防 StopIteration 抛出。

### 4.4 跨版本关键死角 (Version-Specific Pitfalls)
针对 v0.9.5 修复的深层兼容性问题的总结：
- **Blender 5.0 (Node Access)**: 自 5.0 起，场景节点树属性由 `node_tree` 迁移至 `compositing_node_group`（或在某些 context 下不可用）。代码中必须使用 `hasattr` 探测，并优先通过 `node_tree_add()` 确保对象存在。
- **Blender 4.2+ (Bake Settings)**: 烘焙设置从 `scene.render` 迁移到了 `scene.render.bake`。必须通过 `compat.get_bake_settings()` 中转访问。
- **Blender 3.3/3.6 (UDIM Headless Init)**: 在旧版后台模式下，仅 `tiles.new(1001)` 不足以触发 C++ 层的缓冲区分配，会导致烘焙算子报 `Uninitialized image`。
    - **避坑指南 (v1.0.0 Fix)**: 必须执行“三重触发”：分配物理路径 (`image.filepath_raw`) -> 设置 `<UDIM>` 占位符格式 -> 调用 `image.pack()` 强制内存同步。
- **Memory Leak Detection**: 在 E2E 测试中，`assert_no_leak` 必须包裹 `cleanup_scene()` 之后的所有生成逻辑，且在退出 Block 前必须再次执行清理，以防假阳性泄露报错。

### 4.5 动态对齐与参数一致性 (Dynamic Alignment & Consistency)
为了彻底防范拼写导致的 `AttributeError` 或更新遗漏（如元数据字段缺失），系统遵循以下准则：
- **元数据契约**: `BakeStepRunner` 产生的 `meta` 字典必须包含所有在 `property.BakedImageResult` 中定义的关键性能指标字段（如 `bake_time`, `save_time`）。
    - **扩展规范**: 新增元数据字段必须在 `BakedImageResult` (RNA) 和 `add_bake_result_to_ui` (Mapping) 两处同步注册。
- **执行流与 UI 对齐**: 所有的执行结果通过 `core/execution.py` 中的 `add_bake_result_to_ui` 方法进行中转，该方法确保了元数据到 RNA 属性的类型安全映射。
- **导出文件名对齐**: 自动化测试依赖于确定的文件名。导出逻辑必须优先使用 `task.base_name` 而非 `obj.name`，以防止材质重名导致的覆盖。
- **回归防御**: `test_cases/suite_production_workflow.py` 必须包含对新增元数据字段的 `assertIn` 验证。
- **常量字典**: 所有的系统临时资源名称（图层、材质等）**必须**使用 `constants.py` 里的 `SYSTEM_NAMES`。
- **i18n 对齐**: `extract_translations.py` 会自动扫描代码中的字符串，确保 UI 提示语与翻译词库动态同步。

### 4.4 自动化测试架构 (v0.9.3 重构)
- **统一入口**: 使用 `automation/cli_runner.py` 作为唯一的测试入口。
- **环境隔离**: `automation/env_setup.py` 负责路径挂载与模块清理，确保测试环境一致性。
- **矩阵测试**: `automation/multi_version_test.py` 负责跨版本轮询验证。

### 4.5 材质保护节点 (BT Protection) 与上下文
为了防止 Blender 误用非活动材质的节点，引擎会自动注入保护节点，并通过 `is_bt_temp` 打标。
在为 UDIM 生成新瓦片或强制进行操作时，请利用 `bpy.context.temp_override` 或底层的 `image.tiles.new` 来执行，**严禁**随意篡改或劫持 UI Area 的类型（`area.type = 'IMAGE_EDITOR'`），以防无头模式或复杂 UI 崩溃。

## 5. 开发者工作流：参数一致性与动态对齐 (Standard Checklist)

为了防止因拼写错误或逻辑遗漏导致的 `AttributeError`（特别在跨版本环境下的元数据丢失），任何新增的“烘焙指标”或“元数据字段”必须遵循以下 **“参数对齐协议 (Parameter Alignment Protocol)”**：

### 5.1 数据流向协议 (Alignment Points)
1.  **RNA 注册** (`property.py`): 在 `BakedImageResult` 类中定义属性（确保 UI 能显示）。
2.  **数据生产** (`core/engine.py`): 在 `BakeStepRunner.run` 的 `meta` 字典中填入数值。
3.  **数据映射** (`core/execution.py`): 在 `add_bake_result_to_ui` 中将 `meta` 映射至 RNA 属性。
4.  **UI 呈现** (`ui.py`): 在 `BAKETOOL_UL_BakedImageResults` 或详情面板中引用该属性。
5.  **回归防御**: 在 `test_cases/suite_production_workflow.py` 增加断言验证该字段在所有版本下均非空。

### 5.2 状态同步与环境健康
新增任何对于外部插件的依赖（如导出、新降噪驱动），必须在 `ui.py` 的 `draw_env_status` 中同步添加可用性检查逻辑。

### 5.4 第四点：回归测试 (Guard)
在 `test_cases/suite_production_workflow.py` 中增加断言验证。
```python
# test_cases/suite_production_workflow.py
self.assertTrue(hasattr(res, 'vram_usage'))
self.assertGreater(res.vram_usage, 0.0)
```

---

## 6. Iteration Plan & Roadmap (v1.0.0 Update)

- [x] **Modular Engine (v0.9.0)**: Split `BakePassExecutor` into granular pipeline methods.
- [x] **E2E Stability (v0.9.5)**: 100% matrix pass rate for 3.6-5.0.
- [x] **Architecture Hardening**: Robust context manager (`ExitStack`), atomic cleanup, and 100% data-driven UI.
- [x] **Visual Cage Analysis heatmaps (v0.9.5)**: Integrated proximity diagnostics.
- [x] **Zero-Friction GLB/USD Export (v0.9.5)**: Automated post-bake delivery.
- [x] **Performance Profiler (v0.9.3)**: Segmented timing for Bake vs Save phases.
- [x] **Denoise Pipeline (v0.9.3)**: Integrated OIDN node-based processing.
- [x] **Visual Preset Library (v0.9.3)**: Thumbnail gallery with dynamic refresh logic.
- [x] **Exhaustive Matrix Testing**: 100% cross-version coverage (540+ cases).
- [ ] **Background Process Baking (Phase 4.1)**: Multi-process delegation and cluster support.
- [ ] **External Engine Bridge (Phase 5.1)**: Unified API for Marmoset/Substance integration.
- [ ] **AI-Assisted Retopology Bridge (Phase 6.2)**: Automated LOD generation.
