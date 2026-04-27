# BakeTool Roadmap

This document is not a wishlist of "everything we want to do", but a realistic roadmap for release and maintenance. It prioritizes based on current code structure, completed validation work, and actual maintenance pressure. BakeTool has completed the main consolidation for `1.0.0` release candidate, so the core of the roadmap is not to pile on more features, but to ensure clear boundaries for the final release and post-1.0.x maintenance.

## 1. Current Phase Positioning

### 1.1 Status

- Current Version: `1.0.0`
- Current Phase: Release candidate consolidated, entering final smoke testing, packaging, and release actions
- Current Goal: Form the first stable version ready for public release, rather than continuing to expand feature scope

### 1.2 Key Work Completed in Current Version

This round of consolidation addresses not minor flaws, but blockers that directly impact release quality:

- Complete missing UI operators to avoid inconsistency between interface buttons and registration status
- Fix headless background mode initialization logic
- Connect custom channels to actual execution chain
- Unify custom result keys to ensure packing logic can reuse custom maps
- Actually write lighting and Combined pass filter options to Blender bake settings
- Fix issue where `hide_viewport` wasn't restored after export
- Add color space enum mapping to Blender actual colorspace names
- Unify preset schema with Blender ID pointer save/restore strategy
- Complete translation key extraction, sync, audit, and multilingual regression
- Move View Layer pre-check to enqueue stage and add new image cleanup for failed bakes
- Change interactive Safety Audit to isolated Blender process execution to avoid RNA crashes
- Add regression tests and complete multi-version verification validation
- Complete negative and verification cross-version regression validation
- Rewrite core pre-release documentation
- **[v1.0.0-p1] Custom Channel Hardening**: Add default value support and self-reference filtering, eliminate architectural design defects
- **[v1.0.0-p1] Export Quality Optimization**: Support full format parameters like bit depth, compression, codecs, achieve safe scene setting overrides
- **[v1.0.0-p1] Automation Validation**: 100% full regression pass rate, new special hardening test suites
- **[v1.0.0-p1] Blender Extensions Adaptation**: Create blender_manifest.toml, support Blender 4.2+ extension installation format

This means 1.0.0's priority has shifted from "fixing features" to "risk control".

## 2. 1.0.0 Release Goals

The goal of 1.0.0 is not to complete all ideas at once, but to provide a trustworthy set of basic capabilities:

- Users can install and find the plugin in mainstream Blender versions
- Main panel, result panel, and node baking entry behave consistently
- Common PBR, Selected-to-Active, UDIM, custom maps, and export integration work
- Automation entry points can be used for local validation
- Documentation matches code behavior, no longer relying on verbal explanations or temporary memory

As long as the above goals are met, 1.0.0 is valid. Conversely, if we continue adding major features to this version, the risk will outweigh the benefits.

## 3. Pre-Release Boundaries to Maintain

Before official release, the following changes are not recommended:

- No large-scale UI redesign
- No deep refactoring/splitting at `core/engine.py` level
- No new major features that would rewrite preset structure
- No changes to existing Job concept and main workflow
- No additional third-party runtime dependencies

These items are not "never do", but should be deferred to 1.1 or later versions, building on a stable release foundation.

## 4. Post-1.0.0 Priority Directions

### 4.1 First Priority: Stability Maintenance and Feedback Loop

This is the primary work after release. Real users will expose scenario differences that local testing cannot fully cover, so 1.0.x focus should be:

- Archive and categorize user feedback
- Quickly locate high-frequency failure paths
- Add regression tests instead of just one-time fixes
- Keep changelog and task board continuously updated
- Continue treating parameter definitions, dynamic UI bindings, engine consumption, and automation assertions as the same protocol surface

Particularly need to watch:

- Different Blender installation paths and local environment differences
- Color space mapping under different color management configurations
- Stability of large scenes, many objects, and long sequence outputs
- Export integration dependency on third-party plugin enablement status
- "Non-functional crash points" like View Layer, context protection, failure cleanup, and debug entry isolation

### 4.2 Second Priority: Execution Engine Structural Split

Current `core/engine.py` carries many responsibilities, which is good for quick fixes but creates long-term maintenance pressure. A more reasonable post-release direction is gradual splitting rather than one-time rewriting:

