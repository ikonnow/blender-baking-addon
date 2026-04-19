# BakeTool 开发者指?## Developer Guide

**版本:** 1.0.0
**更新日期:** 2026-04-17

---

## 概述

本指南为 BakeTool 的后续开发提供架构说明、技术规范及已知问题的记录。通过遵循本指南，您可以有效地为项目做出贡献，同时保持代码质量和跨版本兼容性?
---

## 第一章：尝试性的设计架构

### 1.1 三层架构设想 (Tentative Design)

BakeTool 尝试遵循 **UI-Engine-Core** 三层逻辑划分。我们承认由于大量逻辑由 AI 生成，目前各层之间可能仍存在耦合风险，后续维护应保持警惕?

```
┌─────────────────────────────────────────────────────────────??                   UI / Operator ?                         ?? ops.py, ui.py                                             ?? - 数据驱动?UI (CHANNEL_UI_LAYOUT)                        ?? - ?Operator (Thin Operators)                            ?? - 环境健康监测                                            ?└─────────────────────────────────────────────────────────────?                              ?                              ?┌─────────────────────────────────────────────────────────────??                   Engine ?(编排?                          ?? core/engine.py                                            ?? - JobPreparer: 验证输入并准备执行队?                     ?? - BakePassExecutor: 执行烘焙步骤                          ?? - BakeStepRunner: 异步烘焙主控                            ?? - BakePostProcessor: 降噪后处?                          ?└─────────────────────────────────────────────────────────────?                              ?                              ?┌─────────────────────────────────────────────────────────────??                   Core ?(无状态工?                      ?? core/*.py                                                 ?? - image_manager: 图像管理                                 ?? - node_manager: 节点操作                                  ?? - uv_manager: UV 层处?                                  ?? - shading: 着色器工具                                    ?? - common: 共享工具                                        ?? - compat: 版本兼容                                        ?└─────────────────────────────────────────────────────────────?```

### 1.2 核心组件

#### 1.2.1 JobPreparer

负责验证输入并准备执行队列：

```python
class JobPreparer:
    @staticmethod
    def prepare_execution_queue(context, jobs) -> List[BakeStep]:
        """验证输入并准备执行队?""
        queue = []
        for job in jobs:
            if not job.enabled:
                continue
            # 验证对象
            # 准备通道配置
            # 创建 BakeStep
            queue.append(step)
        return queue
```

#### 1.2.2 BakePassExecutor

执行单个烘焙步骤的流水线?
```python
class BakePassExecutor:
    @staticmethod
    def execute(context, setting, task, channel, ...) -> Image:
        """执行烘焙通道"""
        # 1. 创建目标图像
        # 2. 准备烘焙参数
        # 3. 执行 Blender 烘焙操作
        # 4. 应用 NumPy 处理
        # 5. 返回烘焙结果
```

#### 1.2.3 BakeStepRunner

异步烘焙主控，支持分段性能采样?
```python
class BakeStepRunner:
    def run(self, step: BakeStep, state_mgr=None, queue_idx=0) -> List[Dict]:
        """执行单个步骤并返回生成的结果"""
        job, task, channels, frame_info = step.job, step.task, step.channels, step.frame_info
        results = []
        # ... 执行逻辑
        return results
```

#### 1.2.4 BakePostProcessor

封装烘焙后的图像后处理逻辑?
```python
class BakePostProcessor:
    @staticmethod
    def apply_denoise(image, reuse_scene=None):
        """应用 OIDN 降噪"""
        # 创建临时合成器场?        # 配置降噪节点
        # 执行降噪
        # 清理临时场景
```

---

## 第二章：关键技术规约

### 2.1 三点对齐协议 (Triple-Point Alignment Protocol)
为了避免 AI 在生成不同文件时产生参数脱节，本项目尝试实施三点对齐规范：

1.  **Constants**: 在 `constants.py` 中定义所有原始默认值、范围和映射。
2.  **Property**: `property.py` 的 RNA 属性定义必须引用上述常量。
3.  **Engine**: 核心执行逻辑直接读取 RNA 属性或常量。

**校验机制**: 必须通过 `suite_parameter_matrix.py` 动态验证 100+ 种参数组合下的同步状态，尝试在发布前发现逻辑断层。

### 2.2 AI 代码维护规范
本项目中超过 70% 的代码由 AI 辅助生成。由于缺乏大规模生产环境的洗礼，维护者需遵循：
1.  **逻辑怀疑**: 不要假设 AI 生成的逻辑分支是覆盖完备的。
2.  **强制测试**: 任何对 AI 生成函数的修改，必须同步运行对应的集成测试。
3.  **姿态中立**: 在注释中保持客观描述，避免使用过度自信的判断语。

---

## 第三章：测试套件

### 3.1 测试套件清单

| 套件 | 文件 | 描述 |
|------|------|------|
| suite_unit.py | 单元测试 | 核心组件逻辑测试 |
| suite_memory.py | 内存测试 | 内存泄漏检?|
| suite_export.py | 导出测试 | 导出安全?|
| suite_api.py | API 测试 | 公共 API 稳定?|
| suite_ui_logic.py | UI 测试 | 面板绘制逻辑 |
| suite_preset.py | 预设测试 | 序列化与迁移 |
| suite_negative.py | 负面测试 | 边界条件 |
| suite_denoise.py | 降噪测试 | 降噪器集?|
| suite_production_workflow.py | E2E 测试 | 端到端流?|
| suite_context_lifecycle.py | 生命周期测试 | 上下文管?|
| suite_parameter_matrix.py | 矩阵测试 | 参数组合测试 |
| suite_compat.py | 兼容性测?| 版本兼容?|
| suite_cleanup.py | 清理测试 | 资源清理 |
| suite_shading.py | 着色测?| 着色器逻辑 |
| suite_udim_advanced.py | UDIM 测试 | UDIM 功能 |
| suite_code_review.py | 代码审查测试 | 静态检?|

