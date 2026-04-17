"""
Blender Version Compatibility Layer
Centralizes all version-specific API differences to improve maintainability.
Supports Blender 3.6 - 5.0+
"""
import bpy
import logging

logger = logging.getLogger(__name__)

# Version Detection
def is_blender_5():
    return bpy.app.version >= (5, 0, 0)

def is_blender_4():
    return bpy.app.version >= (4, 0, 0) and bpy.app.version < (5, 0, 0)

def is_blender_3():
    return bpy.app.version >= (3, 0, 0) and bpy.app.version < (4, 0, 0)

def get_bake_settings(scene):
    """
    Get bake settings object in a version-safe way.
    
    Blender 4.0+ moved/added bake settings in scene.render.bake
    Returns: The bake settings object or None if not available
    """
    if hasattr(scene.render, "bake"):
        return scene.render.bake
    # Legacy: settings are directly on scene.render
    return scene.render


BAKE_MAPPING = {
    'EMIT': 'EMISSION',
    'DIFFUSE': 'DIFFUSE',
    'NORMAL': 'NORMALS' # Version-aware logic moved to set_bake_type if needed
}

def get_compositor_tree(scene):
    """
    Version-safe compositor node tree accessor.
    Blender 5.0 introduces scene.compositor and renames node_tree.
    """
    # 1. Blender 5.0+ Native Compositor Object
    if is_blender_5() or hasattr(scene, "compositor"):
        try:
            comp = getattr(scene, "compositor", None)
            if comp:
                if not comp.use_nodes:
                    comp.use_nodes = True
                if hasattr(comp, "node_tree") and comp.node_tree:
                    return comp.node_tree
        except Exception: pass

    # 2. Blender 5.0+ Renamed Property: compositing_node_group
    if hasattr(scene, "compositing_node_group"):
        try:
            if hasattr(scene, "use_nodes") and not scene.use_nodes:
                scene.use_nodes = True
            
            tree = getattr(scene, "compositing_node_group", None)
            
            # --- B5.0 Background Initialization Fix ---
            if not tree and is_blender_5():
                # HP-13: In B5.0, tree type 'COMPOSITING' is replaced by 'CompositorNodeTree'
                try:
                    tree = bpy.data.node_groups.new("BT_Compositor_Tree", 'CompositorNodeTree')
                    scene.compositing_node_group = tree
                except Exception as e:
                    logger.debug(f"B5.0: Failed to create/assign new CompositorNodeTree: {e}")
            # ------------------------------------------
            
            if tree: return tree
        except Exception: pass
            
    # 3. Legacy / Common Fallback
    try:
        if hasattr(scene, "use_nodes"):
            if not scene.use_nodes:
                scene.use_nodes = True
            
            tree = getattr(scene, "node_tree", None)
            # Safe type check: B5.0 alias might return Annotation tree
            if tree and hasattr(tree, "type") and tree.type in {'COMPOSITING', 'CompositorNodeTree'}:
                return tree
            
            if hasattr(scene, "node_tree") and scene.node_tree:
                 return scene.node_tree
    except Exception as e:
        logger.debug(f"Error accessing compositor tree: {e}")

    return None

def set_bake_type(scene, bake_type):
    """
    Set bake type in a version-safe way. 
    Assumes engine is already CYCLES (handled by BakeContextManager).
    
    Args:
        scene: Blender scene
        bake_type: String like 'EMIT', 'COMBINED', 'NORMAL', etc.
    """
    # Dynamic mapping adjust for Normal pass in modern Blender
    target_bake_type = BAKE_MAPPING.get(bake_type, bake_type)
    if bake_type == 'NORMAL' and (is_blender_4() or is_blender_5()):
        target_bake_type = 'NORMALS'

    try:
        # PRIORITY: Cycles-specific bake type property (Exists in 3.6 - 5.0+)
        if hasattr(scene, "cycles") and hasattr(scene.cycles, "bake_type"):
            try:
                scene.cycles.bake_type = bake_type 
                if bake_type not in {'NORMALS', 'DISPLACEMENT', 'VECTOR_DISPLACEMENT'}:
                    return True
            except Exception:
                try: 
                    scene.cycles.bake_type = target_bake_type
                    return True
                except Exception: pass
        
        bake_settings = get_bake_settings(scene)
        if bake_settings is None: return False

        # Attempt to set on BakeSettings struct
        for attr in ["type", "bake_type"]: # Try both
            if hasattr(bake_settings, attr):
                try:
                    setattr(bake_settings, attr, bake_type)
                    return True
                except (TypeError, ValueError):
                    try:
                        setattr(bake_settings, attr, target_bake_type)
                        return True
                    except (TypeError, ValueError):
                        pass
        
        # Last resort fallback for B3.3 and others
        if hasattr(scene.render, "bake_type"):
            try:
                scene.render.bake_type = bake_type
                return True
            except Exception:
                try:
                    scene.render.bake_type = target_bake_type
                    return True
                except Exception: pass
            
        logger.warning(f"Could not conclusively set bake type to {bake_type} on {bake_settings}")
        return False
    except Exception as e:
        logger.warning(f"Could not set bake type to {bake_type}: {e}")
        return False


def get_version_string():
    """Get a human-readable version string."""
    v = bpy.app.version
    return f"{v[0]}.{v[1]}.{v[2]}"
