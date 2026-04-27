# BakeTool

Professional texture baking suite for Blender.

> [!CAUTION]
> **Project Disclaimer**
>
> This is a fork maintained by **ikonnow**. While 150+ automated tests pass, it's in **early verification stage (Experimental Prototype)**. Backup your .blend scenes before production use.

---

## Installation

Download release ZIP and drag into Blender, or install via `Edit > Preferences > Add-ons`. Find the `Baking` panel in the 3D Viewport sidebar.

## Quick Start

1. Open `3D View`, find `Baking` panel in Sidebar
2. Create new Job
3. SETUP & TARGETS: Specify object, mode, resolution
4. BAKE CHANNELS: Select channels
5. OUTPUT & EXPORT: Output path, image format
6. CUSTOM MAPS: (Optional) Add custom maps
7. START BAKE PIPELINE
8. Check results in Image Editor

## Typical Workflows

### Single Object

For low-poly with target material:
- Create Job → Select SINGLE_OBJECT → Set resolution → Select channels → Run

### Selected-to-Active

For high-poly to low-poly baking:
- Prepare high+low → Select SELECT_ACTIVE → Set cage → Run

### Split Material & UDIM

- Multi-material: SPLIT_MATERIAL
- UDIM assets: UDIM mode

### Custom Maps & Packing

Generate new maps from existing, pack to RGBA.

### Node Baking

Activate node in Editor → Bake via node panel.

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

### Headless Baking

```bash
blender -b scene.blend -P automation/headless_bake.py -- --job "JobName"
blender -b scene.blend -P automation/headless_bake.py -- --output "C:/baked"
```

> Note: `headless_bake.py` auto-registers plugin. Requires saved Job config in .blend.

## Features

- Non-destructive workflow with auto-cleanup
- Batch jobs in one scene
- Target Modes: Single Object, Combined, Selected-to-Active, Split Material, UDIM
- Channel Control: PBR, Lighting, Auxiliary, Custom Maps
- Channel Packing: Multiple bakes to one RGBA texture
- Export Integration: FBX, GLB, USD export
- Crash Recovery

## Compatibility

- Version: `1.0.0`
- Blender: 4.2.0+ (Extensions) / 3.3.0 (Legacy)
- Tested: 3.3-5.1

## Documentation

- [User Manual](docs/USER_MANUAL.md) - Complete usage instructions
- [Developer Guide](docs/dev/DEVELOPER_GUIDE.md) - Architecture and extension points
- [Automation Reference](docs/dev/AUTOMATION_REFERENCE.md) - Test entry points
- [Ecosystem Guide](docs/dev/ECOSYSTEM_GUIDE.md) - Repository structure
- [Standardization Guide](docs/dev/STANDARDIZATION_GUIDE.md) - Coding standards
- [Roadmap](docs/ROADMAP.md) - Future directions
- [Task Board](docs/task.md) - Task status
- [Changelog](CHANGELOG.md) - Version changes

## License

GPL-3.0-or-later - See [LICENSE](LICENSE) file.
