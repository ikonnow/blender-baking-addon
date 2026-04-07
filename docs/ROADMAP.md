# BakeTool Development Roadmap (Strategic Vision)

This document outlines the long-term strategic vision for Simple Bake Tool (SBT), evolving it from a utility addon into a professional-grade **Baking Middleware** for the Blender ecosystem.

## 📅 Phase 1: Visual & UX Revolution (Focus: Artist Feedback)
*Goal: Bridge the gap between parameter tuning and visual results, eliminating "blind baking".*

### 1.1 Interactive Packing Preview [DONE]
- **Status**: Completed in v1.0.0.
- **Feature**: Use GLSL Viewport Shaders to simulate channel packing (ORM) in real-time before baking.
- **Tech**: Temporary shader trees mixing inputs based on "Pack" settings.
- **Benefit**: Visualize RGBA channel distribution instantly.

### 1.2 Visual Cage Analysis [DONE]
- **Status**: Completed (v0.9.5).
- **Feature**: A "Heatmap" overlay on the mesh showing areas where the Cage might intersect with the High Poly mesh or miss details.
- **Tech**: Ray-cast analysis between Low-Poly (with Cage extrusion) and High-Poly objects using BVH-Tree.
- **Benefit**: Visually identify "missed rays" or artifacts before committing to a bake.

### 1.3 Asynchronous Progress UI [DONE]
- **Status**: Completed (Modal Progress with Event Loop decoupling).
- **Tech**: Uses `BakeModalOperator` to maintain UI responsiveness during heavy bakes.

### 1.4 Automated UI Logic Guard [NEW]
- **Status**: Completed (v0.9.0).
- **Feature**: Static analysis of `CHANNEL_UI_LAYOUT` vs Blender RNA properties to prevent runtime UI crashes.
- **Benefit**: 100% confidence when adding new bake channels.

---

---

## 🏭 Phase 2: Pipeline Integration (Focus: TD & Automation)
*Goal: Decouple the Engine from the UI, enabling headless operation and external script integration.*

### 2.1 Engine-UI Decoupling [DONE]
- **Status**: Refined in v0.9.0.
- **Feature**: God-functions split into granular methods (`_create_target_image`, `_execute_blender_bake_op`). 
- **Benefit**: Pure headless operation without relying on active Viewport context.

### 2.2 Public Python API [DONE]
- **Status**: Completed in v1.0.0.
- **Feature**: Standardized API for other addon developers via `core/api.py`.

### 2.3 Preset Library 2.0 (Visual UI) [DONE]
- **Status**: Completed in v0.9.3.
- **Feature**: A dedicated Preset Gallery supporting thumbnail previews and dynamic refresh.
- **Goal**: Improved artist experience for managing complex material projects.

### 2.4 Bake Performance Profiler [DONE]
- **Status**: Completed in v0.9.3.
- **Feature**: Real-time breakdown of Bake time vs I/O (Save) time per channel.
- **Benefit**: Identify bottlenecks in large-scale asset production.

---

## 馃 Phase 3: Intelligence & Algorithms (Focus: Workflow Speed)
*Goal: Replace manual trial-and-error with algorithmic assistance.*

### 3.1 Auto-Cage 2.1 (Proximity-Based) [DONE]
- **Status**: Refined for Production in v0.9.0.
- **Upgrade**: Algorithm predicts safe average extrusion using Numpy ray-casting proximity analysis.

### 3.2 Smart Texel Density [DONE]
- **Status**: Completed in v1.0.0.
- **Feature**: Auto-calculate output resolution based on physical object size.

### 3.3 Anti-Aliasing & Denoise Pipeline [DONE]
- **Status**: Completed in v0.9.3.
- **Feature**: Integrated OIDN (Open Image Denoise) via temporary compositor nodes.

## 🚀 Phase 4: Production Hardening & Ecosystem [STABLE v1.0.0]
*Goal: 100% architectural stability, zero-leak scene management, and cross-version parameter alignment.*

### 4.1 Parameter Consistency & Dynamic Alignment (Hardened) [DONE]
- **Status**: **100% CI PASS** for 3.3, 3.6, 4.2, 4.5, 5.0. 
- **Mechanism**: Triple-Point Alignment Protocol (Constants -> Engine -> Automation).
- **Benefit**: Ensures zero `AttributeError`/`NameError` regressions for 120+ attribute mappings. Added `suite_parameter_matrix.py` and `MockSetting` helpers to verify mapping integrity dynamically across all code paths.
- **Prevention**: Established strict type-checking and `hasattr` guards in shading/node logic to handle Blender RNA variations.

### 4.2 Zero-Leak Denoise Pipeline (Recursive Cleanup) [DONE]
- **Status**: Hardened for v1.0.0.
- **Tech**: Specialized `finally` block logic that recursively identifies and purges all `BT_Denoise_Temp*` scenes, clearing node-trees and using `user_clear()` to satisfy B5.0 deletion constraints.
- **Benefit**: Prevents memory spikes and "Active Scene" conflicts during batch bakes.

### 4.3 Blender 5.0.x Full Support [DONE]
- **Status**: Completed in v1.0.0.
- **Tech**: Implemented robust tree discovery (Direct -> Compositor Object -> Fallback creation). Fixed `EnumProperty` registration constraints for dynamic item callbacks.
- **Cross-Version Rock-Solid**: 100% Pass Rate confirmed for Blender 3.3, 3.6, 4.2 LTS, 4.5, and 5.0. Verified with recursive scene protection.

### 4.4 Production E2E Validation Loop [DONE]
- **Status**: Completed (v1.0.0).
- **Tooling**: `multi_version_test.py` now monitors 70 core test suites across multiple local Blender installs automatically. Added negative test suite to ensure error-path resilience.

### 4.5 UI/UX Production Refactor & Dashboard Logic [DONE]
- **Status**: Completed in v1.0.0.
- **Feature**: Comprehensive dashboard-style refactor. Replaced nested boxes with aligned columns and grouped functional zones for better vertical flow.
- **Goal**: Professional, streamlined aesthetic matching high-end Blender addons.

### 4.6 Multi-Version Icon & Operator Audit [DONE]
- **Status**: Completed (v1.0.0-p5).
- **Feature**: Automated integrity check (`test_ui_operator_integrity`) verifying that every operator used in `ui.py` is correctly registered. 
- **Hardening**: Audited and replaced high-version icons (e.g., `SYNCHRONIZED`, `RAYCAST`) with widely compatible alternatives for Blender 3.3 - 4.2+ support.

---

## 🔮 Phase 5: Async & Performance (Planned v1.1.0)
*Goal: Decouple baking processes and enhance external connectivity.*

### 5.1 Background Process Baking (Worker Thread)
- **Concept**: Spawn a detached Blender worker process to perform heavy bakes, keeping the main interface 100% responsive for modeling.
- **Priority**: HIGH (v1.1.0 focus).

### 5.2 Asset Bridge: Zero-Friction Delivery [PARTIAL]
- **Concept**: GLB/USDZ export is live, next step is automatic PBR material embedding immediately after baking.

### 5.3 Parallel Tile Baking (UDIM Optimizer)
- **Concept**: Multi-process tile baking for UDIM projects to leverage high core-count CPUs.

---

**Current Status**: v1.0.0 Stable (Production Ready).
**Next Focus**: Background Worker Implementation (v1.1.0).
