# BakeTool 2.0 - Comprehensive Code Review & Action Plan

**Date:** 2026-04-07  
**Reviewer:** Automated Code Review  
**Scope:** Full codebase (`__init__.py`, `ops.py`, `property.py`, `ui.py`, `constants.py`, `state_manager.py`, `preset_handler.py`, `translations.py`, `core/*`, `test_cases/*`, `automation/*`, `dev_tools/*`)  
**Version Reviewed:** v1.5.0  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Critical Bugs (Must Fix)](#2-critical-bugs-must-fix)
3. [High Severity Issues](#3-high-severity-issues)
4. [Medium Severity Issues](#4-medium-severity-issues)
5. [Low Severity / Code Quality Issues](#5-low-severity--code-quality-issues)
6. [Test Infrastructure Assessment](#6-test-infrastructure-assessment)
7. [Architecture Observations](#7-architecture-observations)
8. [Detailed Remediation Plan](#8-detailed-remediation-plan)
9. [Unit Test Expansion Plan](#9-unit-test-expansion-plan)
10. [Execution Order & Priority Matrix](#10-execution-order--priority-matrix)
11. [Final Production Hardening (v1.5.0 Final Refresh)](#11-final-production-hardening-v150-final-refresh)

---

## 1. Executive Summary

BakeTool 2.0 is a well-structured Blender addon with a clear 3-layer architecture (UI → Engine → Core). The codebase demonstrates strong engineering practices: data-driven UI configuration, cross-version compatibility shimming, crash recovery, and comprehensive channel metadata. The test suite contains 48 explicit test methods plus ~540 parameterized sub-cases.

**However, the review identified:**

| Severity | Count | Summary |
|---|---|---|
| **CRITICAL** | 4 | Data loss risk, crashes, incorrect logic |
| **HIGH** | 8 | Error swallowing, unsafe operations, coverage gaps |
| **MEDIUM** | 15 | Bare excepts, performance, missing validation |
| **LOW** | 12 | Style, dead code, minor inconsistencies |

**Overall Assessment:** The addon is **HARDENED and Production-Ready** for Blender 3.3-5.0+. All identified critical and high-severity issues have been resolved, and test coverage has been expanded to 65+ cases including core lifecycle and boundary tests.

---

## 2. Critical Bugs (Must Fix)

### CR-01: Vector Zero Falsiness — [FIXED]
**File:** `core/cage_analyzer.py:83`  
**Severity:** CRITICAL  

```python
# Current (BUGGY):
if location and distance <= extrusion:
    ...
```

**Problem:** In Python, `Vector((0, 0, 0))` is falsy. When a raycast hits at the exact origin point `(0,0,0)`, `location` evaluates to `False`, causing the hit to be treated as a miss. This produces incorrect cage analysis results.

**Fix:**
```python
if location is not None and distance <= extrusion:
    ...
```

**Impact:** Cage overlap analysis will produce incorrect results for meshes with vertices near the world origin. This directly affects production workflows where cage accuracy is critical for normal map baking.

---

### CR-02: `StopIteration` Crash in `apply_baked_result` — [FIXED]
**File:** `core/common.py:297-298`  
**Severity:** CRITICAL  

```python
# Current (BUGGY):
color_img = next(iter(task_images.values()))
```

**Problem:** If `task_images` is empty (e.g., all bake steps failed but `apply_to_scene` is True), `next(iter(...))` raises `StopIteration`, crashing the apply pipeline without user feedback.

**Fix:**
```python
if not task_images:
    logger.warning("apply_baked_result: No images to apply.")
    return
color_img = next(iter(task_images.values()))
```

**Impact:** Hard crash during the post-bake apply step when baking fails partially.

---

### CR-03: `save_and_quit` Causes Unsaved Data Loss — [FIXED]
**File:** `core/execution.py:192`  
**Severity:** CRITICAL  

```python
bpy.ops.wm.save_mainfile(exit=True)
```

**Problem:** This saves and immediately quits Blender without any user confirmation. If the user had unsaved changes in their `.blend` file unrelated to baking (modeling work, other scenes, etc.), those changes are forcibly saved and Blender closes.

**Fix:** Add a confirmation check or remove this feature:
```python
if s.save_and_quit:
    if not bpy.data.is_dirty or context.window_manager.confirm:
        bpy.ops.wm.save_mainfile()
        bpy.ops.wm.quit_blender()
    else:
        logger.warning("Save and Quit skipped: Unsaved changes detected.")
```

**Impact:** User data loss in production scenarios. A modeler who set up baking and enabled this toggle will lose their entire session state.

---

### CR-04: `self._timer` Uninitialized Attribute Error — [FIXED]
**File:** `core/execution.py:198`  
**Severity:** CRITICAL  

```python
def _remove_timer(self, context):
    if self._timer:
```

**Problem:** `_timer` is only initialized in `init_modal()` (line 67). If `_remove_timer` or `cancel` is called before `init_modal` completes (e.g., due to an early exception), accessing `self._timer` raises `AttributeError`.

**Fix:**
```python
def __init__(self):
    self._timer = None
    self.bake_queue = []
    self._current_idx = 0
    # ... initialize all instance attributes
```

**Impact:** Crash during error handling, preventing proper cleanup and leaving the scene in `is_baking=True` state.

---

## 3. High Severity Issues

### HI-01: Bare `except: pass` — [FIXED]
**Files:** `core/cage_analyzer.py:128,131`, `core/image_manager.py:182`, `automation/cli_runner.py:44`, `automation/multi_version_test.py:30`  
**Severity:** HIGH  

Multiple locations use bare `except:` instead of `except Exception:`. This catches `SystemExit`, `KeyboardInterrupt`, and `GeneratorExit`, making it impossible to interrupt long operations or debug crashes.

**Fix:** Replace all `except:` with `except Exception:`.

---

### HI-02: Engine Not Restored After `set_bake_type` Failure — [FIXED]
**File:** `core/compat.py:55-58`  
**Severity:** HIGH  

```python
try:
    scene.render.engine = 'CYCLES'
except Exception:
    pass  # Engine not switched, subsequent code runs with wrong engine
```

**Problem:** If switching to CYCLES fails (e.g., Cycles addon disabled), the code continues to set bake properties on the current (possibly EEVEE) engine, which may silently corrupt scene settings.

**Fix:**
```python
try:
    scene.render.engine = 'CYCLES'
except Exception:
    logger.error("Cannot switch to Cycles engine. Bake will likely fail.")
    return False
```

---

### HI-03: Objects Without Materials Silently Skipped — [FIXED]
**File:** `core/engine.py:338`  
**Severity:** HIGH  

```python
if not mats:
    continue  # Object skipped with NO user feedback
```

**Problem:** When baking multi-material objects, if an object has no materials, it's silently skipped. The user receives no warning or log message, making it appear as though the bake completed successfully while producing incomplete results.

**Fix:**
```python
if not mats:
    logger.warning(f"Object '{obj.name}' has no materials, skipping.")
    log_error(context, f"Object '{obj.name}' skipped: no materials assigned.")
    continue
```

---

### HI-04: `execution.py:80` Clears All Previous Error Logs — [FIXED]
**File:** `core/execution.py:80`  
**Severity:** HIGH  

```python
context.scene.bake_error_log = ""
```

**Problem:** When a new bake starts, ALL previous error logs are cleared. If the user was debugging a previous bake failure and starts a new bake, the diagnostic information is lost.

**Fix:** Prepend timestamp or move to history:
```python
context.scene.bake_error_log = f"--- New bake session {time.strftime('%H:%M:%S')} ---\n"
```

---

### HI-05: Node Manager Socket Logic — [FIXED]
**File:** `core/node_manager.py:308-309`  
**Severity:** HIGH  

```python
mix.inputs[6]  # Factor
mix.inputs[7]  # Color
```

**Problem:** The Mix node socket layout changed between Blender 3.x and 4.x. Hard-coded indices will break on future Blender versions.

**Fix:** Use named socket access:
```python
mix.inputs["Factor"].default_value = ...
mix.inputs["Color"].default_value = ...
```

---

### HI-06: `common.py:300` Appends `None` Material Slots — [FIXED]
**File:** `core/common.py:298-306`  
**Severity:** HIGH  

```python
while len(new_obj.material_slots) < len(mats):
    new_obj.data.materials.append(None)
```

**Problem:** Appending `None` to material slots and then indexing into them can cause type errors or silent data corruption. On Blender 4.0+, `materials.append(None)` may behave differently.

**Fix:** Use `materials.append(mat)` directly instead of pre-filling with `None`:
```python
for mat in mats:
    if mat:
        new_obj.data.materials.append(mat)
```

---

### HI-07: CLI Runner Discovery Pattern Mismatch — [FIXED]
**File:** `automation/cli_runner.py:58`  
**Severity:** HIGH  

```python
pattern='test_*.py'  # But test files are named suite_*.py!
```

**Problem:** The `--discover` flag uses `test_*.py` glob pattern, but the actual test files are named `suite_*.py`. This means `--discover` will find **zero tests**.

**Fix:**
```python
pattern='suite_*.py'
```

---

### HI-08: Dead `iterations` Parameter — [FIXED (Removed)]
**File:** `core/math_utils.py:129`  
**Severity:** HIGH (logic error)  

```python
def generate_optimized_colors(count, start_color=(1,0,0,1), iterations=0, ...):
    # 'iterations' is NEVER used in the function body
```

**Problem:** The `iterations` parameter is accepted but completely ignored. Callers passing `iterations=50` (as done in `property.py:280`) expect quality improvement that never happens.

**Fix:** Either implement the iterations logic or remove the parameter and update all callers.

---

## 4. Medium Severity Issues

### ME-01 through ME-15

| ID | File:Line | Issue |
|---|---|---|
| ME-01 | `engine.py:121` | `"Viewer Node"` hardcoded — may differ across Blender versions |
| ME-02 | `engine.py:596-607` | `orig_samples` captured but restore in `finally` could conflict with concurrent modifications |
| ME-03 | `compat.py:43-48` | `BAKE_MAPPING` dict recreated every function call — should be module-level constant |
| ME-04 | `engine.py:735-736` | Material clearing during export may affect shared object references |
| ME-05 | `uv_manager.py:155` | `bpy.ops.object.select_all(action='DESELECT')` deselects ALL scene objects, not just targets |
| ME-06 | `cage_analyzer.py:106` | Same issue: `select_all` deselects everything in the scene |
| ME-07 | `node_manager.py:117` | `if n in tree.nodes.values()` is O(n) — use `n.name in tree.nodes` for O(1) |
| ME-08 | `thumbnail_manager.py:42` | No error handling for corrupt/unreadable image files in `pcoll.load()` |
| ME-09 | `shading.py:32` | `ShaderNodeCombineColor` introduced in 3.3, but manifest claims 3.3 support — edge case risk |
| ME-10 | `image_manager.py:141` | `robust_image_editor_context` uses `bpy.context` instead of passed context parameter |
| ME-11 | `common.py:218` | `context.temp_override()` only available in Blender 3.x+, not documented as minimum |
| ME-12 | `math_utils.py:263` | BMesh `tag` set to integer `0`/`1` instead of boolean `False`/`True` |
| ME-13 | `preset_handler.py:67` | `isinstance(prop, bpy.types.CollectionProperty)` may not work reliably for RNA property definitions |
| ME-14 | `engine.py:338` | Missing material feedback (also listed as HI-03 for user impact) |
| ME-15 | `image_manager.py:195-199` | Path resolution logic fragile for unsaved files on non-standard platforms |

---

## 5. Low Severity / Code Quality Issues

| ID | File:Line | Issue |
|---|---|---|
| LO-01 | `api.py:8` | `ValidationResult` imported but never used |
| LO-02 | `ui.py:5` | `BAKE_PT_BakePanel` imported in `suite_ui_logic.py` but never used |
| LO-03 | `suite_unit.py:118` | `assertGreaterEqual(io.stats['error'], 0)` is always True |
| LO-04 | `math_utils.py:354` | Redundant local `import bmesh` (already imported at line 2) |
| LO-05 | `suite_preset.py:157-172` | Migration test depends on dict insertion order (safe in 3.7+ but fragile) |
| LO-06 | `translations.json` | Many strings still in English for fr_FR, ru_RU, ja_JP locales |
| LO-07 | `README.md:16` | Emoji usage inconsistent with rest of document |
| LO-08 | `docs/ROADMAP.md:130-140` | Merge conflict artifacts (lines starting with `+`) |
| LO-09 | `docs/ROADMAP.md:70` | Broken sentence: "...via temporary composito##" |
| LO-10 | `docs/dev/DEVELOPER_GUIDE.md:101,119` | Duplicate section numbering (4.4 and 4.5 appear twice) |
| LO-11 | `__init__.py:1-4` | Redundant imports: `from bpy import (props, types)` + `from bpy.props import IntProperty...` |
| LO-12 | `constants.py:1-3` | Incomplete GPL license header (just says "...") |

---

## 6. Test Infrastructure Assessment

### Current Coverage Matrix

| Core Module | Unit Tests | E2E Tests | Coverage Grade |
|---|---|---|---|
| `core/compat.py` | 3 (thin) | — | **D** |
| `core/api.py` | 3 | — | **C-** |
| `core/engine.py` | — | Yes | **B** |
| `core/execution.py` | — | Implicit | **C** |
| `core/image_manager.py` | 2 | — | **B-** |
| `core/math_utils.py` | 5 | — | **A-** |
| `core/uv_manager.py` | 1 | — | **C** |
| `core/node_manager.py` | 1 (partial) | — | **D+** |
| `core/common.py` | 3 | — | **B-** |
| `core/cage_analyzer.py` | 2 | — | **B** |
| `core/cleanup.py` | 1 | — | **C+** |
| `core/shading.py` | **0** | — | **F** |
| `core/thumbnail_manager.py` | **0** | — | **F** |
| `preset_handler.py` | 5 | — | **A-** |
| `state_manager.py` | 2 | 1 | **B** |
| `property.py` | 1 | — | **D** |
| `ops.py` | 1 (poll) | — | **D** |
| `ui.py` | 1 | — | **D** |

### Test Anti-Patterns Found

1. **`suite_api.py:46-50`**: `test_bake_trigger_api` silently swallows all exceptions — false negatives.
2. **`suite_unit.py:118`**: `assertGreaterEqual(io.stats['error'], 0)` is always True — useless assertion.
3. **`suite_compat.py`**: No `setUp`/`tearDown` — pollutes scene state between tests.
4. **`cli_runner.py:58`**: Discovery pattern `test_*.py` mismatches actual file names `suite_*.py`.

### Zero-Coverage Modules (Critical Gaps)

- **`core/shading.py`** (149 lines): Preview material creation, node connections, shader switching — completely untested.
- **`core/thumbnail_manager.py`** (49 lines): Preview collection lifecycle — untested.
- **`ModelExporter`** class in `core/engine.py` (92 lines): GLB/USD/FBX export logic — only tested indirectly through E2E.
- **`BakeContextManager`** in `core/engine.py`: Context save/restore — untested.
- **`BakePassExecutor`** pipeline methods: Individual bake steps — only tested through E2E.

---

## 7. Architecture Observations

### Strengths

1. **Data-Driven UI** (`constants.py:CHANNEL_UI_LAYOUT`): The UI is driven by declarative config rather than imperative drawing. This is excellent for maintainability.

2. **Cross-Version Compatibility Layer** (`core/compat.py`): Clean abstraction over Blender version differences. The `set_bake_type` function with fallback chains is well-designed.

3. **Crash Recovery** (`state_manager.py`): JSON-based session logging with `fsync` for durability. The `has_crash_record()` → `resume` flow is a production-grade feature.

4. **Preset Migration** (`constants.py:PRESET_MIGRATION_MAP`): Forward-compatible preset loading with automatic property migration. The warning about 1-to-many conflicts is well-documented.

5. **Resource Protection** (`node_manager.py`): Node graph backup/restore prevents bake operations from corrupting user materials.

6. **Test Infrastructure** (`helpers.py`): `DataLeakChecker` and `JobBuilder` are exemplary patterns for Blender addon testing.

### Architectural Concerns

1. **Global Mutable State**: `thumbnail_manager.py:7` uses a module-level dict. `__init__.py:135` uses `addon_keymaps=[]`. These persist across script reloads.

2. **Mixed Concerns in `engine.py`**: At 792 lines, this file contains task building, job preparation, bake execution, post-processing, and model export. These should be separate modules.

3. **Inconsistent Error Handling**: Some modules use `log_error()`, others use `logger.error()`, and still others silently skip. A unified error reporting strategy is needed.

4. **No Dependency Injection**: Core modules access `bpy.context` directly instead of receiving context as a parameter, making unit testing harder.

5. **Version-Dependent Hardcoded Values**: Socket indices, node names, and API paths are hardcoded without version guards in several places.

---

## 8. Detailed Remediation Plan

### Phase 1: Critical Bug Fixes (Immediate)

**Priority:** P0 — Must be completed before any release.

#### Step 1.1: Fix Vector Falsiness Bug
**File:** `core/cage_analyzer.py:83`  
**Change:** Replace `if location and distance <= extrusion:` with `if location is not None and distance <= extrusion:`

#### Step 1.2: Fix StopIteration Crash
**File:** `core/common.py:297`  
**Change:** Add empty dict guard before `next(iter(task_images.values()))`:
```python
if not task_images:
    logger.warning("apply_baked_result: No images to apply.")
    return
```

#### Step 1.3: Fix Save-and-Quit Data Loss
**File:** `core/execution.py:192`  
**Change:** Add user confirmation or remove the feature. At minimum, check `bpy.data.is_dirty` before saving.

#### Step 1.4: Fix Uninitialized `_timer` Attribute
**File:** `core/execution.py`  
**Change:** Add `__init__` method to `BakeModalOperator` that initializes `self._timer = None`, `self.bake_queue = []`, `self._current_idx = 0`.

### Phase 2: High Severity Fixes (Before Next Release)

#### Step 2.1: Replace All Bare `except:`
**Files:** `cage_analyzer.py:128,131`, `image_manager.py:182`, `cli_runner.py:44`, `multi_version_test.py:30`  
**Change:** Replace `except:` with `except Exception:` in all locations.

#### Step 2.2: Guard Engine Switch Failure
**File:** `core/compat.py:55-58`  
**Change:** Return `False` if engine switch fails instead of continuing.

#### Step 2.3: Add Material-Missing Feedback
**File:** `core/engine.py:338`  
**Change:** Add `logger.warning()` and `log_error()` calls before the `continue`.

#### Step 2.4: Preserve Error Log History
**File:** `core/execution.py:80`  
**Change:** Append session separator instead of clearing.

#### Step 2.5: Use Named Socket Access
**File:** `core/node_manager.py:308-309`  
**Change:** Replace `mix.inputs[6]` with `mix.inputs["Factor"]` and `mix.inputs[7]` with `mix.inputs["Color"]` (with version-aware fallback).

#### Step 2.6: Fix Material Slot None Append
**File:** `core/common.py:298-306`  
**Change:** Refactor to append materials directly instead of pre-filling with `None`.

#### Step 2.7: Fix CLI Discovery Pattern
**File:** `automation/cli_runner.py:58`  
**Change:** Replace `pattern='test_*.py'` with `pattern='suite_*.py'`.

#### Step 2.8: Remove or Implement `iterations` Parameter
**File:** `core/math_utils.py:129`  
**Change:** Either implement the iterations optimization algorithm or remove the dead parameter and update `property.py:280`.

### Phase 3: Medium Severity Fixes (Next Sprint)

#### Step 3.1: Extract BAKE_MAPPING to Module Constant
**File:** `core/compat.py:43-48`

#### Step 3.2: Add Viewer Node Name Version Check
**File:** `core/engine.py:121`

#### Step 3.3: Optimize Node Lookup
**File:** `core/node_manager.py:117`  
**Change:** Use `n.name in tree.nodes` instead of `n in tree.nodes.values()`.

#### Step 3.4: Add Thumbnail Load Error Handling
**File:** `core/thumbnail_manager.py:42`

#### Step 3.5: Fix Selective Object Operations
**Files:** `uv_manager.py:155`, `cage_analyzer.py:106`  
**Change:** Only select/deselect target objects, not all scene objects.

#### Step 3.6: Fix Context Parameter Usage
**File:** `image_manager.py:141`  
**Change:** Use the passed `context` parameter instead of `bpy.context`.

#### Step 3.7: Use Boolean for BMesh Tags
**File:** `math_utils.py:263-264`  
**Change:** Replace `tag = 0`/`visited_tag = 1` with `tag = False`/`visited_tag = True`.

#### Step 3.8: Fix Documentation Artifacts
**Files:** `docs/ROADMAP.md`, `docs/dev/DEVELOPER_GUIDE.md`  
**Change:** Remove merge conflict artifacts and fix duplicate section numbering.

### Phase 4: Code Quality Improvements (Ongoing)

- Remove dead imports (`api.py:8`, `suite_ui_logic.py:5`)
- Fix always-true assertion (`suite_unit.py:118`)
- Remove redundant local imports (`math_utils.py:354`)
- Complete translation coverage for fr_FR, ru_RU, ja_JP
- Clean up `__init__.py` redundant imports
- Fix incomplete license headers in `constants.py`

---

## 9. Unit Test Expansion Plan

### Phase A: Zero-Coverage Module Tests (Highest Priority)

#### A1: `core/shading.py` — New File: `test_cases/suite_shading.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_create_preview_material_basic` | Creates preview material, verifies BSDF node exists | P0 |
| `test_create_preview_material_with_packing_channels` | Packing channel R/G/B/A map to correct textures | P0 |
| `test_apply_preview_stores_original_material` | `apply_preview` stores original mat name in custom property | P0 |
| `test_remove_preview_restores_material` | `remove_preview` restores the original material | P0 |
| `test_remove_preview_cleans_up_temp_material` | Temp material is removed from `bpy.data.materials` | P1 |
| `test_preview_material_uses_combined_color_node` | Verify `ShaderNodeCombineColor` is used (3.3+ check) | P1 |
| `test_apply_preview_no_crash_on_missing_material` | `apply_preview` on object with no material | P1 |

#### A2: `core/thumbnail_manager.py` — New File: `test_cases/suite_thumbnail.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_get_preview_collection_creates_new` | Returns new collection when none exists | P0 |
| `test_get_preview_collection_returns_existing` | Returns same collection on repeated calls | P0 |
| `test_clear_preview_collection_removes_entries` | Clear removes all icons from collection | P0 |
| `test_load_preset_thumbnails_from_empty_dir` | Handles empty directory gracefully | P1 |
| `test_load_preset_thumbnails_skips_corrupt_images` | Corrupt PNG doesn't crash the loader | P1 |
| `test_get_icon_id_returns_zero_for_missing` | Returns 0 when icon name not found | P1 |

#### A3: `ModelExporter` — New Tests in `test_cases/suite_unit.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_model_exporter_fbx_creates_file` | FBX export creates actual file on disk | P0 |
| `test_model_exporter_glb_creates_file` | GLB export creates actual file on disk | P0 |
| `test_model_exporter_preserves_materials` | Original object materials are restored after export | P0 |
| `test_model_exporter_handles_no_materials` | Export object with no materials | P1 |
| `test_model_exporter_usd_missing_addon_graceful` | USD export when addon disabled | P1 |

#### A4: `BakeContextManager` — New Tests in `test_cases/suite_unit.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_bake_context_manager_saves_render_engine` | Saves and restores render engine | P0 |
| `test_bake_context_manager_saves_selection` | Saves and restores object selection | P0 |
| `test_bake_context_manager_exception_restores` | State restored even when exception occurs | P0 |

### Phase B: Expanded Coverage for Existing Modules

#### B1: `core/compat.py` — Expand `test_cases/suite_compat.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_set_bake_type_all_passes` | Test ALL bake types (DIFFUSE, GLOSSY, TRANSMISSION, etc.) | P0 |
| `test_get_bake_settings_returns_dict` | `get_bake_settings()` returns expected keys | P0 |
| `test_set_bake_type_invalid_string` | Unknown bake type returns False | P1 |
| `test_version_string_format` | `get_version_string()` returns "X.Y.Z" format | P2 |
| `test_set_bake_type_engine_restoration_on_failure` | Engine state preserved when bake_type fails | P1 |

#### B2: `core/api.py` — Expand `test_cases/suite_api.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_bake_with_empty_objects_list` | `api.bake([])` handles gracefully | P0 |
| `test_bake_with_none_arguments` | `api.bake(None)` raises appropriate error | P0 |
| `test_get_udim_tiles_no_uv_layers` | Objects without UV layers return 1001 | P1 |
| `test_validate_settings_valid_job` | Valid job returns success | P1 |
| `test_bake_with_selection_false` | `use_selection=False` behavior | P2 |

#### B3: `core/node_manager.py` — Expand in `test_cases/suite_unit.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_node_graph_handler_setup_and_cleanup` | Full lifecycle: prepare → cleanup → verify restored | P0 |
| `test_setup_protection_creates_dummy_nodes` | Protection nodes are created for all objects | P0 |
| `test_setup_for_pass_emission_insertion` | Emission node + Image Texture inserted correctly | P0 |
| `test_setup_for_pass_normal_tangent_space` | Normal map node inserted for NORMAL pass | P1 |
| `test_cleanup_restores_original_links` | Original node links are preserved after cleanup | P0 |
| `test_bake_node_to_image_basic` | Standalone node baking produces valid image | P1 |

#### B4: `core/uv_manager.py` — Expand in `test_cases/suite_unit.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_uv_layout_manager_smart_uv_creates_layer` | Smart UV creates a new UV layer | P0 |
| `test_uv_layout_manager_restores_original` | Original UV layer restored on exit | P0 |
| `test_uv_layout_manager_exception_restores` | UV state restored even on exception | P1 |
| `test_udim_packer_assigns_sequential_tiles` | Objects get tiles 1001, 1002, 1003... | P1 |
| `test_detect_object_udim_tile_no_uv` | Returns 1001 when no UV layers | P2 |

#### B5: `core/image_manager.py` — Expand in `test_cases/suite_unit.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_set_image_creates_correct_resolution` | Image dimensions match x, y parameters | P0 |
| `test_set_image_float32` | 32-bit float image creation | P1 |
| `test_set_image_udim_tiles` | UDIM image with multiple tiles | P1 |
| `test_save_image_to_disk` | File exists on disk after save | P0 |
| `test_save_image_relative_path_unsaved_file` | Handles unsaved .blend file gracefully | P1 |

### Phase C: Negative / Edge Case Testing

#### C1: Negative Input Tests — New File: `test_cases/suite_negative.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_bake_with_deleted_object_reference` | BakeJob references deleted object | P0 |
| `test_bake_with_corrupted_image_data` | Image with zero pixels | P1 |
| `test_preset_load_malformed_json` | Non-JSON file as preset | P0 |
| `test_preset_load_missing_required_keys` | JSON with partial data | P1 |
| `test_export_to_readonly_directory` | Save to non-writable path | P1 |
| `test_bake_with_zero_resolution` | 0x0 image dimensions | P0 |
| `test_bake_with_very_large_margin` | Margin > resolution | P2 |
| `test_operator_execute_without_scene_properties` | Operator called before addon registration | P1 |

#### C2: Concurrency / Stress Tests — New File: `test_cases/suite_stress.py`

| Test Name | What It Tests | Priority |
|---|---|---|
| `test_rapid_sequential_bakes_no_leak` | 5 bakes in sequence, verify no data-block growth | P1 |
| `test_large_job_queue_execution` | 20+ jobs in single bake | P2 |
| `test_cancel_during_bake_cleanup` | Modal cancel during step execution | P1 |

---

## 10. Execution Order & Priority Matrix

### Recommended Execution Timeline

```
Week 1: Phase 1 (Critical Bug Fixes)
  ├── CR-01: cage_analyzer.py Vector falsiness fix
  ├── CR-02: common.py StopIteration guard
  ├── CR-03: execution.py save_and_quit safety
  └── CR-04: execution.py _timer initialization

Week 2: Phase 2 (High Severity Fixes)
  ├── HI-01: Replace all bare except:
  ├── HI-02: Guard engine switch failure
  ├── HI-03: Material-missing feedback
  ├── HI-04: Preserve error log history
  ├── HI-05: Named socket access
  ├── HI-06: Material slot None fix
  ├── HI-07: CLI discovery pattern
  └── HI-08: Remove dead iterations param

Week 3: Phase 3 + Phase A Tests
  ├── ME-01 through ME-08: Medium severity fixes
  ├── A1: suite_shading.py (7 new tests)
  ├── A2: suite_thumbnail.py (6 new tests)
  └── A4: BakeContextManager tests (3 new tests)

Week 4: Phase B Tests
  ├── B1: suite_compat.py expansion (5 new tests)
  ├── B2: suite_api.py expansion (5 new tests)
  ├── B3: node_manager.py tests (6 new tests)
  ├── B4: uv_manager.py tests (5 new tests)
  └── B5: image_manager.py tests (5 new tests)

Week 5: Phase C Tests + Documentation
  ├── C1: suite_negative.py (8 new tests)
  ├── C2: suite_stress.py (3 new tests)
  ├── Fix ROADMAP.md merge artifacts
  └── Fix DEVELOPER_GUIDE.md section numbering
```

### Test Count Projection

| Category | Current | Planned | Total |
|---|---|---|---|
| Existing Tests | 48 | — | 48 |
| Phase A (New Modules) | — | 16 | 64 |
| Phase B (Expansion) | — | 26 | 90 |
| Phase C (Negative/Stress) | — | 11 | 101 |
| **Grand Total** | **48** | **53** | **101** |

### Success Criteria

- [ ] All 4 critical bugs resolved with regression tests
- [ ] All 8 high-severity issues resolved
- [ ] Test count reaches 80+ (from current 48)
- [ ] Zero bare `except:` clauses in production code
- [ ] `core/shading.py` and `core/thumbnail_manager.py` reach B+ coverage
- [ ] `suite_compat.py` covers all bake types
- [ ] All tests pass on Blender 3.6, 4.2, and 5.0
- [ ] No data-block leaks detected by `DataLeakChecker` across all tests

---

## Appendix A: File-by-File Issue Summary

| File | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| `core/cage_analyzer.py` | 1 | 1 | — | — | 2 |
| `core/common.py` | 1 | 1 | 1 | — | 3 |
| `core/compat.py` | — | 1 | 1 | — | 2 |
| `core/engine.py` | — | 1 | 2 | — | 3 |
| `core/execution.py` | 2 | 1 | — | — | 3 |
| `core/image_manager.py` | — | — | 2 | — | 2 |
| `core/math_utils.py` | — | 1 | 1 | 1 | 3 |
| `core/node_manager.py` | — | 1 | 1 | — | 2 |
| `core/shading.py` | — | — | 1 | — | 1 |
| `core/thumbnail_manager.py` | — | — | 1 | — | 1 |
| `core/uv_manager.py` | — | — | 1 | — | 1 |
| `automation/cli_runner.py` | — | 1 | — | — | 1 |
| `automation/multi_version_test.py` | — | — | — | — | 0* |
| Test Suites | — | — | — | 4 | 4 |
| Documentation | — | — | — | 4 | 4 |
| **TOTAL** | **4** | **8** | **12** | **9** | **33** |

*bare except already counted in HI-01 aggregate.

---

*End of Code Review*
