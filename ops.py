"""Operator definitions for BakeTool.

This module contains all Blender Operators used by the BakeTool add-on,
handling UI interactions, baking orchestration, and data management.
"""

import bpy
from bpy import props
import logging
import os
import traceback
import json
from pathlib import Path
from typing import Optional, List, Set, Any, Dict

from .core.common import (
    apply_baked_result,
    safe_context_override,
    reset_channels_logic,
    check_objects_uv,
    log_error,
)
from .core.image_manager import set_image, save_image
from .core.uv_manager import UVLayoutManager, detect_object_udim_tile
from .core.node_manager import NodeGraphHandler
from .core.math_utils import pack_channels_numpy
from .core.engine import (
    BakeStep,
    BakeTask,
    TaskBuilder,
    JobPreparer,
    BakeContextManager,
    BakePassExecutor,
    ModelExporter,
    BakeStepRunner,
)
from .core.execution import BakeModalOperator
from .core import compat
from . import preset_handler
from .constants import UI_MESSAGES
from .state_manager import BakeStateManager

logger = logging.getLogger(__name__)


class _DummyEvent:
    """Mock event object for script-based operator invocations.

    Attributes:
        event_type (str): Type of event.
        event_value (str): Value of event (e.g., 'PRESS').
        mouse_x (int): X coordinate of mouse.
        mouse_y (int): Y coordinate of mouse.
    """

    event_type: str = "NONE"
    event_value: str = "PRESS"
    mouse_x: int = 0
    mouse_y: int = 0
    shift: bool = False
    ctrl: bool = False
    alt: bool = False
    oskey: bool = False


# --- Operators ---


