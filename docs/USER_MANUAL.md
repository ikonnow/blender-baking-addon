# BakeTool User Manual

This document is for plugin end-users.

> [!WARNING]
> **Risk Notice**: BakeTool is an experimental tool heavily reliant on AI-assisted generation, currently maintained by a single person, and **seriously lacks real-world production stress testing**. Please read Section 12 of this manual for detailed limitations.

## 1. Plugin Positioning and Scope

BakeTool aims to organize the most error-prone and time-consuming parts of texture baking in Blender into a workflow. Currently, it functions more like a **proof-of-concept (PoC)**.

- Low-poly object base texture output
- High-poly to low-poly Selected-to-Active baking
- Multi-object batch processing
- Multi-material split baking
- UDIM asset texture processing
- Node result baking
- Custom channels and channel packing
- Post-bake model and texture export

It does not attempt to replace Blender's native material system, nor will it automatically understand the semantics of all your custom node networks. BakeTool's principle is to automate processes that are "clearly determinable and stably verifiable", while leaving parts with "high project variance and inference cost" to explicit user configuration.

## 2. Installation and Basic Access

### 2.1 Installation

You can install from a ZIP package or use the source directory directly as the plugin directory. Either way, you need to enable BakeTool in Blender's `Edit > Preferences > Add-ons`.

### 2.2 Interface Location

Main panel located at:

- `3D View > N Panel > Baking`

Auxiliary panels located at:

- Result browsing related panels
- `Image Editor` result viewing area
- `Node Editor` node baking panel

## 3. Core Concepts

### 3.1 Job

Job is BakeTool's basic working unit. A Job saves a complete baking configuration, including:

- Object selection and mode
- Resolution and sampling
- Enabled baking channels
- Output path and image format
- Channel packing settings
- Custom map configuration
- Export integration options
- Animation and naming rules

If your project has character, scene asset, and prop categories, the most direct approach is often not modifying one Job repeatedly, but creating a Job for each category and saving them as presets separately.

### 3.2 Bake Mode

BakeTool currently revolves around several core modes:

- `SINGLE_OBJECT`: Single object or regular object collection baking
- `COMBINE_OBJECT`: Combined object results
- `SELECT_ACTIVE`: High-poly to low-poly Selected-to-Active workflow
- `SPLIT_MATERIAL`: Split results by material
- `UDIM`: UDIM tile-based baking workflow

Mode affects execution queue construction, object context, target image naming, and export behavior, so it's recommended to determine the mode first, then select channels.

### 3.3 Channel

Channel refers to a single texture output that needs to be produced, such as color, roughness, normal, AO, Combined, or custom maps. BakeTool ultimately converts these channels into execution steps, preparing images, node context, and save logic for each step.

### 3.4 Custom Maps

Custom maps are a key capability of BakeTool. You can extract a channel from existing bake results, or specify sources per R/G/B/A to assemble new grayscale or RGBA images. The current version has connected this pipeline to the execution engine, so custom maps can be generated and also participate in channel packing.

## 4. Main Panel Structure

The 3D View main panel is roughly divided into four blocks:

- `SETUP & TARGETS`
- `BAKE CHANNELS`
- `OUTPUT & EXPORT`
- `CUSTOM MAPS`

The panel top also contains preset, task management, and environment check information; the bottom is the start baking entry. The recommended usage order is top to bottom.

### 4.1 Job Management Area

This manages Job creation, deletion, switching, saving, and loading. Recommended workflow:

1. Create a new Job first.
2. Immediately rename it to something meaningful.
3. Configure the most commonly used channels and output format.
4. Then save as a preset.

This way, subsequent new scenes only need to load presets instead of starting from zero.

### 4.2 One-Click PBR

`One-Click PBR` serves to quickly enable a basic, common PBR set. The current implementation only enables:

- `Base Color`
- `Roughness`
- `Normal`

This is important because older documentation described it as also enabling metallic and AO, which is inconsistent with current code. If your project needs metallic, AO, Emission, Alpha, or other layers, please manually check them in `BAKE CHANNELS`.

