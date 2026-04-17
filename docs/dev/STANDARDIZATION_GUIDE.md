# Blender Addon Standardization Guide (The BakeTool Pattern)

This document outlines the architectural standards and engineering practices developed for **BakeTool**, intended as a reference for creating professional-grade, industrial-strength Blender middleware.

---

## 1. Core Mandates

### 1.1 Engine-UI Decoupling
*   **Principle**: `ui.py` should only handle drawing and basic context gathering. All heavy logic must reside in `core/`.
*   **Standard**: Use a "Task-Step" architecture. The UI creates a `BakeTask`, which the `BakeStepRunner` executes. This allows for headless execution and automated testing without viewport dependencies.

### 1.2 Translation-Driven Development (TDD)
*   **Principle**: Zero hardcoded strings in the UI.
*   **Standard**: All user-facing text must be defined in `translations.json`. Use `pgettext_iface` for contextual translations to support Blender's localized UI seamlessly.

### 1.3 Triple-Point Parameter Alignment
*   **Principle**: Prevent desynchronization between UI properties and engine parameters.
*   **Standard**:
    1.  **Constants**: Define defaults, ranges, and types in `constants.py`.
    2.  **Property**: Map RNA properties to these constants in `property.py`.
    3.  **Engine**: Use these constants to validate incoming tasks.
    *   *Self-Verification*: Implement a `suite_parameter_matrix.py` test to verify this alignment dynamically.

---

## 2. Code Quality & Style (Google Python Style Adaptation)

### 2.1 Namespace Isolation
*   Avoid using common module names like `property`. Use `prop_module` or `property_group` to prevent shadowing Python's built-ins.
*   Prefix temporary scene data (Materials, Images) with `BT_` or `_bt_`.

### 2.2 Defensive Programming
*   **Safe Context Overrides**: Always use `context.temp_override()` or a robust custom context manager for operations requiring specific areas (like the Image Editor).
*   **Exception Specificity**: Replace bare `except:` with specific exceptions (e.g., `AttributeError`, `RuntimeError`).
*   **Material Factories**: Use UUIDs for temporary materials created during baking to avoid naming collisions with user data.

### 2.3 Documentation & Type Hinting
*   **Format**: Use **Google Style** docstrings for all core functions.
*   **Type Hints**: Enforce type hinting for all public APIs in the `core/` module.

---

## 3. Testing & Automation Pipeline

### 3.1 Cross-Version Matrix Testing
*   Addons must be verified against a matrix of Blender versions (e.g., 3.3, 3.6, 4.2 LTS, 5.0+).
*   Use `multi_version_test.py` to automate this process locally before deployment.

### 3.2 Resilience Testing
*   **Leak Detection**: Use a `DataLeakChecker` in tests to ensure data blocks (Meshes, Images) are correctly unlinked and removed after operations.
*   **Negative Testing**: Explicitly test failure states (e.g., missing UVs, disk full, corrupted JSON presets).

---

## 4. Future Standardization Frontiers

### 4.1 Bake Metadata Standard (.btmeta)
Standardize a sidecar JSON file that records the exact environment under which a texture was baked (samples, engine version, high-poly source names).

### 4.2 VRAM Audit Mechanism
Before starting a heavy batch, standardize a pre-computation step to estimate VRAM usage and warn the user if it exceeds a safety threshold.

### 4.3 Addon-as-Middleware
Standardize a public API entry point (`core/api.py`). Any functionality exposed via UI buttons should be reachable via a clean Python function call for other addon developers.

---

## 5. Summary of the Development Workflow
1.  **Define Constants** in `constants.py`.
2.  **Implement Logic** in `core/` with type hints.
3.  **Expose via API** in `core/api.py`.
4.  **Connect UI** in `property.py` and `ui.py` using translations.
5.  **Write Tests** in `test_cases/`.
6.  **Verify Cross-Version** via `automation/`.
7.  **Standardized Commit** following the versioning protocol.
