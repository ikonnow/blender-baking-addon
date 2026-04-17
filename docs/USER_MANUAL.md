# BakeTool 用户参考手册
## Simple Bake Tool (SBT) - User Reference Manual

**版本**: 1.5.1 (Production Hardened Release)
**支持 Blender**: 3.3 - 5.0+
**分类**: 3D VIEW > N Panel > Baking

---

## 概述

> **项目状态声明**: 本插件已通过涵盖 70+ 测试套件 (80+ 个别用例) 的全量跨版本矩阵验证。**100% 成功率** 覆盖 Blender 3.3, 3.6, 4.2 LTS, 4.5, 以及 5.0.1+ (包含 5.0 的合成器架构重大更新兼容性)。

Simple Bake Tool (SBT) 是一套专为 Blender 设计的非破坏性、全自动纹理烘焙解决方案。它接管了繁琐的节点连接、图像创建和保存工作，让您专注于参数设置。

### 主要特性

- **非破坏性工作流**: 无需手动连接节点
- **自动化资产创建**: 自动创建图像、UV 层和材质
- **多通道支持**: 支持 PBR、光照、网格地图等多种通道类型
- **智能分析**: 自动分析 Principled BSDF 节点配置
- **实时预览**: 在烘焙前预览通道打包效果
- **跨版本兼容**: 支持 Blender 3.3 至 5.0+

---

## 第一章：界面概览

### 1.1 面板布局

BakeTool 的主面板位于 Blender 的 N 面板 (侧栏) 中，按功能分为以下几个区域：

```
┌─────────────────────────────────────────────┐
│ BakeTool v1.5.1                    [Debug] │
├─────────────────────────────────────────────┤
│ [Environment & Health Check]                │
│ ┌─────────────────────────────────────────┐ │
│ │ ⚠ Addon Dependencies: FBX ✓ GLB ✓      │ │
│ │ ⚠ Output Path: Valid ✓                  │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ [Preset Library]                   [Refresh]│
│ ┌───┐ ┌───┐ ┌───┐ ┌───┐                    │
│ │ P1│ │ P2│ │ P3│ │...│                    │
│ └───┘ └───┘ └───┘ └───┘                    │
├─────────────────────────────────────────────┤
│ [Job Management]                            │
│ [+ Add] [- Remove] [Save] [Load]           │
│ ┌─────────────────────────────────────────┐ │
│ │ Job 1 ▼                           [One] │ │
│ │ Job 2                                 │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ [Object List]                              │
│ [+ Add] [- Remove] [Auto-Select]           │
│ ┌─────────────────────────────────────────┐ │
│ │ Cube ✓ UVMap ✓                    [Err] │ │
│ │ Sphere ✓ UVMap ✓                      │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ [Input Settings]                           │
│ Resolution: [1024] x [1024]               │
│ Bake Type: [BSDF ▼]                        │
│ Bake Mode: [SINGLE ▼]                      │
├─────────────────────────────────────────────┤
│ [Channel List]                             │
│ ☑ Base Color    suffix: _color            │
│ ☑ Roughness     suffix: _rough             │
│ ☑ Normal       suffix: _normal            │
│ ☑ Metallic     suffix: _metal             │
├─────────────────────────────────────────────┤
│ [Advanced Settings]                        │
│ [Denoise] [Cage Settings] [Texel Density] │
├─────────────────────────────────────────────┤
│ [Save & Export]                           │
│ ☑ Apply to Scene  ☑ External Save        │
│ Path: [//textures/        ] [Browse]      │
├─────────────────────────────────────────────┤
│           [ BAKE ]    [ Quick Bake ]       │
└─────────────────────────────────────────────┘
```

### 1.2 环境健康检查

面板顶部的环境健康检查区域实时监控系统状态：

| 状态图标 | 含义 | 操作 |
|----------|------|------|
| ✓ 绿色 | 正常 | 无需操作 |
| ⚠ 黄色 | 警告 | 建议检查 |
| ✗ 红色 | 错误 | 需要修复 |

**检查项目**:
- **Addon Dependencies**: 验证导出插件 (FBX/GLB/USD) 是否启用
- **Path Validation**: 验证输出路径是否合法
- **UV Detection**: 检测对象是否包含 UV 层

---

## 第二章：任务管理

### 2.1 创建和管理任务

任务是保存和复用烘焙配置的容器。

