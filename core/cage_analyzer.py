import bpy
import bmesh
from mathutils.bvhtree import BVHTree
from mathutils import Vector
import logging

logger = logging.getLogger(__name__)

class CageAnalyzer:
    @staticmethod
    def run_raycast_analysis(context, low_obj, high_objects, extrusion=0.1, auto_switch_vp=False):
        """
        Perform visual cage analysis.
        Highlights vertices on the low poly where rays fail to hit the high poly.
        """
        if not low_obj or low_obj.type != 'MESH' or not high_objects:
            return False, "Target or source objects invalid."

        depsgraph = context.evaluated_depsgraph_get()
        
        # 1. Build BVH Trees for High objects
        bvh_trees = []
        for obj in high_objects:
            if obj.type == 'MESH' and obj.hide_render == False:
                try:
                    bm = bmesh.new()
                    bm.from_object(obj, depsgraph)
                    bm.transform(obj.matrix_world)
                    bvh = BVHTree.FromBMesh(bm)
                    bvh_trees.append(bvh)
                    bm.free()
                except Exception as e:
                    logger.warning(f"Failed to build BVH for {obj.name}: {e}")
                    
        if not bvh_trees:
            return False, "No valid high poly geometry found."
            
        # 2. Iterate low obj vertices and raycast
        low_matrix = low_obj.matrix_world.copy()
        mesh = low_obj.data
        
        # Ensure working on Object Mode
        if context.object and context.object.mode != 'OBJECT':
            try: bpy.ops.object.mode_set(mode='OBJECT')
            except: pass

        # Deal with Vertex Colors (Color Attributes in 3.2+)
        vcol_name = "BT_CAGE_ERROR"
        
        # Compatibility layer: use color_attributes if available (Blender 3.2+)
        if hasattr(mesh, "color_attributes"):
            vcol = mesh.color_attributes.get(vcol_name)
            if not vcol:
                vcol = mesh.color_attributes.new(name=vcol_name, type='BYTE_COLOR', domain='CORNER')
            mesh.color_attributes.active = vcol
            color_data = vcol.data
        else:
            # Fallback for <3.2
            vcol = mesh.vertex_colors.get(vcol_name)
            if not vcol:
                vcol = mesh.vertex_colors.new(name=vcol_name)
            mesh.vertex_colors.active = vcol
            color_data = vcol.data
        
        error_count = 0
        total_verts = len(mesh.vertices)
        vert_errors = [False] * total_verts
        
        for v in mesh.vertices:
            world_co = low_matrix @ v.co
            world_no = (low_matrix.to_3x3() @ v.normal).normalized()
            
            # Cage shoots ray INWARDS (from extrude pos towards original pos)
            ray_origin = world_co + (world_no * extrusion)
            ray_dir = -world_no
            
            hit_any = False
            for bvh in bvh_trees:
                location, normal, index, distance = bvh.ray_cast(ray_origin, ray_dir)
                # Give some tolerance. The ray travels inwards, typically 
                # should hit within extrusion distance, maybe slight penetration (max 2*extrusion)
                if location and distance <= extrusion * 2.5: 
                    hit_any = True
                    break
                    
            if not hit_any:
                vert_errors[v.index] = True
                error_count += 1
                
        # Apply colors to loops
        for poly in mesh.polygons:
            for loop_index in poly.loop_indices:
                v_idx = mesh.loops[loop_index].vertex_index
                if vert_errors[v_idx]:
                    color_data[loop_index].color = (1.0, 0.0, 0.0, 1.0) # Red
                else:
                    color_data[loop_index].color = (1.0, 1.0, 1.0, 1.0) # White
                    
        # 3. Viewport Feedback
        if auto_switch_vp:
            bpy.ops.object.select_all(action='DESELECT')
            low_obj.select_set(True)
            context.view_layer.objects.active = low_obj
            try:
                bpy.ops.object.mode_set(mode='VERTEX_PAINT')
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                space.shading.type = 'SOLID'
                                space.shading.color_type = 'VERTEX'
            except Exception as e:
                logger.warning(f"Failed to switch Viewport to Vertex Paint: {e}")
                
        return True, f"Found {error_count} potential baking errors out of {total_verts} vertices."