### 3.2 运行测试

#### Blender UI 运行

```
Blender ?N 面板 ?Baking ?Debug Mode ?Run Test Suite
```

#### CLI 运行

```bash
# 单个套件
blender -b --python automation/cli_runner.py -- --suite unit

# 所有套?blender -b --python automation/cli_runner.py -- --suite all

# 按类?blender -b --python automation/cli_runner.py -- --category memory

# 跨版本测?python automation/multi_version_test.py --verification
```

### 3.3 测试辅助工具

#### DataLeakChecker

检?Blender 数据块泄漏：

```python
from test_cases.helpers import DataLeakChecker

checker = DataLeakChecker()
# ... 执行操作 ...
leaks = checker.check()
```

#### assert_no_leak

上下文管理器?
```python
with assert_no_leak(self):
    create_bake_result()
```

#### JobBuilder

流畅 API 构建测试?
```python
job = (JobBuilder("TestJob")
    .mode("SINGLE_OBJECT")
    .type("BSDF")
    .resolution(512)
    .add_objects([obj])
    .build())
```

---

## 第四章：开发规?
### 4.1 代码风格

遵循 Google Python Style Guide?
- 使用 `snake_case` 命名函数和变?- 使用 `CapWords` 命名?- 使用 `ALL_CAPS` 命名常量
- 为所有公共函数和类添?docstring

### 4.2 异常处理

避免?`except:` 子句?
```python
# BAD
try:
    do_something()
except:
    pass

# GOOD
try:
    do_something()
except (ReferenceError, RuntimeError) as e:
    logger.debug(f"Failed: {e}")
```

### 4.3 版本兼容?
使用 `compat.py` 中的工具函数?
```python
from core.compat import IS_BLENDER_5, get_bake_settings

if IS_BLENDER_5:
    # Blender 5.0+ 特定代码
else:
    # 旧版本代?```

### 4.4 参数一致?
遵循三点点对齐协议：

1. **Constants** ?`constants.py` 定义所有系统常?2. **Engine** ?`core/engine.py` 使用常量
3. **Automation** ?`automation/*.py` 验证对齐

### 4.5 IDProperty 安全

严禁直接存储 `bpy.types.ID`?
```python
# BAD
obj["material"] = some_material

# GOOD
obj["material_name"] = some_material.name
# 使用?material = bpy.data.materials.get(obj["material_name"])
```

---

## 第五章：已知问题与解决方?
### 5.1 EnumProperty 安全

?`items` 参数使用函数回调时，`default` **必须是整数索?*?
```python
# BAD
prop = EnumProperty(
    items=my_items_func,
    default="option_a"  # 字符串会报错
)

# GOOD
prop = EnumProperty(
    items=my_items_func,
    default=0  # 整数索引
)
```

### 5.2 Blender 5.0 节点架构

B5.0 统一了节点系统：

```python
# 旧版?tree = bpy.data.node_groups.new("MyTree", type='COMPOSITING')
output_node = tree.nodes.new('CompositorNodeComposite')

# B5.0+
tree = bpy.data.node_groups.new("MyTree", type='CompositorNodeTree')
output_node = tree.nodes.new('NodeGroupOutput')
```

### 5.3 UDIM Headless 初始?
在旧版后台模式下，必须执?三重触发"?
```python
image.filepath_raw = f"//{tile_path}<UDIM>.png"
image.file_format = 'PNG'
image.pack()
```

### 5.4 内存泄漏检?
?E2E 测试中，`assert_no_leak` 必须包裹所有生成逻辑?
```python
def test_bake_result(self):
    with assert_no_leak(self):
        create_images()
        create_objects()
    # 测试后清?    cleanup_scene()
```

---

## 第六章：开发者工作流

### 6.1 开发检查清?
| 步骤 | 描述 |
|------|------|
| 1 | 编写测试用例 |
| 2 | 实现功能 |
| 3 | 运行单元测试 |
| 4 | 运行集成测试 |
| 5 | 运行跨版本测?|
| 6 | 更新文档 |
| 7 | 代码审查 |

### 6.2 提交规范

```bash
# 功能分支
git checkout -b feature/amazing-feature

# 提交
git commit -m "feat: add amazing feature"

# 推?git push origin feature/amazing-feature

# 创建 Pull Request
```

### 6.3 版本发布

```bash
# 1. 更新版本?# 2. 更新 CHANGELOG
# 3. 运行所有测?# 4. 创建 Git tag
git tag v1.0.0
git push origin v1.0.0
```

---

## 第七章：参考资?
### 7.1 官方文档

- [Blender Python API](https://docs.blender.org/api/current/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Blender Stack Exchange](https://blender.stackexchange.com/)

### 7.2 相关项目

- [pytest-blender](https://github.com/puckow/pytest-blender)
- [blender-addon-tests](https://github.com/p2or/blender-addon-tests)

---

*开发者指南版?1.0.0*
*最后更? 2026-04-17*