**创建新任务**:
1. 点击 `+ Add` 按钮
2. 在任务列表中选择新创建的任务
3. 配置烘焙参数

**保存预设**:
1. 配置完所有参数后，点击 `Save`
2. 选择保存位置
3. 预设保存为 `.json` 文件，包含所有通道配置

**加载预设**:
1. 点击 `Load`
2. 浏览并选择预设文件
3. 参数自动加载到当前任务

### 2.2 One-Click PBR 设置

点击 `One-Click PBR Setup` 按钮，系统自动配置标准 PBR 烘焙通道：

- ✅ Base Color
- ✅ Roughness
- ✅ Normal
- ✅ Metallic
- ✅ Ambient Occlusion (可选)

自动设置推荐的后缀名，便于在 Substance Painter 等软件中自动识别。

---

## 第三章：对象管理

### 3.1 添加烘焙对象

**手动添加**:
1. 在 3D 视图中选择对象
2. 点击 `+ Add` 按钮
3. 对象添加到列表

**自动选择**:
1. 在 3D 视图中选择所有需要烘焙的对象
2. 点击 `Auto-Select`
3. 所有选中的对象自动添加到列表

### 3.2 智能对象诊断

对象列表实时显示诊断信息：

| 图标 | 含义 | 说明 |
|------|------|------|
| ✓ 绿色 | UV 正常 | 对象包含有效的 UV 层 |
| ⚠ 黄色 | 无 UV | 对象缺少 UV 层，需要添加 |
| ✗ 红色 | 错误 | 对象有问题，无法烘焙 |

**添加 UV**:
1. 选择缺少 UV 的对象
2. 在 3D 视图中按 `U` 键
3. 选择展 UV 方式 (Smart UV Project / Unwrap)

### 3.3 选择激活模式 (Select to Active)

用于高模烘焙低模的工作流：

1. 选择所有高模物体
2. 按住 `Shift` 并选择低模物体（作为激活对象）
3. 设置 `Bake Mode` 为 `Select to Active`
4. 烘焙

**优势**: 高模物体无需 UV 层，系统自动处理

---

## 第四章：通道配置

### 4.1 PBR 通道

| 通道 | 描述 | Blender 烘焙类型 |
|------|------|-----------------|
| Base Color | 基本颜色/Albedo | Diffuse |
| Roughness | 粗糙度 | Roughness |
| Metallic | 金属度 | Glossy ( Metallic ) |
| Specular | 高光 | Specular |
| Normal | 法线贴图 | Normal |
| Height | 高度贴图 | Displacement |
| Ambient Occlusion | 环境光遮蔽 | Ambient Occlusion |
| Emit | 自发光 | Emit |

### 4.2 网格通道

| 通道 | 描述 | Blender 烘焙类型 |
|------|------|-----------------|
| Curvature | 曲率 | Cursor to Depth |
| Normal | 顶点法线 | Normal |
| Position | 位置 | Position |
| UV | UV 坐标可视化 | UV |

### 4.3 ID 通道

| 通道 | 描述 | Blender 烘焙类型 |
|------|------|-----------------|
| Material ID | 材质 ID | Diffuse |
| Fac | 衰减 | Fac |

### 4.4 通道后缀

为每个通道配置输出文件的后缀：

| 通道 | 默认后缀 |
|------|----------|
| Base Color | `_color` |
| Roughness | `_rough` |
| Normal | `_normal` |
| Metallic | `_metal` |

### 4.5 自定义通道

支持创建自定义通道：

1. 点击 `+ Add Channel`
2. 选择通道类型
3. 配置后缀和参数
4. 拖动调整顺序

---

## 第五章：高级设置

### 5.1 笼子设置 (Cage Settings)

笼子是用于投影烘焙的中间壳体。

**模式**:
- **Uniform**: 统一挤出，所有面等距离挤出
- **Proximity**: 智能邻近度，自动分析高模与低模间距

**设置**:
- **Cage Extrusion**: 挤出距离 (默认 0.01)
- **Cage Offset**: 笼子偏移量
- **Cage Object**: 使用自定义笼子对象

### 5.2 笼子分析 (Cage Analysis)

点击 `Analyze Cage` 进行预烘焙诊断：

**热力图显示**:
- 🟢 绿色: 安全区域，烘焙正常
- 🔴 红色: 碰撞区域，可能产生瑕疵
- 🟡 黄色: 警告区域，建议检查

