import unittest
import bpy
import inspect
from .. import get_classes

class TestRegistration(unittest.TestCase):
    def test_auto_discovery(self):
        """Verify that all essential classes are found by the discovery system."""
        classes = get_classes()
        
        # Check for core types
        class_names = [cls.__name__ for cls in classes]
        
        # Properties
        self.assertIn('BakeJobSetting', class_names)
        self.assertIn('BakeChannel', class_names)
        
        # Operators
        self.assertIn('BAKETOOL_OT_BakeOperator', class_names)
        self.assertIn('BAKETOOL_OT_TogglePreview', class_names) # New operator check
        
        # UI
        self.assertIn('BAKE_PT_BakePanel', class_names)
        
    def test_inheritance_filter(self):
        """Ensure only bpy.types subclasses are collected (except Preferences)."""
        # Define blender base types to look for
        blender_bases = (bpy.types.Operator, bpy.types.Panel, bpy.types.PropertyGroup, 
                         bpy.types.UIList, bpy.types.Menu, bpy.types.Header, 
                         bpy.types.AddonPreferences)

        classes = get_classes()
        for cls in classes:
            if cls.__name__ == 'BakeToolPreferences':
                continue
            
            # Check if it inherits from any Blender type
            has_blender_base = issubclass(cls, blender_bases)
            self.assertTrue(has_blender_base, f"Class {cls.__name__} does not inherit from bpy.types")
