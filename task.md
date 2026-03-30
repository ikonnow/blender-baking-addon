# BakeTool 研发攻坚行动清单 (Phase 3.1 & 3.2)

本任务列表用于追踪“近期及中期战略方略”的落地实施。当前优先执行“一键资产交付 (USD/glTF)”，并为后续的两大护城河能力打好基础。

## 🎯 优先战役 1: 零摩擦资产交付闭环 (USD/glTF Delivery Loop)
- `[x]` **`core/engine.py`**: 开发 `build_pbr_material` 函数。
  - 自动新建材质，创建 `Principled BSDF`，并将传入的 `baked_images`（BaseColor, Normal, MR 等）链接到对应的 Socket 上。
- `[x]` **`core/engine.py`**: 重构 `ModelExporter.export`。
  - 在原有的导出逻辑前，劫持并注入上述构建的材质。
  - 针对 GLB 格式，设置 `export_format='GLTF_SEPARATE'` 或打包模式，确保物理图片绑定成功。
- `[x]` **`property.py` & `ui.py`**: 配置专属开关。
  - 增加 `export_textures_with_model` (携带材质与贴图导出) 开关，默认激活。
- `[x]` **`test_cases/suite_production_workflow.py`**: 追加完整交付验证。
  - 新增 E2E 节点，读取导出的 GLB 测试其贴图包容量或材质属性节点存在性。

## 🛡️ 战役 2: 视觉包裹分析引擎基础 (Visual Cage Analysis)
- `[x]` **`core/cage_analyzer.py`**: 创建基础框架。
  - 实现射线数学计算模块 `run_raycast_analysis` 的骨骼架子（使用 BMesh 与 BVHTree）。
- `[x]` **`property.py`**: 注册界面属性。
  - 新增针对笼状容差的控制组，以及 `auto_switch_vertex_paint` (默认 False) 选项。
- `[x]` **`ops.py` & `ui.py`**: 加入呼出入口。
  - 添加 `BAKETOOL_OT_AnalyzeCage`，在 UI 面板“Smart Intelligence”中绘制 `Analyze Cage Overlap` 按钮。
- `[x]` **`test_cases/suite_unit.py`**: 部署基础的数学断言测试 (`TestCageAnalyzer`)。

## 🧹 战役 3: 激进垃圾回收防泄露基础 (Memory Safety Guard)
- `[x]` **`core/execution.py`**: 在模态操作周期的收尾点 (`_process_single_step` 结束后)，探查并引入 `img.gl_free()` 与主动内存收缩。
- `[x]` **`core/cleanup.py`**: 强化 Crash 和正常完成后的游离 `Image` 孤单节点强回收。