### 4.3 SETUP & TARGETS

This section determines "what gets baked, how it's organized, result size, and execution context". Usually includes:

- Target object list
- Bake type or working mode
- Resolution
- Sampling and margin
- Target object and active object
- UV-related strategies
- Cage and extrusion
- UDIM behavior

It's recommended to confirm objects and mode first, then adjust sampling. Many issues that look like "texture errors" are actually wrong mode selection or incorrect object context.

The current version also checks whether objects, active object, and cage object are in the current `View Layer` before actual execution. If an object is excluded from the current view layer, BakeTool will skip that Job directly and write a clear log, rather than waiting until Blender's native bake stage to throw a hard-to-locate runtime error.

### 4.4 BAKE CHANNELS

This section determines "which specific maps to output". Think of it as a channel list where each channel may have its own settings. Common combinations in real projects:

- Color: Base Color, Emission
- Surface properties: Roughness, Metallic, Specular
- Normal and geometric aids: Normal, AO, etc.
- Lighting: Combined, Diffuse, Glossy, Transmission

For lighting or Combined types, the current version's pass filter options actually pass through to Blender's bake settings. That means direct, indirect, color switches you see in the interface are no longer decorative—they actually affect results.

### 4.5 OUTPUT & EXPORT

This section handles result saving and export integration. Configurable items include:

- Whether to save externally
- Save directory
- File naming and suffix
- Color space
- Image format, bit depth, quality, compression codec (e.g., EXR/TIFF specific options)
- Color space
- Animation frame output
- Channel packing
- Whether to export models
- Model format and whether to include textures

If you enable export, BakeTool will call the corresponding export logic after execution. The current version has fixed visibility pollution issues during export—`hide_set()` and `hide_viewport` are restored after completion.

### 4.6 CUSTOM MAPS

This is for creating custom maps. Key points when configuring:

- Output type is grayscale or RGBA
- Which component comes from which baked result
- Whether to extract single channel
- Whether to invert
- **Default Value**: When "Use Map" is disabled, you can customize the fill value for that channel (e.g., AO/Metallic default 1.0)
- Whether to output black and white

> [!TIP]
> **Self-reference Protection**: Current version automatically filters out the channel itself. For example, you cannot select "MaskA" again as the R source in "MaskA", effectively avoiding logical dead loops.

If channel packing uses custom maps, it's recommended to first confirm custom map names are stable, because packing sources use the `BT_CUSTOM_<name>` normalized result key.

## 5. Standard Operating Procedures

### 5.1 Single Object Baking

Suitable for scenarios with clear low-poly targets that only need standard maps.

1. Create new Job.
2. Add target objects.
3. Select `SINGLE_OBJECT`.
4. Set resolution and save path.
5. Select common channels, e.g., color, roughness, normal.
6. Check materials and UVs.
7. Execute.

For quick start, you can click `One-Click PBR` first, then fine-tune.

### 5.2 High-Poly to Low-Poly Baking

Suitable for transferring high-poly detail to low-poly textures.

1. Prepare high-poly and low-poly in scene.
2. Confirm low-poly is the active object.
3. Select `SELECT_ACTIVE`.
4. Set cage-related parameters.
5. Enable normal, AO, color, and other needed channels.
6. Adjust extrusion or cage based on results.

If you find normal edges intersecting, AO pollution, or detail loss, first check object normals, UV, cage, and sampling before considering texture settings.

### 5.3 Multi-Material Split

When an object needs to be split by material for output, use `SPLIT_MATERIAL`. This mode is commonly used for complex assets or before exporting to game engines that need texture management by material slot. It's recommended to unify naming rules and output directories in advance, otherwise later organization costs will increase significantly.

### 5.4 UDIM Workflow

The key to UDIM workflow is not "can it bake", but whether tile detection, naming, and result organization are stable. Recommended order:

