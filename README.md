# BakeTool

BakeTool is a professional texture baking suite for Blender.

> [!CAUTION]
> **Project Disclaimer**
>
> 1. **Development Context**: This project is currently maintained by **lastraindrop** in spare time. Code logic heavily relies on **vibecode (AI-assisted development)**. While 150+ automated tests pass, AI-generated code may have unpredictable behavior in extreme edge cases or complex production environments.
>
> 2. **Stability Status**: BakeTool is in **early verification stage (Experimental Prototype)**. It performs well in lab environments but seriously lacks large-scale production validation.
>
> 3. **Core Warning**: **"All tests pass, production fails" is very likely.** It is far from production-grade stability.
>
> 4. **Usage Recommendation**: **Backup your .blend scenes before production use.** Developer assumes no liability for data loss.

---

## Current Position

- Professional texture baking tool for Blender 3.3 to 5.x
- Supports Single Object, Selected-to-Active, UDIM and more
- Built-in batch jobs, non-destructive workflow and automation

## Core Features

- **Non-Destructive Workflow**: Automatically create and clean temporary images, nodes, and context states
- **Batch Jobs**: Maintain multiple Bake Jobs in one scene
- **Multiple Target Modes**: Single Object, Combined, Selected-to-Active, Split Material, UDIM
- **Channel Control**: PBR, Lighting, Auxiliary and Custom Maps
- **Channel Packing**: Multiple bakes to one RGBA texture
- **Custom Maps**: Assemble grayscale or RGBA from channel sources
- **Node Baking**: Bake directly in Node Editor
- **Export Integration**: FBX, GLB, USD export
- **Crash Recovery**: state_manager.py records incomplete tasks
- **Automation**: CLI suite, cross-version verification

## Version & Compatibility

| Item | Value |
|------|-------|
| Plugin Version | `1.0.0` |
| Manifest | `blender_manifest.toml` (Extensions) |
| Min Version | Blender 4.2.0+ (Extensions) / 3.3.0 (Legacy) |
| Tested Versions | 3.3.21, 3.4.1, 3.5.1, 3.6.23, 4.0.2, 4.1.1, 4.2.14, 4.3.2, 4.4.3, 4.5.3, 5.0.1, 5.1.0 |

## Installation

### From Release Package

1. Download release ZIP
2. Blender: `Edit > Preferences > Add-ons` → `Install...`
3. Select ZIP → `Install Add-on`
4. Enable BakeTool

### From Source

1. Put repo in Blender add-ons folder
2. Directory must be named `baketool`
3. Access via `3D View > Sidebar > Baking` after enabling

## Quick Start

1. Open `3D View`, find `Baking` panel in Sidebar
2. Create new Job
3. SETUP & TARGETS: Specify object, mode, resolution
4. BAKE CHANNELS: Select channels
5. OUTPUT & EXPORT: Output path, image format
6. CUSTOM MAPS: (Optional) Add custom maps
7. START BAKE PIPELINE
8. Check results in Image Editor

For quick PBR textures, use `One-Click PBR` (enables Base Color/Roughness/Normal).

## Typical Workflows

### Single Object

For low-poly with target material.
- Create Job → Select SINGLE_OBJECT → Set resolution → Select channels → Run

### Selected-to-Active

For high-poly to low-poly baking.
- Prepare high+low → Select SELECT_ACTIVE → Set cage → Run

### Split Material & UDIM

- Multi-material: SPLIT_MATERIAL
- UDIM assets: UDIM mode

### Custom Maps & Packing

Generate new maps from existing, pack to RGBA.

### Node Baking

Activate node in Editor → Bake via node panel

## Automation & Verification

### CLI Test Entry

```bash
# Unit tests
blender -b --factory-startup --python automation/cli_runner.py -- --suite unit

# Verification tests
blender -b --factory-startup --python automation/cli_runner.py -- --suite verification

# Integration tests
blender -b --factory-startup --python automation/cli_runner.py -- --category integration
```

### Cross-Version Verification

```bash
python automation/multi_version_test.py --verification
python automation/multi_version_test.py --suite unit
python automation/multi_version_test.py --list
```

### Headless Baking

```bash
blender -b scene.blend -P automation/headless_bake.py -- --job "JobName"
blender -b scene.blend -P automation/headless_bake.py -- --output "C:/baked"
```

> Note: `headless_bake.py` auto-registers plugin. Requires saved Job config in .blend.

## Documentation

- [User Manual](docs/USER_MANUAL.md) - Complete usage instructions
- [Developer Guide](docs/dev/DEVELOPER_GUIDE.md) - Architecture and extension points
- [Automation Reference](docs/dev/AUTOMATION_REFERENCE.md) - Test entry points
- [Ecosystem Guide](docs/dev/ECOSYSTEM_GUIDE.md) - Repository structure
- [Standardization Guide](docs/dev/STANDARDIZATION_GUIDE.md) - Coding standards
- [Roadmap](docs/ROADMAP.md) - Future directions
- [Task Board](docs/task.md) - Task status
- [Changelog](CHANGELOG.md) - Version changes

## Repository Structure

```
baketool/
  automation/       Automation entries
  core/             Execution engine
  docs/             Documentation
  test_cases/       Test suites
  __init__.py       Entry point
  ops.py            Operators
  property.py       Properties
  ui.py             UI layout
  constants.py      Constants
  preset_handler.py Presets
  state_manager.py  State management
```

## License

GPL-3.0-or-later - See [LICENSE](LICENSE) file.