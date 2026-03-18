import unittest
import bpy
from .helpers import cleanup_scene, create_test_object, get_job_setting
from ..core import shading

class TestShadingPreview(unittest.TestCase):
    def setUp(self):
        cleanup_scene()
        self.obj = create_test_object("PreviewObj")
        self.setting = get_job_setting()

    def test_preview_lifecycle(self):
        """Verify that preview material is created, applied, and removed correctly."""
        s = self.setting
        obj = self.obj
        
        # 1. Apply Preview
        shading.apply_preview(obj, s)
        self.assertEqual(obj.active_material.name, shading.PREVIEW_MAT_NAME)
        self.assertIsNotNone(obj.get("_bt_orig_mat"), "Original material not stored")
        
        # 2. Check shader nodes (basic)
        nodes = obj.active_material.node_tree.nodes
        self.assertIn('ShaderNodeCombineColor', [n.bl_idname for n in nodes])
        
        # 3. Remove Preview
        shading.remove_preview(obj)
        self.assertNotEqual(obj.active_material.name, shading.PREVIEW_MAT_NAME)
        self.assertIsNone(obj.get("_bt_orig_mat"), "Original material marker not cleaned up")

    def test_no_objects_safety(self):
        """Ensure no crash when applying to None or non-mesh."""
        shading.apply_preview(None, self.setting) # Should not crash
        
        # Test with non-mesh object (Camera)
        cam_data = bpy.data.cameras.new("Cam")
        cam_obj = bpy.data.objects.new("CamObj", cam_data)
        bpy.context.collection.objects.link(cam_obj)
        shading.apply_preview(cam_obj, self.setting) # Should not crash
        self.assertIsNone(cam_obj.get("_bt_orig_mat"))