- Split queue preparation, single-step execution, packing, export, and post-processing into clearer modules
- Keep external behavior of `BakePassExecutor`, `BakeStepRunner` stable
- Allow tests to more directly cover separated sub-modules

The most important thing here is not "how pretty the file split looks", but not breaking existing calling protocols.

### 4.3 Third Priority: Preset and Data Schema Stabilization

Once the plugin starts entering real projects, preset compatibility quickly becomes important. Future steps should gradually introduce:

- More explicit preset schema version identification
- More complete property migration mapping
- Explicit warnings for deprecated fields
- Clearer fallback strategies for missing and new fields

The goal is to make plugin upgrades not equal to redoing all presets.

### 4.4 Fourth Priority: Advanced Workflow Extensions

When basic stability is sufficient, consider extending in these directions:

- More granular node baking workflows
- Richer custom layer sources
- More complete batch export templates
- Pipeline-oriented metadata output
- More systematic UDIM batch processing and naming strategies

All of these should build on clear existing workflows and sufficient testing.

## 5. Mid-term Planning: 1.1.x

`1.1.x` can be seen as an "architecture upgrade version without breaking 1.0 workflows". Candidate directions:

### 5.1 Further Engine Modularization

- Further separate packing and custom map assembly logic
- Extract export flow context protection and state recovery logic
- Introduce clearer data structure boundaries for bake queue

### 5.2 Stricter Presets and Automation

- Add preset roundtrip validation matrix
- Add more combination tests for custom maps, animation baking, UDIM, and export integration
- Strengthen consistency validation of headless and API paths
- **Parameter Consistency and Dynamic Alignment Validation**: Write parameter alignment constraints into truly regressable rules, establish automatic audit mechanism for three-point consistency of "property definition-UI mapping-engine consumption"

### 5.3 Blender Extensions Ecosystem Integration

- Continuously sync `bl_info` and `blender_manifest.toml` versions and fields
- Use `blender --command extension build/validate` as standard release validation workflow
- Keep tags, permissions consistent with Blender Extensions platform specifications

### 5.4 Documentation and Internationalization Sync Mechanism

- Clarify that new features must have documentation before entering main branch
- Establish stronger change checking for `translations.json`
- Keep terminology consistent between developer and user documentation
- **Vibecode Iteration Model**: Solidify rapid prototyping with AI assistance into a hardened development workflow

## 6. Long-term Direction

Long-term, BakeTool's more valuable direction is not becoming "another all-encompassing material system", but becoming a reusable, scriptable, verifiable Blender baking middleware layer. Possible long-term goals include:

- More stable public API
- More explicit automation and headless operation specifications
- Standardized output structure for project templates
- More complete crash recovery and task recovery strategies
- Organize complex baking context into clearer external interfaces

## 7. Directions Not Currently Prioritized

The following items are not recommended for priority investment:

- Complex online service integration
- Task scheduling systems dependent on external databases or daemons
- Highly invasive UI visual refactoring
- New material inference mechanisms without sufficient testing

These directions either introduce additional dependencies or significantly expand the maintenance surface, not suitable for the 1.0 to 1.1 phase.

## 8. Version Advancement Conditions

### 8.1 Conditions for 1.0.0 Release

- Release checklist fully completed
- Key documentation consistent with code behavior
- Multi-version verification passed
- At least one critical suite passed on an LTS version
- Installation, basic baking, node baking, UDIM, export, and headless smoke testing completed

### 8.2 Conditions for Advancing to 1.1.0

- No persistent high-frequency blocking issues in 1.0 user feedback
- Automation suites can stably cover current core workflows
- Engine split plan has clear boundaries and regression test support

## 9. Conclusion

BakeTool's most correct direction now is not to pile on more new features, but to stably deliver the capabilities it already has. The success criteria for 1.0.0 is not "looking like a big version", but:

- Can install
- Can use
- Can verify
- Can explain
- Can locate problems

As long as these five points hold, BakeTool qualifies for official release. Then steady evolution around real feedback in 1.0.x and 1.1.x will be more rational than continuing to expand scope before release.