1. Confirm object UV is organized by UDIM.
2. Use `UDIM` mode.
3. Select appropriate `udim_mode`, e.g., auto-detect or custom.
4. If object list changes, use the refresh UDIM locations feature to resync.
5. Confirm output filename and tile matching before export.

### 5.5 Animation Frame Sequence Baking

BakeTool supports frame-by-frame texture output. Configuration includes:

- Whether to enable animation baking
- Whether to use custom frame range
- Start frame and duration
- Start number
- Number padding
- Frame separator

This is suitable for per-frame changing caches or special procedural effects, but significantly increases time and disk usage. Before releasing assets, it's recommended to do a smoke test with a short frame range first.

### 5.6 Node Baking

If you just want to bake current node output directly instead of going through the whole object-level channel configuration, you can use the node baking feature in the Node Editor panel. The current version has completed the corresponding operator; interface buttons are consistent with registration status.

Usage notes:

- Requires active object and active material
- Requires currently active node
- Node baking output path and image parameters are controlled by node baking settings

## 6. Output and Naming Recommendations

### 6.1 Path Strategy

If the project is saved, prefer using a dedicated output folder under the project directory. If the current `.blend` is not yet saved, BakeTool will fall back to temp directory in some path logic, but it's not recommended to rely on this behavior long-term for formal assets.

### 6.2 Color Space

Normal, roughness, metallic, AO, and other data maps should generally use non-color data. The current version has added color space mapping logic that correctly maps internal enum values to Blender's actual supported colorspace names, e.g.:

- `NONCOL` corresponds to `Non-Color`
- `SRGB` corresponds to `sRGB`
- `LINEAR` tries to match available linear color spaces

If switching between different Blender versions, it's recommended to always check that key data maps land in the correct color space.

### 6.3 Channel Packing

Channel packing is suitable for combining multiple data maps into a single texture, e.g., common ORM or other custom combinations. Recommended prerequisites:

- Source maps have consistent sizes
- All are finalized results
- Color space requirements are clear
- Downstream engine or DCC pipeline actually needs packed textures

If packing includes custom maps, confirm sources come from latest generated results, not old filenames or temp caches.

## 7. Presets and Reuse

BakeTool's preset system serializes Job-related properties and supports some migration compatibility. Suggested usage:

- Save "project template-level" configurations as presets
- Don't mix temporary states with strong dependencies on specific object names into general presets
- After plugin upgrade, first load old presets in a test scene to verify results

If preset loading partially fails to restore fields, there are usually three causes:

- Property renamed without hitting migration mapping
- Some fields are read-only or runtime fields, not participating in save
- Target objects, materials, images, and other Blender IDs no longer exist in current scene, cannot be resolved by name/library path

## 8. State Recovery and Interruption Handling

BakeTool uses `state_manager.py` to write last execution state to the system temp directory, filename:

```text
sbt_last_session.json
```

It records:

- Job name
- Total steps
- Current step
- Queue index
- Current object
- Current channel
- Last error

If Blender crashes or the process is interrupted, after reopening the interface you can decide whether to recover or clean state based on UI prompts. Recovery doesn't mean "continue from any internal detail", but rather reasonable continuation based on recorded execution position. Therefore, for key production tasks, it's still recommended to keep intermediate results and scene backups.

## 9. Headless and Scripted Usage

### 9.1 Background Baking

```bash
blender -b scene.blend -P automation/headless_bake.py -- --job "PBR_Job"
blender -b scene.blend -P automation/headless_bake.py -- --output "C:/baked"
blender -b scene.blend -P automation/headless_bake.py -- --job "PBR_Job" --output "C:/baked"
```

### 9.2 Usage Limitations

- Headless script won't create new Jobs for you
- `.blend` must already have BakeTool job configuration saved
- If `--job` is not specified, it runs all enabled Jobs
- `--output` overrides Job's external save directory and automatically enables external saving

### 9.3 API Usage

For other scripts or plugin integration, you can use the entry points provided by `core/api.py`:

- `bake(objects, use_selection=True)`
- `get_udim_tiles(objects)`
- `validate_settings(job)`

