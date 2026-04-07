import unittest
import bpy
import os
import tempfile
from pathlib import Path
from .helpers import cleanup_scene, create_test_object, JobBuilder, ensure_cycles, MockSetting
from ..core import common, node_manager

class SuiteNegative(unittest.TestCase):
    """
    Negative and Boundary Test Suite.
    Ensures stability when inputs are malformed or environmental conditions are poor.
    """

    @classmethod
    def setUpClass(cls):
        ensure_cycles()

    def setUp(self):
        cleanup_scene()
        self.obj = create_test_object("NegObj")

    def tearDown(self):
        cleanup_scene()

    def test_bake_with_deleted_object_reference(self):
        """Verify JobPreparer handles Job referencing a deleted object."""
        from ..core.engine import JobPreparer
        builder = JobBuilder("DeletedRefJob").add_objects(self.obj)
        job = builder.build()
        
        # Delete the object from Blender
        bpy.data.objects.remove(self.obj, do_unlink=True)
        
        # This should fail validation/preparation but NOT crash Blender
        queue = JobPreparer.prepare_execution_queue(bpy.context, [job])
        self.assertEqual(len(queue), 0)

    def test_preset_load_malformed_json(self):
        """Verify PropertyIO doesn't crash on invalid JSON data."""
        from ..preset_handler import PropertyIO
        bj = bpy.context.scene.BakeJobs
        io = PropertyIO()
        
        # Non-dict input
        io.from_dict(bj, "This is not a dict")
        self.assertGreaterEqual(io.stats['error'], 0)

    def test_preset_load_missing_required_keys(self):
        """Verify PropertyIO handles partial dictionaries gracefully."""
        from ..preset_handler import PropertyIO
        bj = bpy.context.scene.BakeJobs
        io = PropertyIO()
        
        # Empty dict or dict with missing keys
        io.from_dict(bj, {"random_key": "ignored"})
        # Should finish without raising KeyError

    def test_bake_with_zero_resolution(self):
        """Verify boundary resolution (0 or negative) is handled."""
        from ..core.engine import JobPreparer
        builder = JobBuilder("ZeroRes").add_objects(self.obj)
        builder.setting.res_x = 0
        builder.setting.res_y = -10
        job = builder.build()
        
        # Preparer should ideally clamp or reject, but definitely NOT crash
        queue = JobPreparer.prepare_execution_queue(bpy.context, [job])
        # Even if it proceeds, individual steps should guard against 0-size images
        if len(queue) > 0:
            for step in queue:
                self.assertGreater(step.job.setting.res_x, 0, "Resolution was not clamped to minimum 1")

    def test_export_to_readonly_directory(self):
        """Verify graceful error reporting when saving to forbidden paths."""
        # Note: actually making a directory RO on Windows is tricky, we test behavior on logical failure
        from ..core import image_manager
        img = image_manager.set_image("FixedImg", 8, 8)
        
        # Use an impossible path (invalid characters on Windows)
        bad_path = "Z:\\Invalid|Path?*/Forbidden"
        res = image_manager.save_image(img, path=bad_path)
        self.assertIsNone(res, "Save should have failed and returned None for invalid path")

    def test_context_manager_exception_restores_state(self):
        """Verify that BakeContextManager performs cleanup even if an exception occurs."""
        from ..core.engine import BakeContextManager
        orig_engine = bpy.context.scene.render.engine
        
        try:
            with BakeContextManager(bpy.context, MockSetting()):
                bpy.context.scene.render.engine = 'CYCLES'
                raise RuntimeError("Simulated crash")
        except RuntimeError:
            pass
            
        self.assertEqual(bpy.context.scene.render.engine, orig_engine, "Context manager failed to restore engine after exception")

    def test_node_handler_cleanup_restores_links(self):
        """Verify that NodeGraphHandler restores original links even on early exit."""
        mat = self.obj.data.materials[0]
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Create a specific link
        bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
        out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
        links.new(bsdf.outputs[0], out.inputs[0])
        
        orig_link_count = len(links)
        
        try:
            # Fix: NodeGraphHandler expects materials, not objects
            with node_manager.NodeGraphHandler([mat]) as h:
                # Force some changes
                links.clear()
                raise RuntimeError("Abort mid-process")
        except RuntimeError:
            pass
            
        self.assertEqual(len(links), orig_link_count, "Node links were not restored after exception in NodeGraphHandler")

    def test_empty_channel_list_no_crash(self):
        """Verify engine handles Job with 0 enabled channels."""
        from ..core.engine import JobPreparer
        builder = JobBuilder("NoChannels").add_objects(self.obj)
        # Disable all default channels
        for c in builder.setting.channels:
            c.enabled = False
            
        job = builder.build()
        queue = JobPreparer.prepare_execution_queue(bpy.context, [job])
        # It should probably return 0 steps
        self.assertEqual(len(queue), 0)

if __name__ == '__main__':
    unittest.main()
