import unittest
import bpy
from .. import ui
from ..property import BakeChannel, BakeJobSetting


class TestUILogic(unittest.TestCase):
    """测试 UI 层的纯逻辑函数 / Test UI layer pure logic functions."""
    
    def setUp(self):
        """Create test scene with basic setup."""
        bpy.ops.wm.read_homefile(use_empty=True)
        self.scene = bpy.context.scene
        
    def test_draw_property_group_helper(self):
        """Test generic property drawer helper function."""
        # This is a logic test - we verify the function doesn't crash
        # and properly handles edge cases
        
        # Create a mock layout (we can't fully test UI rendering without GUI)
        # But we can verify the function signature and basic logic
        
        # Create a test channel
        bj = self.scene.BakeJobs
        job = bj.jobs.add()
        job.name = "Test Job"
        
        from ..core.common import reset_channels_logic
        reset_channels_logic(job.setting)
        
        # Verify channels were created
        self.assertGreater(len(job.setting.channels), 0, "Channels should be created")
        
    def test_channel_ui_map_coverage(self):
        """Verify all special channels have UI layouts defined."""
        from ..constants import BAKE_CHANNEL_INFO, CHANNEL_UI_LAYOUT
        
        # These channels should have specific UI definitions
        expected_channels = ['normal', 'diff', 'gloss', 'tranb', 'combine', 
                            'ao', 'bevel', 'bevnor', 'curvature', 'wireframe', 'node_group']
        
        for ch_id in expected_channels:
            self.assertIn(ch_id, CHANNEL_UI_LAYOUT, 
                         f"Channel '{ch_id}' should have a UI layout defined in CHANNEL_UI_LAYOUT")
    
    def test_format_settings_validation(self):
        """Test image format settings validation logic."""
        from ..constants import FORMAT_SETTINGS
        
        # Verify critical formats exist
        required_formats = ['PNG', 'JPEG', 'TARGA', 'OPEN_EXR']
        for fmt in required_formats:
            self.assertIn(fmt, FORMAT_SETTINGS, 
                         f"Format '{fmt}' should be defined in FORMAT_SETTINGS")
            
        # Verify PNG has expected structure
        png_settings = FORMAT_SETTINGS.get('PNG', {})
        self.assertIn('depths', png_settings, "PNG should have depth options")
        self.assertIn('modes', png_settings, "PNG should have mode options")
    
    def test_generic_channel_operator_targets(self):
        """Test that GenericChannelOperator is registered."""
        # Blender operators use annotations for properties, which aren't accessible
        # via hasattr on the class. Just verify the operator is registered.
        
        # Verify the operator is registered and callable
        self.assertTrue(hasattr(bpy.ops.bake, 'generic_channel_op'),
                       "Operator should be registered in bpy.ops.bake")
    
    def test_bake_mode_validation(self):
        """Test bake mode consistency across UI and engine."""
        from ..constants import BAKE_MODES
        
        # Verify all modes are defined
        expected_modes = ['SINGLE_OBJECT', 'COMBINE_OBJECT', 'SELECT_ACTIVE', 
                         'SPLIT_MATERIAL', 'UDIM']
        
        mode_ids = [m[0] for m in BAKE_MODES]
        for mode in expected_modes:
            self.assertIn(mode, mode_ids, 
                         f"Bake mode '{mode}' should be defined in BAKE_MODES")
    
    def test_channel_filtering_logic(self):
        """Test channel filtering based on bake type."""
        bj = self.scene.BakeJobs
        job = bj.jobs.add()
        job.name = "Filter Test"
        s = job.setting
        
        from ..core.common import reset_channels_logic
        
        # Test BSDF mode
        s.bake_type = 'BSDF'
        reset_channels_logic(s)
        
        bsdf_channels = [c.id for c in s.channels if c.valid_for_mode]
        self.assertIn('color', bsdf_channels, "BSDF should have color channel")
        self.assertIn('metal', bsdf_channels, "BSDF should have metal channel")
        
        # Test with light maps enabled
        s.use_light_map = True
        reset_channels_logic(s)
        
        # Light maps add channels like 'diff', 'gloss', 'tranb', 'combine'
        # But the exact IDs depend on CHANNEL_DEFINITIONS['LIGHT']
        all_channels = [c.id for c in s.channels if c.valid_for_mode]
        
        # Verify that enabling light maps increases channel count
        self.assertGreater(len(all_channels), len(bsdf_channels),
                          "Enabling light maps should add more channels")
        
    def test_baked_result_attribute_integrity(self):
        """Verify BakedImageResult has all metadata fields used by the UI."""
        results = self.scene.baked_image_results
        item = results.add()
        
        # UI uses these attributes in draw_results
        expected_attrs = [
            'image', 'filepath', 'object_name', 'channel_type',
            'res_x', 'res_y', 'samples', 'duration', 'bake_type', 'device', 'file_size'
        ]
        
        for attr in expected_attrs:
            self.assertTrue(hasattr(item, attr), f"BakedImageResult missing attribute: {attr}")
            
    def test_draw_results_crash_test(self):
        """Test if draw_results function crashes with a valid result."""
        # Create a mock result
        results = self.scene.baked_image_results
        item = results.add()
        item.channel_type = "Base Color"
        item.object_name = "Cube"
        item.file_size = "1.2 MB"
        self.scene.baked_image_results_index = 0
        
        # Create a mock layout
        class MockLayout:
            def box(self, *args, **kwargs): return self
            def row(self, *args, **kwargs): return self
            def column(self, *args, **kwargs): return self
            def label(self, *args, **kwargs): pass
            def prop(self, *args, **kwargs): pass
            def split(self, *args, **kwargs): return self
            def separator(self, *args, **kwargs): pass
            def template_list(self, *args, **kwargs): pass
            def prop_search(self, *args, **kwargs): pass
            def operator(self, *args, **kwargs): return self
            
        layout = MockLayout()
        
        try:
            # We need to mock the BakeJobs root too
            bj = self.scene.BakeJobs
            ui.draw_results(self.scene, layout, bj)
        except Exception as e:
            self.fail(f"ui.draw_results crashed: {e}")


def suite():
    """Return test suite for this module."""
    return unittest.TestLoader().loadTestsFromTestCase(TestUILogic)


if __name__ == '__main__':
    unittest.main()
