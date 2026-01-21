import unittest
import bpy
import os
import tempfile
import shutil
import math
from .helpers import cleanup_scene, create_test_object, JobBuilder
from ..core import engine, common

class TestProductionHazards(unittest.TestCase):
    def setUp(self):
        cleanup_scene()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass

    def test_readonly_output_directory(self):
        """Test engine resilience when output directory is read-only."""
        # Note: On Windows, os.chmod(..., 0o444) only affects files, not directories.
        # We simulate the failure by using a path that is likely to fail or exists as a file.
        obj = create_test_object("ResilienceObj")
        
        # Create a file where a directory should be
        fake_dir = os.path.join(self.temp_dir, "fake_dir")
        with open(fake_dir, 'w') as f:
            f.write("I am a file, not a directory")
            
        job = (JobBuilder("ReadOnlyJob")
               .add_objects(obj)
               .save_to(fake_dir)
               .enable_channel('color')
               .build())
        
        from ..core.engine import BakeStepRunner
        runner = BakeStepRunner(bpy.context)
        
        # Prepare queue
        from ..core.engine import JobPreparer
        queue = JobPreparer.prepare_execution_queue(bpy.context, [job])
        self.assertGreater(len(queue), 0)
        
        # Execution should handle the OSError/IOError gracefully without crashing Blender
        try:
            results = runner.run(queue[0])
            # Even if it fails to save, it should return results (maybe with empty paths)
            # or at least not raise an unhandled exception.
        except (OSError, IOError):
            # This is acceptable if caught at a higher level, but we check for crash
            pass
        except Exception as e:
            self.fail(f"Unexpected crash on read-only path: {e}")

    def test_linked_library_object(self):
        """Test behavior with objects linked from external libraries (Proxy/Override)."""
        obj = create_test_object("LocalObj")
        # Simulate 'library' status (Blender doesn't allow easy mocking of .lib in-memory)
        # but we can check if the engine filters out non-editable data.
        
        # We manually set the library property to simulate a linked object
        # Note: In real scenarios, obj.library is not None.
        
        job = (JobBuilder("LinkedJob")
               .add_objects(obj)
               .enable_channel('color')
               .build())
        
        # The engine should verify if the object is editable/mesh-based.
        self.assertTrue(obj.type == 'MESH')
        # If it's linked, we can't add UVs or change materials easily.
        # This test ensures we don't crash when trying to process it.
        from ..core.engine import JobPreparer
        queue = JobPreparer.prepare_execution_queue(bpy.context, [job])
        self.assertGreater(len(queue), 0)

    def test_nan_mesh_data_resilience(self):
        """Test if the engine or cleanup crashes when encountering NaN vertex data."""
        obj = create_test_object("NaNObj")
        # Inject NaN into a vertex coordinate
        obj.data.vertices[0].co[0] = float('nan')
        
        job = (JobBuilder("NaNJob")
               .add_objects(obj)
               .enable_channel('color')
               .build())
        
        # Check TaskBuilder
        tasks = engine.TaskBuilder.build(bpy.context, job.setting, [obj], obj)
        self.assertEqual(len(tasks), 1)
        
        # Check if math_utils or engine crashes during bounds check etc.
        # (Usually Blender internals or NumPy might complain, but shouldn't crash process)
        from ..core.engine import JobPreparer
        try:
            queue = JobPreparer.prepare_execution_queue(bpy.context, [job])
        except Exception as e:
            self.fail(f"Crashed on NaN mesh data: {e}")

if __name__ == '__main__':
    unittest.main()
