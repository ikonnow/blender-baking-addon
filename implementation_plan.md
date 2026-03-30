# Simple Bake Tool (SBT) 研发攻坚行动计划 (Phase 3.1 & 3.2)

本计划书是针对**近期及中期方略**的落地执行大纲。目标是突破当前的纯烘焙局限，完成从“内部实用工具”向“标准资产交付中间件”的关键跨越，同时补齐可视化除错与极致内存控制。

## 一、 核心目标与特性拆解

### 🎯 目标 1: 零摩擦资产交付 (One-Click USD/glTF Closed-Loop)
**目的**：烘焙完毕后不仅停留在 Blender，必须自动将其打包为游戏引擎立即可用的标准化 PBR 资产文件（包含自动连接好的材质节点）。
- [x] 当前状态：具备粗糙的 `ModelExporter.export`，但只导出网格，缺乏 PBR 材质与烘焙贴图的**强绑定**。
- [ ] 升级计划：
  1. 强化 `apply_baked_result` 逻辑，在克隆低模的同时，自动编织一套极简的 Principled BSDF，将刚生成的贴图注入。
  2. 扩展 `ModelExporter.export`，支持将贴图打包进 `.glb` 或随 `.usd` 关联导出。

### 🎯 目标 2: 视觉包裹框分析 (Visual Cage Analysis)
**目的**：在长达数十分钟的烘焙前，几秒钟内预测并高亮显示高低模穿插的“漏光/错误”区域。
- [x] 当前状态：仅支持简单的 Proximity 数值预测，无视觉反馈。
- [ ] 升级计划：
  1. 引入 Raycasting 算法核引擎。
  2. 通过顶点色 (Vertex Color) 或 GPU 屏幕空间外框 (GPU Overlay) 实时绘制穿插点（红色高亮）。

### 🎯 目标 3: 强制垃圾回收与防泄露 (Aggressive GC & Memory Leak Defense)
**目的**：消除因为连续大量烘焙（特别是 UDIM 100+ 瓦片）触发 Blender 内存墙的问题。
- [x] 当前状态：依赖 `Image.update()` 和基础的 Python GC。
- [ ] 升级计划：在流水线切换通道时，实施具有侵略性的强制 VRAM 转移与释放。

---

## 二、 [需用户审核] 关键设计与修改范围 (Proposed Changes)

> [!IMPORTANT]
> 此部分决定了我们将动刀的核心代码库。请核对这些位置的改动是否符合你的架构预期。

### 模块 A: 交付与导出中心 (Delivery System)

#### [MODIFY] `e:\blender project\project\script project\Addons\baketool\core\engine.py`
- **修改 `apply_baked_result`**：新增 `build_pbr_material(obj, baked_images)` 功能。使用代码自动新建一个材质，并创建 Image Nodes，把 Base Color, Normal, ORM 等接口按照标准连好。
- **修改 `ModelExporter.export`**：不再仅调用基础 export，而是先将打包好的 Image Nodes 设置为当前材质，然后再调 `.glb` 导出指令（需确保 format = 'GLTF_SEPARATE' 或打包贴图）。

#### [MODIFY] `e:\blender project\project\script project\Addons\baketool\property.py`
- **新增属性**：在 `BakeJobSetting` 增加 `export_textures_with_model: BoolProperty`，允许用户选择纯网格还是带图导出。

### 模块 B: 可视化分析引擎 (Analysis Engine)

#### [NEW] `e:\blender project\project\script project\Addons\baketool\core\cage_analyzer.py`
- **开发新模块**：实现 `run_raycast_analysis(low_poly, high_poly, extrusion)` 方法。
- **技术栈**：使用 `mathutils.bvhtree.BVHTree.FromObject` 构建高模树，用低模沿法线发射射线（偏移量为 cage 挤出量）。如果 `is_hit == False`，则认为“射失”（可能出现黑色锯齿或包裹不住），标记该顶点。
- **反馈层**：生成名为 `BT_CAGE_ERROR` 的顶点色图层，将射失点染成纯红色。

#### [MODIFY] `e:\blender project\project\script project\Addons\baketool\ui.py`
- **界面修改**：在 `draw_saves` 的 Smart Intelligence 区块下方新增一个醒目的大按钮：`"🔍 Analyze Cage Overlap"`。

#### [MODIFY] `e:\blender project\project\script project\Addons\baketool\ops.py`
- **新增操作符**：`BAKETOOL_OT_AnalyzeCage`。作为 `cage_analyzer.py` 的前端挂载点。

### 模块 C: 内存防火墙 (Memory Guard)

#### [MODIFY] `e:\blender project\project\script project\Addons\baketool\core\execution.py`
- **强化 `BakeModalOperator.finish` 与 `_process_single_step`**：
  在每个通道烘焙完成且 Save (持久化) 完毕后，如果是大数据贴图且不需用于合包 (Packing)，立即对其执行 `img.gl_free()` 和 `img.buffers_free()` (Blender 3.x+ C++ API) 或触发显式的 `bpy.data.images.remove`，以此抹平尖峰内存。

---

## 三、 [需用户审核] 全方位验证与测试方略 (Verification Plan)

本阶段的开发极其强调“测试驱动 (TDD)”。以下为明确的测试用例布置（基于当前的 `test_cases/` 结构）：

### 1. 交付闭环验证 (Delivery Loop Test)
**测试目标件**：`test_cases/suite_production_workflow.py`
- **新增 Test**: `test_full_gltf_export_loop`
  - 流程：创建一个基础网格 -> 执行 `BSDF` 各通道烘焙 -> 检查是否生成 `Baked_Results` 物体 -> **核心断言**：读取外部存储系统，反向加载导出的 `.glb` 文件，验证其是否成功绑定了生成的 `.png` 或者内置了正确的 Buffer 字节流。

### 2. 射线检测稳健性验证 (Raycast Logic Test)
**测试目标件**：`test_cases/suite_unit.py` (新建一套类：`TestCageAnalyzer`)
- **新增 Test**: `test_cage_raycast_hit_detection`
  - 流程：用 Python 创建一个直径为 2 的高模球，和一个直径为 1 的低模球。
  - 断言 1：挤出设置为 0.4 时，检测器必须返回 100% Errors (包裹不完全)。
  - 断言 2：挤出设置为 0.6 时，检测器必须返回 0% Errors (完全包裹)。
  - 极细粒度的几何数学隔离测试，确保核心算法正确。

### 3. 深层内存泄露压测 (Deep Leak Test)
**测试目标件**：`test_cases/suite_production_workflow.py`
- 扩展 `assert_no_leak` 的检查范围：在大量生成 8K 贴图的模拟任务中，监听 `bpy.data.images` 的总量。不仅要通过泄漏检查，还要对**显存占用峰值**进行 `import psutil` 式的侧信道分析（可选，若系统支持）。

---

## 四、 悬而未决的问题 (Open Questions)

> [!WARNING] 
> 请在推进到代码实现前反馈以下疑问：

1. **导出材质标准的取舍**：在将贴图组装进导出网格以备 `.glb` 导出时，是组装成标准的 `Principled BSDF`，还是仅仅简单应用 `Emission` 节点？（通常主流游戏资产采用组装 Principled：BaseColor + Normal + ORM 连入单独的槽）。
2. **可视化结果显示**：包裹框交叉检测之后，生成一个红点顶点色图层，是否需要我们自动把这个模型切换到“顶点色(Vertex Paint) / 实体验证模式”，以强制让用户立刻看到红色斑块？

---

请确认以上模块划分、代码位置以及测试验证矩阵是否符合预期？一旦确认，我会先分解出具体的 `task.md`。
