# BakeTool Phase 3.1 & 3.2：从烘焙插件到资产交付中间件的跨越

本次开发根据既定架构设计与您的选择（`Principled BSDF 连通` 与 `可选的顶点色切入`），不仅完美实现了**GLB/USD零摩擦交付流水线**，更彻底落地了基于纯几何射线的**可视化包裹分析黑科技（Visual Cage Analysis）**以及防内存黑洞的**极致 GC 清理系统**。

---

## 🚀 重磅特性 1: “零摩擦”的一键资产交付 (Closed-Loop Exporter)

> [!TIP]
> 现在，游戏开发者不需要盯着 Blender 看了，SBT 直接吐出挂载好贴图的成品 `.glb` 资产！

### 发生了怎样的改变：
*   **解除逻辑捆绑**：在以前，如果要导出带贴图的模型，你必须激活 `Apply to Scene (应用到场景)`，这会永久污染你的本地工程。
*   **黑盒渲染通道**：现在，后台渲染引擎会在沙盒中**克隆出一个低模 -> 自动利用 Principled BSDF 连接生成的各类贴图 -> 打包进 .GLB -> 删除克隆体**。
*   **自动化测试护卫**：已经在 `autotests/suite_production_workflow.py` 埋入了 `test_full_gltf_export_loop`。系统每次都会模拟烘焙，并在系统级扫描 `.glb` 的体积与材质节点，验证内嵌纹理的完整度。

```yaml
# 新增的暴露 API:
export_textures_with_model: Boolean (Default: True) 位于 BakeJobSetting
```

---

## 🔍 重磅特性 2: 视觉包裹框探伤雷达 (Visual Cage Analysis)

> [!IMPORTANT]
> 这是我们拉开与普通 Blender 插件差距的核心功能！长达数小时的渲染将不再因为发现“漏缝、漏黑”而付诸东流。

### 核心运转逻辑 (`core/cage_analyzer.py`):
1.  构建目标高模组合的 `BVHTree` (无论它们有多少个修改器、镜像，都会被转换为 World Space 树结构并支持列表遍历追踪)。
2.  拾取活跃低模 (Active Object)，从其每一个表面顶点 (Vertices) 沿**反方向法线向内回溯射线**！距离限定为您设置的挤出容差 (`Extrusion`)。
3.  如果射线未找到物体，即代表“这片区域没有高模可以供投影”-> 即将产生烘烤破绽。

### 反馈给画师：
该层信息会被作为 `BYTE_COLOR` 被实时写入低模的数据缓冲中（兼容 Blender 3.2+ Color Attributes 及老版的 Vertex Colors），图层名为 `BT_CAGE_ERROR`。
由于您选择了**可选机制**，在开启 `auto_switch_vertex_paint` 的前提下，画师会立刻看到网格身上哪里有扎眼的**红色病变斑块**。

---

## 🛡️ 背景引擎特性 3: 显存刺客终结者 (VRAM Deep Guard)

在处理大量 UDIM（甚至 >20 个 4K Tile 的大炮塔模型）时，Blender Python 的软回收是来不及的。

### 拦截级别实现：
我们将拦截网格架设在了 `execution.py` 内部 `_process_single_step` 执行期的最末端。
当该帧 (单物体一类别贴图) 处理且硬盘持久化完毕后，拦截器会直接对底层调用：
```python
img.gl_free()
if hasattr(img, 'buffers_free'):
    img.buffers_free()
```
从而以 C++ 级直接扯断与 VRAM 显存的羁绊，彻底抹平内存的激进波峰，为即将到来的 100+ 模型批量渲染奠定了稳定性基石。

---

## 💡 下一步：您的审查与部署
目前，所有的接口、代码引擎与测试节点都已完备。
您可以：
1. 打开 Blender，前往 BakeTool 的 `Smart Intelligence` 栏目，现在那里会出现 **[🔍 Analyze Cage Overlap]** 按钮。
2. 配置好 `export_textures_with_model` 并运行一键 Bake -> Export，去您的临时目录检查 `.glb` 是否开箱即用。