class BAKETOOL_OT_RunDevTests(bpy.types.Operator):
    """Run all internal test suites and report results to UI.

    Iterates through all registered test suites and executes them using
    unittest, providing feedback to the user via the sidebar.
    """

    bl_idname = "bake.run_dev_tests"
    bl_label = "Run Development Tests"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Execute the full test suite.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'}.
        """
        import unittest
        import io
        from .test_cases import (
            suite_unit,
            suite_shading,
            suite_negative,
            suite_memory,
            suite_export,
            suite_api,
            suite_cleanup,
            suite_code_review,
            suite_compat,
            suite_context_lifecycle,
            suite_denoise,
            suite_parameter_matrix,
            suite_preset,
            suite_production_workflow,
            suite_udim_advanced,
            suite_ui_logic,
            suite_verification,
        )

        loader = unittest.TestLoader()
        suites = [
            loader.loadTestsFromTestCase(suite_unit.SuiteUnit),
            loader.loadTestsFromTestCase(suite_shading.SuiteShading),
            loader.loadTestsFromTestCase(suite_negative.SuiteNegative),
            loader.loadTestsFromTestCase(suite_memory.SuiteMemory),
            loader.loadTestsFromTestCase(suite_memory.SuiteMemoryIntegration),
            loader.loadTestsFromTestCase(suite_export.SuiteExport),
            loader.loadTestsFromTestCase(suite_code_review.SuiteCodeReviewFixes),
            loader.loadTestsFromTestCase(suite_verification.SuiteVerification),
            loader.loadTestsFromTestCase(suite_compat.SuiteCompat),
            loader.loadTestsFromTestCase(suite_context_lifecycle.SuiteContextLifecycle),
            loader.loadTestsFromTestCase(suite_denoise.SuiteDenoise),
            loader.loadTestsFromTestCase(suite_preset.SuitePreset),
            loader.loadTestsFromTestCase(
                suite_production_workflow.SuiteProductionWorkflow
            ),
            loader.loadTestsFromTestCase(suite_udim_advanced.SuiteUDIMAdvanced),
            loader.loadTestsFromTestCase(suite_ui_logic.SuiteUILogic),
        ]

        try:
            suites.append(loader.loadTestsFromTestCase(suite_api.SuiteAPI))
        except (AttributeError, ImportError):
            pass
        try:
            suites.append(loader.loadTestsFromTestCase(suite_cleanup.SuiteCleanup))
        except (AttributeError, ImportError):
            pass
        try:
            suites.append(
                loader.loadTestsFromTestCase(suite_parameter_matrix.SuiteParameterMatrix)
            )
        except (AttributeError, ImportError):
            pass

        consolidated = unittest.TestSuite(suites)

        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=1)
        result = runner.run(consolidated)

        info = f"Ran {result.testsRun} tests. {len(result.errors)} Errors, {len(result.failures)} Fails."
        context.scene.last_test_info = info
        context.scene.test_pass = result.wasSuccessful()

        if result.wasSuccessful():
            self.report({"INFO"}, f"All {result.testsRun} tests passed!")
        else:
            self.report({"ERROR"}, f"Tests Failed: {info}")

        return {"FINISHED"}


class BAKETOOL_OT_BakeOperator(bpy.types.Operator, BakeModalOperator):
    """Executes the texture baking process for selected objects.

    This operator handles the complete baking pipeline including
    validation, UV preparation, task building, and result saving.
    Uses modal execution for progress tracking and crash recovery.
    """

    bl_label = "Bake"
    bl_idname = "bake.bake_operator"

    is_resume: props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Ensure no other bake process is running.

        Returns:
            bool: True if baking can start.
        """
        return not context.scene.is_baking

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        """Initialize the bake queue and start modal execution.

        Args:
            context: Blender context.
            event: Event that triggered the invocation.

        Returns:
            Set[str]: {'RUNNING_MODAL'} or {'CANCELLED'}.
        """
        if context.object and context.object.mode != "OBJECT":
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except (RuntimeError, AttributeError):
                pass
        try:
            enabled_jobs = [j for j in context.scene.BakeJobs.jobs if j.enabled]
            if not enabled_jobs:
                self.report({"WARNING"}, UI_MESSAGES["NO_JOBS"])
                return {"CANCELLED"}

            self.bake_queue = JobPreparer.prepare_execution_queue(context, enabled_jobs)

            if not self.bake_queue:
                self.report({"WARNING"}, "Nothing to bake (Check logs/setup).")
                return {"CANCELLED"}

            start_idx = 0
            if self.is_resume:
                mgr = BakeStateManager()
                if mgr.has_crash_record():
                    data = mgr.read_log()
                    if data:
                        start_idx = data.get("current_queue_idx", 0)

        except (RuntimeError, ValueError) as e:
            err_msg = UI_MESSAGES.get(
                "PREP_FAILED", "Bake preparation failed: {0}"
            ).format(str(e))
            self.report({"ERROR"}, err_msg)
            log_error(context, err_msg, include_traceback=True)
            return {"CANCELLED"}

        return self.init_modal(context, start_idx=start_idx)


class BAKETOOL_OT_QuickBake(bpy.types.Operator, BakeModalOperator):
    """Bake current selection using active job settings immediately.

    This operator provides quick baking for the current object selection
    using the active job as a template, without requiring full job setup.
    """

    bl_idname = "bake.quick_bake"
    bl_label = "Quick Bake Selected"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Support non-interactive execution.

        Args:
            context: Blender context.

        Returns:
            Set[str]: Result of invocation.
        """
        return self.invoke(context, _DummyEvent())

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        """Prepare quick bake queue and start modal.

        Args:
            context: Blender context.
            event: Triggering event.

        Returns:
            Set[str]: Modal result.
        """
        if not hasattr(context.scene, "BakeJobs"):
            self.report({"ERROR"}, "BakeTool properties not initialized.")
            return {"CANCELLED"}

        bj = context.scene.BakeJobs
        if not bj.jobs:
            self.report({"WARNING"}, "No Job settings available as template.")
            return {"CANCELLED"}

        if bj.job_index < 0 or bj.job_index >= len(bj.jobs):
            bj.job_index = 0

        job = bj.jobs[bj.job_index]
        sel_objs = [o for o in context.selected_objects if o.type == "MESH"]
        act_obj = (
            context.active_object
            if (context.active_object and context.active_object.type == "MESH")
            else None
        )

        if not sel_objs:
            self.report({"WARNING"}, "Select mesh objects to bake.")
            return {"CANCELLED"}

        try:
            self.bake_queue = JobPreparer.prepare_quick_bake_queue(
                context, job, sel_objs, act_obj
            )

            if not self.bake_queue:
                self.report({"WARNING"}, UI_MESSAGES["QUICK_PREP_FAILED"])
                return {"CANCELLED"}

        except (RuntimeError, ValueError) as e:
            err_msg = f"Quick Bake preparation failed: {str(e)}"
            self.report({"ERROR"}, err_msg)
            log_error(context, err_msg, include_traceback=True)
            return {"CANCELLED"}

        return self.init_modal(context)


class BAKETOOL_OT_ResetChannels(bpy.types.Operator):
    """Reset bake channels to default configuration based on bake type."""

    bl_idname = "bake.reset_channels"
    bl_label = "Reset"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Sync channels for the active job.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'}.
        """
        bj = context.scene.BakeJobs
        if not bj.jobs:
            return {"CANCELLED"}
        if bj.job_index >= 0 and bj.job_index < len(bj.jobs):
            reset_channels_logic(bj.jobs[bj.job_index].setting)
        else:
            bj.job_index = 0
            if bj.jobs:
                reset_channels_logic(bj.jobs[0].setting)
        return {"FINISHED"}


