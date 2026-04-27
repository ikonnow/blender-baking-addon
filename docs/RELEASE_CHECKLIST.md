# BakeTool Release Checklist

This document is for final verification before official packaging and release. Its value is not in "looking professional", but in fixing the items most easily forgotten yet directly impacting user first impressions and subsequent maintenance costs. It is recommended to actually go through this each release, rather than verbally assuming it's complete.

## 1. Version and Metadata

- Confirm `bl_info` version in `__init__.py` is correct
- Confirm `version`, `blender_version_min`, `website` in `blender_manifest.toml` are correct
- Confirm `README.md`, `CHANGELOG.md` match current version number
- Confirm `doc_url` and `tracker_url` no longer use placeholder addresses

## 2. Repository Cleanliness

- Delete or ignore temporary files not needed for this release
- Confirm no residual `__pycache__`, `test_output` or other runtime directories
- Confirm workspace has no residual `blender.crash.txt`, `crash_log.txt`, temporary screenshots, or similar one-time debug files
- Confirm local temporary validation scripts are not accidentally included in release
- Confirm latest validation reports are archived, old temporary reports cleaned or ignored
- Confirm old `dist/` artifacts cleaned or prepared for regeneration, avoid mistakenly treating expired ZIP as this release artifact

## 3. Documentation Sync

- `README.md` consistent with current actual functionality
- `docs/USER_MANUAL.md` consistent with current UI, workflows, limitations
- `docs/dev/DEVELOPER_GUIDE.md` consistent with current core architecture and extension points
- Commands and script names in `docs/dev/AUTOMATION_REFERENCE.md` can be run directly
- Constraints on parameter consistency, dynamic UI alignment, and test isolation in `docs/dev/STANDARDIZATION_GUIDE.md` match current code
- `docs/ROADMAP.md` and `docs/task.md` reflect true phase status, without distorted descriptions
- `CHANGELOG.md` records key fixes included in this release

## 4. Automation Validation

At least complete the following validations:

- `unit`
- `export`
- `ui_logic`
- `verification`
- `production_workflow`

Recommended commands:

```bash
blender -b --factory-startup --python automation/cli_runner.py -- --suite unit
blender -b --factory-startup --python automation/cli_runner.py -- --suite export
blender -b --factory-startup --python automation/cli_runner.py -- --suite ui_logic
blender -b --factory-startup --python automation/cli_runner.py -- --suite verification
blender -b --factory-startup --python automation/cli_runner.py -- --suite production_workflow
```

If the runtime environment restricts temp directory writing, explicitly point `TEMP` and `TMP` to writable directories in the workspace before running end-to-end suites.

If this change touches the following areas, also run corresponding suites:

- Input validation, View Layer, failure cleanup, exception paths: `negative`
- Translation extraction, dictionary rewrite, multilingual display: `localization`

## 5. Cross-Version Validation

At least execute:

```bash
python automation/multi_version_test.py --verification
```

Recommended minimum coverage:

- Blender `3.3.x`
- Blender `3.6.x`
- Blender `4.2 LTS`
- Blender `4.5 LTS`
- Blender `5.0.x`

If a version cannot run, don't just record "failed", also record whether it's:

- Path doesn't exist
- Environment incomplete
- Plugin compatibility issue
- Automation script issue

## 6. Feature Smoke Testing

Before official release, recommended to manually run through:

- Install ZIP and enable plugin
- Create new Job and execute single object basic baking
- Selected-to-Active baking
- Custom map generation and channel packing
- UDIM mode basic validation
- Node baking
- Export integration
- Crash recovery prompts and cleanup entry
- `Run Safety Audit` returns isolated test summary without messing up current interactive session
- headless CLI runs saved Job

## 7. Output Correctness Verification

- Data map color spaces correct, especially normal, roughness, metallic, AO
- Custom maps generate correctly, not pure black or blank error results
- Channel packing reads latest results, not old cache or wrong keys
- Object `hide_viewport` and `hide_set()` states correctly restored after export
- When object not in current View Layer, Job is explicitly skipped instead of crashing at Blender native bake stage

## 8. Distribution Package Contents

- Package contains Python source files and necessary user documentation for plugin runtime
- Package does not contain automation tests, development scripts, or historical archive materials
- `MANIFEST.in` consistent with current directory structure
- Plugin directory structure directly recognizable in Blender

Recommended to use repository script to generate distribution package, not manual compression of entire workspace:

```bash
python automation/build_release_zip.py
```

This stably excludes `.venv/`, `test_output/`, `docs/legacy/`, `automation/`, `dev_tools/`, and `test_cases/` and other local or development-period content.

## 9. Release Notes

Public release notes should at least contain:

- Supported Blender version range
- Key fixes in this version
- Known limitations
- Recommended first-time usage
- Issue feedback entry

If this version has behavioral changes users need to pay special attention to, such as `One-Click PBR` only enabling three base maps, this should also be clearly stated in release notes.

## 10. Post-Release First-Round Observation

Even if everything passed before release, recommended to immediately watch after release:

- Installation feedback
- Headless usage feedback
- Large scene, many objects, and export integration failures
- Old preset compatibility issues
- Color space differences under different Blender minor versions

The conclusion is simple: true release quality depends not only on "this run passed locally", but on treating validation, documentation, packaging, and manual acceptance as standard actions every release, not improvisation.
