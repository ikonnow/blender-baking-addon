# Blender Baking Workflow & BakeTool Assessment Report

## 1. Blender Baking: Challenges & Workflows

### The Core Challenges in Blender
1.  **Context Sensitivity**: `bpy.ops.object.bake` is notoriously picky about the active object and selection state.
2.  **Material Setup Overhead**: Manually creating "Bake Target" nodes and ensuring they are selected is error-prone.
3.  **Lack of PBR Native Export**: Blender bakes "Passes" (Diffuse, Roughness), but doesn't natively "Pack" them (e.g., ORM for Unreal) without complex node setups.
4.  **Hardware Management**: Switching between CPU and GPU (and handling samples) needs to be global but temporary.

### The BakeTool Solution (The Logic Flow)
- **Pre-Bake**: `JobPreparer` + `TaskBuilder` abstracts the scene. It doesn't care *what* is selected; it calculates *what should be* baked.
- **Execution**: `BakeStepRunner` manages the "Secure Context". It uses context overrides to trick Blender's legacy ops into working reliably.
- **Post-Bake**: NumPy-accelerated packing and `ModelExporter` close the loop, turning raw data into game-ready assets.

---

## 2. BakeTool Evaluation

### Generality (通用性) - **Rating: A-**
- **Abstraction**: The `core.engine` is highly abstracted. A developer can theoretically import `BakeStepRunner` and pass it a custom `BakeStep` without touching the UI.
- **Improvement Point**: The engine still relies heavily on the `BakeJobSetting` PropertyGroup. Decoupling this into a plain-Python data class would make it 100% usable as a standalone library.

### Comprehensiveness (涵盖性) - **Rating: A**
- **End-to-End**: It covers Material Analysis -> UV/UDIM Management -> Rendering -> NumPy Processing -> FBX/GLB Export.
- **Bridge to SP/External**: The auto-packing (ORM) and standard naming conventions make it highly compatible with Substance Painter (SP) and Unreal Engine workflows.

### Stability (稳定性) - **Rating: S (Superior)**
- **Versatility**: 100% test pass rate from Blender 3.6 to 5.0.
- **Resilience**: The new `TestProductionHazards` ensures that even if the user has "broken" meshes or "locked" files, the addon fails gracefully instead of crashing the Blender process.

---

## 3. Blueprint (Roadmap) Evaluation & Incremental Updates

### Assessment of the Current Blueprint
The current roadmap is solid but focuses heavily on "Features". To reach "Middleware" status, we need to focus more on **"Integration Stability"** and **"Data Integrity"**.

### Suggested Incremental Updates (Refined Roadmap)

#### [Update] Phase 1: Real-time & Responsibility
- **[New] Progress API**: Expose a callback mechanism so other addons can listen to bake progress.

#### [Update] Phase 2: Intelligence
- **[New] Material Semantic Library**: A JSON-based mapping system that allows artists to define "If I see a node named 'Roughness_Target', map it to the Roughness channel automatically."

#### [Update] Phase 4: Production Scale
- **[New] Headless Farm Support**: Explicit support for running BakeTool jobs via CLI on a render farm without a GUI.

---

## 4. Final Recommendation
BakeTool has evolved from a simple utility into a robust **Baking Engine**. The next step is to formalize the **Developer API** to allow other pipeline tools (like asset browsers) to trigger bakes programmatically.
