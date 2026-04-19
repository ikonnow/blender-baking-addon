#!/usr/bin/env python3
import ast
import os
import json
from pathlib import Path
from typing import Set

class DeepUIExtractor(ast.NodeVisitor):
    def __init__(self):
        self.strings: Set[str] = set()

    def add(self, s: str) -> None:
        if isinstance(s, str) and len(s.strip()) > 1:
            # 排除明显的逻辑标识符和内部路径
            if s.startswith(("ShaderNode", "CompositorNode", "BT_")): return
            if s.endswith((".py", ".json", ".blend")): return
            if all(c.isupper() or c == '_' for c in s) and len(s) > 4: return # 排除内部常量名
            self.strings.add(s)

    def visit_ClassDef(self, node: ast.ClassDef):
        # 提取类级别的 bl_label, bl_description
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id in ['bl_label', 'bl_description']:
                        if isinstance(item.value, ast.Constant): self.add(item.value.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # 1. 属性定义: prop(name="...", description="...")
        attr_name = getattr(node.func, "attr", "")
        if attr_name.endswith("Property"):
            for kw in node.keywords:
                if kw.arg in ['name', 'description']:
                    if isinstance(kw.value, ast.Constant): self.add(kw.value.value)
                # 特别处理 EnumProperty 的 items
                if kw.arg == 'items' and isinstance(kw.value, ast.List):
                    for elt in kw.value.elts:
                        if isinstance(elt, ast.Tuple):
                            for sub_elt in elt.elts:
                                if isinstance(sub_elt, ast.Constant): self.add(sub_elt.value)

        # 2. UI 布局: label(text="..."), operator(text="...")
        if attr_name in ['label', 'prop', 'operator', 'pgettext', 'report']:
            for kw in node.keywords:
                if kw.arg in ['text', 'name']:
                    if isinstance(kw.value, ast.Constant): self.add(kw.value.value)
            # 处理位置参数 (针对 pgettext 或 report)
            for arg in node.args:
                if isinstance(arg, ast.Constant): self.add(arg.value)
        
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # 捕获 UI_MESSAGES 字典中的内容
        if any(isinstance(t, ast.Name) and "MESSAGE" in t.id for t in node.targets):
            if isinstance(node.value, ast.Dict):
                for v in node.value.values:
                    if isinstance(v, ast.Constant): self.add(v.value)
        self.generic_visit(node)

def extract(source_dir: Path, output_path: Path):
    all_strings = set()
    for py_file in source_dir.rglob("*.py"):
        if any(p in str(py_file) for p in ['test_cases', 'automation', 'dev_tools']): continue
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            extractor = DeepUIExtractor()
            extractor.visit(tree)
            all_strings.update(extractor.strings)
        except Exception: continue

    output_data = {"data": {}}
    for s in sorted(all_strings):
        output_data["data"][s] = {"en_US": s}
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    print(f"Extracted {len(all_strings)} comprehensive UI strings to {output_path}")

if __name__ == "__main__":
    extract(Path("."), Path("translations_deep.json"))
