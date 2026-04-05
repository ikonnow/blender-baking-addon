# BakeTool 改进与优化任务看板 (v0.9.5 -> v1.0.0)

## 🔴 Phase 1: 核心 Bug 修复 (Critical Bug Fixes)
- [ ] **[CB-1]** 修复 `core/compat.py` 中的同义反复逻辑，确保 NORMAL 映射正确 (B3.x/B4+)
- [ ] **[CB-2]** 重构 `core/api.py` 的 `bake()` 函数，使其正确处理 `objects` 参数，不再强制调用 UI 算子
- [ ] **[CB-3]** 修复 `core/execution.py` 中的类级可变对象污染问题 (`bake_queue = []`)
- [ ] **[CB-4]** 为 `core/execution.py` 中的 `gl_free()` 增加 Blender 5.0+ 版本守护
- [ ] **[CB-5]** 修正 `core/cage_analyzer.py` 的裸 `except` 捕获，改为 `except Exception`

## 🟠 Phase 2: 高优先级改进 (High Priority Improvements)
- [ ] **[HP-1]** 解决 `core/cage_analyzer.py` 中的 BMesh 内存泄漏 (使用 `try/finally`)
- [ ] **[HP-2]** 修复 `core/cage_analyzer.py` 的选择状态副作用，操作后恢复原始选择
- [ ] **[HP-4]** 修复 `core/engine.py` 中空列表可能导致的 `IndexError`
- [ ] **[HP-5]** 修正 `core/shading.py` 节点连接：在颜色输出与 Shader 输入间插入 `Emission` 节点
- [ ] **[HP-6]** 修复 `core/image_manager.py` 在未保存文件时的路径回退逻辑 (使用 `bpy.app.tempdir`)
- [ ] **[HP-7]** 修复 `core/common.py` 中的孤立网格数据残留问题
- [ ] **[HP-8]** 在 `core/engine.py` 导出逻辑前增加插件依赖性检查 (glTF/USD)
- [ ] **[HP-9]** **全局替换**：将所有散乱的 `bpy.app.version` 检查统一至 `compat` 模块调用

## 🟡 Phase 3: 测试套件硬化 (Testing & Automation)
- [ ] **[TB-1]** 修复 `suite_parameter_matrix.py` 中的 Linux 硬编码路径问题
- [ ] **[TB-2]** 增强 `suite_preset.py`：验证序列化后的频道顺序一致性
- [ ] **[TB-3]** 修正 `suite_unit.py` 中的无效断言逻辑
- [ ] **[TB-6]** 修复 `cli_runner.py` 中的测试套件映射表错误
- [ ] **[D-3]** 移除 `automation/multi_version_test.py` 中的个人硬编码路径
- [ ] **[NEW]** 增加端到端测试：取消烘焙后的状态恢复 (State Recovery)
- [ ] **[NEW]** 增加端到端测试：降噪 (Denoise) 流程验证

## 🔵 Phase 4: 文档与代码质量 (Quality & Documents)
- [ ] **[D-1]** 统一 `__init__.py`、`manifest` 与 `README` 中的版本号为 `1.0.0`
- [ ] **[MP-2]** 清理 `api.py`、`engine.py` 等 6 个文件中的未使用 Import
- [ ] **[MP-11]** 将 `core/common.py` 中的 `_create_simple_mat` 嵌套函数提取至模块级别
- [ ] **[D-2]** 修正 `DEVELOPER_GUIDE.md` 中的重复章节编号

---
**目标**：执行 `automation/multi_version_test.py` 并保证 B3.6、B4.2、B5.0 全部 PASS。