**分析报告**:
- 错误总数
- 重叠百分比
- 建议挤出距离

### 5.3 像素密度 (Texel Density)

定义目标像素密度，确保资产库质量一致。

**计算公式**:
```
Resolution = Texel Density × Object Size
```

**设置方法**:
1. 输入目标密度 (如 512 px/unit)
2. 系统自动计算推荐分辨率
3. 点击应用推荐值

### 5.4 降噪设置 (Denoise)

启用 Intel Open Image Denoise (OIDN) 进行后处理：

1. 勾选 `Denoise`
2. 选择降噪强度 (1-10)
3. 可选: 设置去噪后的锐化程度

**适用场景**:
- 低采样率快速预览
- 复杂光照烘焙
- 减少噪点

### 5.5 性能分析 (Performance Profiler)

烘焙完成后查看每个通道的性能数据：

| 指标 | 描述 |
|------|------|
| Bake Time | 计算耗时 |
| Save Time | 保存耗时 |
| Total Time | 总耗时 |
| Memory Peak | 内存峰值 |

---

## 第六章：保存与导出

### 6.1 应用到场景

勾选后，烘焙结果创建新物体并赋予材质：

**智能更新**:
- 如果场景中已存在该结果物体
- 系统直接更新其材质和网格
- 不重复创建物体，保持场景整洁

**命名规则**:
- 物体名: `{原物体名}_Baked`
- 材质名: `{原材质名}_Baked`

### 6.2 外部保存

勾选后，烘焙结果保存到磁盘：

**支持格式**:
- PNG (默认，推荐)
- JPEG
- EXR (32 位，支持 HDR)
- TIFF

**路径设置**:
- 支持绝对路径: `C:/textures/`
- 支持相对路径: `//textures/` (相对于 .blend 文件)

### 6.3 一键交付 (Zero-Friction Delivery)

自动导出烘焙结果为可立即使用的格式：

**支持格式**:
- **GLB/GLTF**: 用于 Web、Three.js、游戏引擎
- **USD**: 用于电影制作、DCC 软件

**工作流**:
1. 勾选 `Export Model`
2. 选择导出格式
3. 选择导出路径
4. 烘焙完成后自动执行导出

**PBR 材质自动封装**:
- 自动创建符合工业标准的 PBR 材质
- 自动连接所有烘焙贴图
- 可直接在 Substance、Unity、Unreal 中使用

---

## 第七章：快速烘焙

### 7.1 Quick Bake 功能

无需配置复杂任务，直接烘焙选中的对象：

1. 在 3D 视图中选择对象
2. 点击 `Quick Bake`
3. 使用当前激活任务的设置（或默认设置）开始烘焙

**特点**:
- **零副作用**: 使用内存代理执行，不修改当前任务设置
- **快速预览**: 适合快速检查烘焙效果
- **一键操作**: 无需切换面板

### 7.2 UDIM 烘焙

专为 UDIM 流程设计：

1. 确保模型使用 UDIM 格式 UV
2. 在列表中显示所有检测到的瓦片
3. 每个瓦片自动创建对应的图像
4. 一次性烘焙所有瓦片

---

## 第八章：实时预览

### 8.1 交互式预览

在烘焙前预览通道打包效果：

1. 勾选 `Preview Packing`
2. 在 3D 视图中实时查看 ORM 效果
3. 调整参数后自动更新预览

**支持通道**:
- Occlusion (R)
- Roughness (G)
- Metallic (B)

### 8.2 自动恢复

关闭预览后，系统自动恢复原始材质：

- 不保留临时着色器
- 不影响场景数据
- 100% 非破坏性

---

## 第九章：命令行与 API

### 9.1 无头烘焙 (Headless CLI)

在服务器或渲染农场中运行烘焙：

```bash
# 基本用法
blender -b project.blend -P headless_bake.py

# 指定任务
blender -b project.blend -P headless_bake.py -- --job "PBR_Job"

# 指定输出目录
blender -b project.blend -P headless_bake.py -- --output "C:/baked/"

# 组合参数
blender -b project.blend -P headless_bake.py -- --job "PBR" --output "C:/baked/"
```

### 9.2 Python API

在脚本中直接调用烘焙功能：