class BAKETOOL_OT_GenericChannelOperator(bpy.types.Operator):
    """Generic operator for list operations (add, delete, move, clear)."""

    bl_idname = "bake.generic_channel_op"
    bl_label = "Op"

    action_type: props.EnumProperty(
        name="Action",
        items=[
            ("ADD", "Add", "Add a new custom channel"),
            ("DELETE", "Delete", "Remove the selected item"),
            ("UP", "Up", "Move current item up"),
            ("DOWN", "Down", "Move current item down"),
            ("CLEAR", "Clear", "Remove all items"),
        ],
    )
    target: props.StringProperty()

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Delegate channel management to logic helper.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        from .core.common import manage_channels_logic

        success, err = manage_channels_logic(
            self.target, self.action_type, context.scene.BakeJobs
        )
        if not success:
            self.report({"ERROR"}, err)
            return {"CANCELLED"}
        return {"FINISHED"}


class BAKETOOL_OT_SetSaveLocal(bpy.types.Operator):
    """Set save path to the current blend file directory."""

    bl_idname = "bake.set_save_local"
    bl_label = "Local"
    save_location: props.IntProperty(default=0)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Resolve current file path and apply to settings.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        if not bpy.data.filepath:
            self.report({"WARNING"}, "Save your file first to use relative paths.")
            return {"CANCELLED"}

        path = str(Path(bpy.data.filepath).parent) + os.sep
        bj = context.scene.BakeJobs

        if self.save_location == 0:
            if bj.job_index >= 0 and bj.job_index < len(bj.jobs):
                bj.jobs[bj.job_index].setting.external_save_path = path
            else:
                self.report({"WARNING"}, "Select a job first.")
                return {"CANCELLED"}
        elif self.save_location == 2:
            bj.node_bake_settings.external_save_path = path
        else:
            self.report({"WARNING"}, "Invalid save target.")
            return {"CANCELLED"}

        return {"FINISHED"}


class BAKETOOL_OT_RefreshUDIM(bpy.types.Operator):
    """Refresh UDIM tile assignments for all objects in the job."""

    bl_idname = "bake.refresh_udim_locations"
    bl_label = "Refresh / Repack UDIMs"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Detect or repack UDIM tiles for objects in the active job.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        bj = context.scene.BakeJobs
        if not (bj.jobs and bj.job_index >= 0 and bj.job_index < len(bj.jobs)):
            self.report({"WARNING"}, "No active job selected.")
            return {"CANCELLED"}

        s = bj.jobs[bj.job_index].setting
        objs = [o.bakeobject for o in s.bake_objects if o.bakeobject]
        if not objs:
            self.report({"WARNING"}, "No objects assigned.")
            return {"CANCELLED"}
        from .core.engine import UDIMPacker

        if s.udim_mode == "REPACK":
            assignments = UDIMPacker.calculate_repack(objs)
        else:
            assignments = {o: detect_object_udim_tile(o) for o in objs}
        for bo in s.bake_objects:
            if bo.bakeobject in assignments:
                bo.udim_tile = assignments[bo.bakeobject]
        return {"FINISHED"}


