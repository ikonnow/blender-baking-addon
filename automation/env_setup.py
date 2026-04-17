import sys
import os
from pathlib import Path
import bpy


def setup_environment():
    """统一的插件测试环境初始化"""
    current_dir = Path(__file__).resolve().parent
    addon_root = current_dir.parent
    addon_name = "baketool"

    parent_dir = str(addon_root.parent)

    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    script_dir = str(addon_root)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    for mod in list(sys.modules.keys()):
        if mod == addon_name or mod.startswith(f"{addon_name}."):
            del sys.modules[mod]

    print(f"\n>>> Environment Setup: Blender {bpy.app.version_string}")
    print(f">>> Addon Root: {addon_root}")
    print(f">>> Python Path: {sys.path[:3]}")

    return addon_name, addon_root