```python
import bpy
from baketool.core import api

# 基础烘焙
api.bake(
    objects=bpy.context.selected_objects,
    resolution=1024,
    channels=["color", "roughness", "normal"]
)

# 使用预设
api.bake_with_preset(
    objects=bpy.context.selected_objects,
    preset="C:/presets/pbr_standard.json"
)

# 高级用法
api.bake(
    objects=bpy.context.selected_objects,
    resolution=2048,
    channels=["color", "roughness", "normal", "metallic"],
    use_denoise=True,
    output_path="//textures/",
    export_format="GLB"
)
```

### 9.3 API 参考

| 函数 | 描述 | 参数 |
|------|------|------|
| `api.bake()` | 执行烘焙 | objects, resolution, channels, ... |
| `api.bake_with_preset()` | 使用预设烘焙 | objects, preset_path |
| `api.create_preview()` | 创建预览 | objects |
| `api.analyze_cage()` | 分析笼子 | context, low_obj, high_objs |

---

## 第十章：故障排查

### 10.1 崩溃恢复

如果 Blender 在烘焙过程中意外关闭：

1. 重新打开 Blender
2. 面板顶部显示红色警告框
3. 显示最后一次处理的物体和通道
4. 根据信息排查模型问题

### 10.2 紧急清理

如果场景中出现临时数据残留：

1. 按 `F3` (搜索)
2. 输入 `Clean Up Bake Junk`
3. 回车执行清理

**清理内容**:
- `BT_Bake_Temp_UV` - 临时 UV 层
- `BT_Protection_*` - 保护节点
- `BT_*` 图像 - 临时图像

### 10.3 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 法线贴图有接缝 | Color Space 设置错误 | 确保设为 `Non-Color` |
| 烘焙结果全黑 | 物体未选中或无 UV | 添加 UV 层并选中物体 |
| 链接资产崩溃 | 外部资产引用失效 | 解除链接或修复路径 |
| 内存不足 | 分辨率过高 | 降低分辨率或分块烘焙 |
| 导出失败 | 插件未启用 | 启用 glTF/USD 插件 |

### 10.4 性能优化

| 问题 | 优化方法 |
|------|----------|
| 烘焙太慢 | 使用 GPU 渲染、降低采样率 |
| 内存不足 | 分批烘焙、降低分辨率 |
| 预览卡顿 | 关闭实时预览、降低预览分辨率 |

---

## 附录 A: 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F3` | 搜索操作 (输入 `Bake` 快速访问) |
| `Ctrl + Shift + B` | 打开 BakeTool 面板 |
| `U` | 展 UV (在 UV Editor 中) |

---

## 附录 B: 文件结构

```
baketool/
├── __init__.py          # 插件入口
├── ops.py               # 操作符定义
├── ui.py                # UI 面板
├── property.py          # 属性定义
├── constants.py         # 常量
├── translations.py      # 翻译
├── state_manager.py     # 状态管理
├── preset_handler.py    # 预设处理
├── core/                # 核心模块
│   ├── api.py          # 公共 API
│   ├── engine.py       # 烘焙引擎
│   ├── image_manager.py # 图像管理
│   ├── node_manager.py # 节点管理
│   ├── uv_manager.py   # UV 管理
│   ├── shading.py     # 着色器工具
│   ├── cage_analyzer.py # 笼子分析
│   ├── common.py       # 通用工具
│   └── compat.py       # 版本兼容
├── automation/          # 自动化工具
│   ├── cli_runner.py   # CLI 测试入口
│   ├── multi_version_test.py # 跨版本测试
│   └── headless_bake.py # 无头烘焙
└── test_cases/          # 测试套件
    ├── suite_unit.py   # 单元测试
    ├── suite_memory.py # 内存测试
    └── ...
```

---

## 附录 C: 术语表

| 术语 | 描述 |
|------|------|
| UDIM | 多象限贴图系统，支持 1001, 1002, ... 瓦片 |
| Cage | 笼子，用于投影烘焙的中间壳体 |
| Texel Density | 像素密度，单位面积像素数 |
| PBR | 基于物理的渲染 |
| ORM | Occlusion + Roughness + Metallic 通道打包 |
| OIDN | Intel Open Image Denoise，降噪库 |

---

## 附录 D: 支持与反馈

- **问题反馈**: GitHub Issues
- **功能请求**: GitHub Discussions
- **文档纠错**: Pull Request

---

*用户手册版本 1.5.1*
*最后更新: 2026-04-17*
