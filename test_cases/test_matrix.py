import unittest
import bpy
import os
from .helpers import cleanup_scene, create_test_object, get_job_setting, JobBuilder
from ..core import common, engine
from ..constants import BAKE_MODES, BAKE_TYPES, BAKE_CHANNEL_INFO

class TestExhaustiveMatrix(unittest.TestCase):
    """
    Exhaustive traversal of Bake Modes and Bake Types.
    Validates task generation, channel collection, and naming consistency.
    """
    
    def setUp(self):
        cleanup_scene()
        self.obj = create_test_object("MatrixCube")
        self.setting = get_job_setting()

    def test_mode_type_traversal(self):
        """Test all combinations of Modes and Types for basic task generation."""
        for mode_id, mode_name, _, _ in BAKE_MODES:
            for type_id, type_name, _, _ in BAKE_TYPES:
                with self.subTest(mode=mode_id, type=type_id):
                    self.setting.bake_mode = mode_id
                    self.setting.bake_type = type_id
                    common.reset_channels_logic(self.setting)
                    
                    # Add object to job
                    self.setting.bake_objects.clear()
                    item = self.setting.bake_objects.add()
                    item.bakeobject = self.obj
                    
                    if mode_id == 'SELECT_ACTIVE':
                        self.setting.active_object = self.obj
                    
                    # Prepare tasks
                    from ..ops import JobPreparer
                    # Mock job object
                    class MockJob:
                        def __init__(self, setting):
                            self.setting = setting
                            self.name = "TestJob"
                            self.custom_bake_channels = []
                    
                    steps = JobPreparer.prepare_execution_queue(bpy.context, [MockJob(self.setting)])
                    self.assertGreater(len(steps), 0, f"No tasks generated for {mode_id}/{type_id}")
                    
                    for step in steps:
                        task = step.task
                        # Basic integrity checks
                        self.assertIsNotNone(task.base_name)
                        self.assertGreater(len(step.channels), 0)
                        
                        # Channel Correspondence Check
                        collected_ids = {c['id'] for c in step.channels}
                        
                        # Determine expected IDs from constants
                        ver_key = ('BSDF_4' if bpy.app.version >= (4, 0, 0) else 'BSDF_3') if type_id == 'BSDF' else type_id
                        expected_defs = BAKE_CHANNEL_INFO.get(ver_key, [])
                        expected_ids = {d['id'] for d in expected_defs}
                        
                        # Only check if enabled/valid logic holds (JobPreparer filters)
                        # By default common.reset_channels_logic enables some.
                        # Let's verify no "ghost" channels exist.
                        for c_id in collected_ids:
                            self.assertIn(c_id, expected_ids, f"Ghost channel {c_id} found in {type_id} mode")

    def test_naming_consistency_matrix(self):
        """Verify naming patterns across different modes."""
        self.setting.name_setting = 'OBJECT'
        modes_to_test = ['SINGLE_OBJECT', 'COMBINE_OBJECT', 'SELECT_ACTIVE']
        
        for mode in modes_to_test:
            self.setting.bake_mode = mode
            name = common.get_safe_base_name(self.setting, self.obj, self.obj.data.materials[0])
            self.assertEqual(name, self.obj.name, f"Naming failed for mode {mode}")

    def test_udim_task_separation(self):
        """Verify UDIM task configuration logic."""
        self.setting.bake_mode = 'UDIM'
        self.setting.udim_mode = 'CUSTOM'
        # Setup manual tile in objects
        self.setting.bake_objects.clear()
        bo = self.setting.bake_objects.add()
        bo.bakeobject = self.obj
        bo.udim_tile = 1002
        
        tasks = engine.TaskBuilder.build(bpy.context, self.setting, [self.obj], self.obj)
        self.assertEqual(len(tasks), 1)
        
        # Verify UDIM configuration logic
        tiles = engine.BakePassExecutor.get_udim_configuration(self.setting, [self.obj])
        self.assertIn(1002, tiles)

    def test_split_material_task_separation(self):
        """Verify SPLIT_MATERIAL mode creates tasks per material slot."""
        # Add another material slot
        mat2 = bpy.data.materials.new(name="Mat2")
        self.obj.data.materials.append(mat2)
        
        self.setting.bake_mode = 'SPLIT_MATERIAL'
        tasks = engine.TaskBuilder.build(bpy.context, self.setting, [self.obj], self.obj)
        self.assertEqual(len(tasks), 2)
        names = [t.base_name for t in tasks]
        self.assertIn(f"{self.obj.name}_{self.obj.data.materials[0].name}", names)
        self.assertIn(f"{self.obj.name}_{mat2.name}", names)

    def test_select_active_mapping(self):
        """Verify SELECT_ACTIVE correctly assigns source objects to active task."""
        high = create_test_object("High")
        low = create_test_object("Low")
        
        self.setting.bake_mode = 'SELECT_ACTIVE'
        self.setting.active_object = low
        self.setting.bake_objects.clear()
        item = self.setting.bake_objects.add()
        item.bakeobject = high
        
        tasks = engine.TaskBuilder.build(bpy.context, self.setting, [high], low)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].active_obj, low)
        self.assertIn(high, tasks[0].objects)

if __name__ == '__main__':
    unittest.main()