class BAKETOOL_OT_ManageObjects(bpy.types.Operator):
    """Add, remove, or manage objects in the current bake job."""

    bl_idname = "bake.manage_objects"
    bl_label = "Manage Objects"
    bl_options = {"REGISTER", "UNDO"}
    action: props.EnumProperty(
        name="Action",
        items=[
            ("SET", "Set", "Replace list with selection"),
            ("ADD", "Add", "Add selection"),
            ("REMOVE", "Remove", "Remove selection"),
            ("CLEAR", "Clear", "Remove all"),
            ("SET_ACTIVE", "Set Active", "Set active object as target"),
            ("SMART_SET", "Smart Set", "Auto-assign by naming"),
        ],
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Handle object list modification.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        bj = context.scene.BakeJobs
        if not bj.jobs:
            self.report({"WARNING"}, "No jobs available.")
            return {"CANCELLED"}
        if bj.job_index < 0 or bj.job_index >= len(bj.jobs):
            bj.job_index = 0

        s = bj.jobs[bj.job_index].setting
        sel = [o for o in context.selected_objects if o.type == "MESH"]
        act = (
            context.active_object
            if (context.active_object and context.active_object.type == "MESH")
            else None
        )

        from .core.common import manage_objects_logic

        manage_objects_logic(s, self.action, sel, act)
        return {"FINISHED"}


class BAKETOOL_OT_SaveSetting(bpy.types.Operator):
    """Save current job settings to a JSON preset file."""

    bl_idname = "bake.save_setting"
    bl_label = "Save Preset"
    filepath: props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        """Open file browser.

        Args:
            context: Blender context.
            event: Triggering event.

        Returns:
            Set[str]: {'RUNNING_MODAL'}.
        """
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Serialize and write settings to disk.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        bj = context.scene.BakeJobs
        if not (bj.jobs and bj.job_index >= 0 and bj.job_index < len(bj.jobs)):
            self.report({"WARNING"}, "No active job to save")
            return {"CANCELLED"}

        data = preset_handler.PropertyIO(exclude_props={"active_channel_index"}).to_dict(
            bj
        )
        path = (
            self.filepath
            if self.filepath.endswith(".json")
            else self.filepath + ".json"
        )
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except (OSError, IOError) as e:
            self.report({"ERROR"}, f"Failed to save preset: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


class BAKETOOL_OT_LoadSetting(bpy.types.Operator):
    """Load job settings from a JSON preset file."""

    bl_idname = "bake.load_setting"
    bl_label = "Load Preset"
    filepath: props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        """Open file selector.

        Args:
            context: Blender context.
            event: Triggering event.

        Returns:
            Set[str]: {'RUNNING_MODAL'}.
        """
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Read and apply settings from disk.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            preset_handler.PropertyIO().from_dict(context.scene.BakeJobs, data)
        except (OSError, IOError, json.JSONDecodeError) as e:
            self.report({"ERROR"}, f"Failed to load preset: {e}")
            return {"CANCELLED"}
        return {"FINISHED"}


class BAKETOOL_OT_RefreshPresets(bpy.types.Operator):
    """Scan library path and load thumbnails."""

    bl_idname = "bake.refresh_presets"
    bl_label = "Refresh Preset Library"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Trigger thumbnail scanning and loading.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'}.
        """
        from .core import thumbnail_manager

        prefs = context.preferences.addons[__package__].preferences
        if prefs.library_path:
            thumbnail_manager.load_preset_thumbnails(prefs.library_path)
            self.report({"INFO"}, f"Library refreshed from: {prefs.library_path}")
        else:
            self.report({"WARNING"}, "Library path not set.")
        return {"FINISHED"}


class BAKETOOL_OT_BakeSelectedNode(bpy.types.Operator):
    """Bake the active shader node to an image."""

    bl_label = "Bake Node"
    bl_idname = "bake.selected_node_bake"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Bake the selected node to image.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        from .core.node_manager import bake_node_to_image

        nbs = context.scene.BakeJobs.node_bake_settings
        if not context.active_object:
            self.report({"WARNING"}, "No active object")
            return {"CANCELLED"}

        mat = context.active_object.active_material
        node = getattr(context, "active_node", None)

        if not mat:
            self.report({"WARNING"}, "No material found")
            return {"CANCELLED"}
        if not node:
            self.report({"WARNING"}, "No node selected")
            return {"CANCELLED"}

        img = bake_node_to_image(context, mat, node, nbs)

        if img:
            self.report({"INFO"}, f"Baked node to {img.name}")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, "Node baking failed")
            return {"CANCELLED"}


class BAKETOOL_OT_DeleteResult(bpy.types.Operator):
    """Delete the currently selected baked result."""

    bl_idname = "baketool.delete_result"
    bl_label = "Delete"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Remove result item and its image datablock.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'}.
        """
        results = context.scene.baked_image_results
        idx = context.scene.baked_image_results_index
        if 0 <= idx < len(results):
            r = results[idx]
            img = r.image
            results.remove(idx)
            context.scene.baked_image_results_index = max(0, idx - 1)
            if img:
                if img.users == 0:
                    try:
                        bpy.data.images.remove(img, do_unlink=True)
                    except (ReferenceError, RuntimeError) as e:
                        logger.debug(f"Failed to remove image: {e}")
                else:
                    img.use_fake_user = False
        return {"FINISHED"}


class BAKETOOL_OT_DeleteAllResults(bpy.types.Operator):
    """Delete all baked results and their associated images."""

    bl_idname = "baketool.delete_all_results"
    bl_label = "Delete All"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Clear the results collection and remove orphan images.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'}.
        """
        results = context.scene.baked_image_results
        images = [r.image for r in results if r.image]

        results.clear()

        for img in images:
            if img.users == 0:
                try:
                    bpy.data.images.remove(img, do_unlink=True)
                except (ReferenceError, RuntimeError):
                    pass
            else:
                img.use_fake_user = False

        return {"FINISHED"}


class BAKETOOL_OT_ExportResult(bpy.types.Operator):
    """Export the selected baked result to disk."""

    bl_idname = "baketool.export_result"
    bl_label = "Export"
    filepath: props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        """Select export location.

        Args:
            context: Blender context.
            event: Triggering event.

        Returns:
            Set[str]: {'RUNNING_MODAL'}.
        """
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Save image to the selected path.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        results = context.scene.baked_image_results
        idx = context.scene.baked_image_results_index
        if 0 <= idx < len(results):
            r = results[idx]
            if r.image:
                export_dir = os.path.dirname(self.filepath)
                if not os.path.exists(export_dir):
                    try:
                        os.makedirs(export_dir)
                    except OSError:
                        self.report({"ERROR"}, "Could not create directory")
                        return {"CANCELLED"}
                save_image(r.image, export_dir)
                self.report({"INFO"}, f"Exported {r.image.name}")
            else:
                return {"CANCELLED"}
        return {"FINISHED"}


class BAKETOOL_OT_ExportAllResults(bpy.types.Operator):
    """Export all baked results to a directory."""

    bl_idname = "baketool.export_all_results"
    bl_label = "Export All"
    directory: props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        """Select target directory.

        Args:
            context: Blender context.
            event: Triggering event.

        Returns:
            Set[str]: {'RUNNING_MODAL'}.
        """
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Iterate and save all images.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'}.
        """
        for r in context.scene.baked_image_results:
            if r.image:
                save_image(r.image, self.directory)
        return {"FINISHED"}


class BAKETOOL_OT_ClearCrashLog(bpy.types.Operator):
    """Clear the crash warning and reset bake state."""

    bl_idname = "bake.clear_crash_log"
    bl_label = "Dismiss Warning"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Remove persistent crash record.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'}.
        """
        try:
            BakeStateManager().finish_session(context)
        except (OSError, RuntimeError) as e:
            logger.error(f"Failed to clear log: {e}")
        return {"FINISHED"}


class BAKETOOL_OT_TogglePreview(bpy.types.Operator):
    """Toggle interactive packing preview in the viewport."""

    bl_idname = "bake.toggle_preview"
    bl_label = "Toggle Preview"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Apply or remove viewport preview material.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        bj = context.scene.BakeJobs
        if not bj.jobs:
            return {"CANCELLED"}
        job = bj.jobs[bj.job_index]
        s = job.setting

        from .core import shading

        s.use_preview = not s.use_preview
        objs = [o.bakeobject for o in s.bake_objects if o.bakeobject]

        if not objs:
            self.report({"WARNING"}, "No objects to preview")
            s.use_preview = False
            return {"CANCELLED"}

        for obj in objs:
            if s.use_preview:
                shading.apply_preview(obj, s)
            else:
                shading.remove_preview(obj)

        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()

        return {"FINISHED"}


class BAKETOOL_OT_AnalyzeCage(bpy.types.Operator):
    """Analyze cage overlap by raycasting high-poly onto low-poly."""

    bl_idname = "bake.analyze_cage"
    bl_label = "Analyze Cage Overlap"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Ensure active object is a mesh.

        Returns:
            bool: True if analysis is possible.
        """
        if not context.active_object:
            return False
        return context.active_object.type == "MESH"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Execute BVH-based raycast analysis.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        if not hasattr(context.scene, "BakeJobs"):
            return {"CANCELLED"}
        bj = context.scene.BakeJobs
        if not bj.jobs:
            return {"CANCELLED"}
        job = bj.jobs[bj.job_index]
        s = job.setting

        sel_objs = [o for o in context.selected_objects if o.type == "MESH"]
        act_obj = (
            context.active_object
            if (context.active_object and context.active_object.type == "MESH")
            else None
        )

        if s.bake_mode == "SELECT_ACTIVE":
            low = act_obj
            highs = [o for o in sel_objs if o != low]
        else:
            self.report({"WARNING"}, "Requires 'Selected to Active' mode.")
            return {"CANCELLED"}

        if not highs:
            self.report({"WARNING"}, "Select high poly objects first.")
            return {"CANCELLED"}

        from .core.cage_analyzer import CageAnalyzer

        success, msg = CageAnalyzer.run_raycast_analysis(
            context,
            low,
            highs,
            extrusion=s.extrusion,
            auto_switch_vp=s.auto_switch_vertex_paint,
        )
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class BAKETOOL_OT_OneClickPBR(bpy.types.Operator):
    """Setup standard PBR channels (Color, Roughness, Normal) for the job.

    Args:
        context: Blender context.

    Returns:
        Set[str]: {'FINISHED'} on success.
    """

    bl_idname = "bake.one_click_pbr"
    bl_label = "One-Click PBR Setup"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Ensure a job exists.

        Returns:
            bool: True if job is available.
        """
        if not hasattr(context.scene, "BakeJobs"):
            return False
        bj = context.scene.BakeJobs
        return len(bj.jobs) > 0

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Enable standard PBR channels.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'} or {'CANCELLED'}.
        """
        bj = context.scene.BakeJobs
        if bj.job_index < 0 or bj.job_index >= len(bj.jobs):
            return {"CANCELLED"}
        job = bj.jobs[bj.job_index]
        s = job.setting

        standards = {"color", "rough", "normal"}
        for c in s.channels:
            if c.id in standards:
                c.enabled = True

        self.report({"INFO"}, "Standard PBR channels enabled.")
        return {"FINISHED"}


class BAKETOOL_OT_OpenAddonPrefs(bpy.types.Operator):
    """Open Blender addon preferences for configuring dependencies."""

    bl_idname = "bake.open_addon_prefs"
    bl_label = "Addon Prefs"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Open user preferences.

        Args:
            context: Blender context.

        Returns:
            Set[str]: {'FINISHED'}.
        """
        bpy.ops.screen.userpref_show("INVOKE_DEFAULT")
        return {"FINISHED"}