These entry points are more suitable for pipeline integration or custom automation than directly driving UI operators.

## 10. Common Issues and Troubleshooting

### 10.1 Button clicks don't respond or operator errors

Current version has fixed known missing operator issues. If errors still occur, first check:

- Whether plugin is latest directory
- Whether Blender loaded old cache
- Whether multiple plugins with same name exist

### 10.2 Background mode says BakeTool properties not found

Using current version's `automation/headless_bake.py`, this should be fixed. If still occurring:

- Confirm script path is under `automation/`
- Confirm repo directory can be imported by Python as `baketool`
- Confirm job configuration actually exists in `.blend` file

### 10.3 Console says object not in current View Layer

This is usually not the engine "randomly failing", but at least one object in current Job is not in your current `View Layer`. First check:

- Whether target objects are visible in current view layer and not excluded
- Whether low-poly target in `SELECT_ACTIVE` mode is still in current view layer
- Whether cage object is also in the same view layer

Current version skips such Jobs directly at enqueue stage and avoids generating half-finished or leftover images.

### 10.4 Normal map colors are wrong

First check:

- Whether image color space is `Non-Color`
- Whether target material correctly uses normal map nodes
- Whether high-low direction and cage are reasonable

### 10.5 Selected custom map in channel packing but results abnormal

Current version has fixed custom map packing key inconsistency. If still abnormal, check:

- Whether custom map was successfully generated
- Whether custom map name was modified after generation
- Whether packing source still points to old name

### 10.6 Object visibility changes after export

Current version has restored `hide_viewport` and `hide_set()`. If scene state still changes, it usually means export process was abnormally interrupted. First check console errors, then confirm whether other plugins are simultaneously modifying object visibility.

### 10.7 Long wait after clicking Run Safety Audit

`Run Safety Audit` now launches an independent background Blender process to run tests, then writes summary back to current interface. This avoids running full test suites in interactive sessions that would corrupt RNA data currently referenced by the UI.

If you wait tens of seconds after clicking, this is normal. What really matters:

- Whether a test summary is eventually returned
- Whether there are failure/error counts
- Whether current session remains operable, not messed up by test process

## 11. Usage Recommendations

- Before first production asset use, run full workflow in a small test scene.
- Make commonly used project templates into presets to reduce manual selection.
- Uniform color space and naming rules for data maps.
- For animation, UDIM, multi-object merging, and other high-cost workflows, do small sample validation first.
- Keep `.blend` backups and intermediate outputs for key projects; don't treat "plugin can recover" as primary insurance.

## 12. Known Limitations and Production Risks (Critical)

Since this project is currently **single-maintainer** and heavily uses **vibecode (AI) development flow**, users must be aware of the following boundaries:

1. **Tests ≠ Reality**: 150+ automated tests mainly cover standard geometry and basic PBR materials. Faced with complex Geometry Nodes, deeply nested Shader groups, or extremely large scene files, the plugin may crash or produce incorrect results due to AI-generated logic gaps.
2. **UI refresh delays**: In some Blender 4.5/5.0 pre-release versions, dynamic list refresh may have delays.
3. **Export addon dependencies**: Export integration heavily depends on third-party FBX/GLB plugin stability. If these built-in addons change, BakeTool's export chain may break.
4. **Performance bottlenecks**: Batch processing for massive object quantities has not yet undergone memory limit stress testing.
5. **Recovery mechanism limitations**: `state_manager.py` crash recovery is "best-effort", cannot guarantee perfect restoration of all unsaved scene states after hard crash.

**Final Recommendation**: BakeTool is currently your "second choice". In the final delivery phase of critical projects, please reserve manual baking time as backup.

---

## Conclusion

BakeTool's value lies in using AI to empower individual developers with efficient tool development models. As long as you maintain a **cautiously optimistic** attitude and follow the **scene backup** principle, it will become a sharp blade for exploring Blender baking automation. But remember, it is still a "work in progress".
