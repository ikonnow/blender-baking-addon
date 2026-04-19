import ast
import json
from pathlib import Path
import re
import sys
import argparse

# ================= 配置�?=================
# 默认输出文件
DEFAULT_JSON = "translations.json"
# 目标语言
TARGET_LANGS = ["zh_CN", "fr_FR", "ru_RU", "ja_JP"]
# 忽略目录
IGNORE_DIRS = {'__pycache__', '.git', '.vscode', '.venv', 'doc', 'build', 'dist'}
# 忽略文件
IGNORE_FILES = {'extract_translations.py', 'translations.py', 'setup.py'}
# ==========================================

class SmartFilter:
    """过滤器：决定哪些字符串值得翻译"""
    
    # 纯数�?符号正则 (匹配: "123", "+", "->", "10.5")
    re_numeric_or_symbol = re.compile(r'^[\d\s\W]+$')
    # 看起来像内部ID正则 (匹配: "OBJECT_OT_op", "MY_PROP")，允许下划线，全大写
    re_internal_id = re.compile(r'^[A-Z][A-Z0-9_]+$')

    @staticmethod
    def is_translatable(s):
        if not s or not isinstance(s, str):
            return False
        
        s = s.strip()
        if not s: 
            return False

        # 1. 忽略纯数字和符号 (�?"1024", "+", "---")
        if SmartFilter.re_numeric_or_symbol.match(s):
            return False

        # 2. 忽略单个 ASCII 字符 (�?"X", "Y", "Z", "i")
        # 但保留单个中文字符（如果源码里有的话�?        if len(s) == 1 and s.isascii():
            return False

        # 3. 忽略内部 ID (�?"BAKETOOL_OT_bake")
        # 规则：全大写，包含下划线，且没有空格
        if "_" in s and " " not in s and SmartFilter.re_internal_id.match(s):
            # 例外：保留短的常用词，如 "ERROR", "WARNING" 即使全大写也可能是UI标题
            if len(s) > 12: 
                return False

        # 4. 忽略文件扩展�?(�?"*.png", ".json")
        if s.startswith("*.") or (s.startswith(".") and len(s) < 6):
            return False

        return True

class UniversalExtractor(ast.NodeVisitor):
    def __init__(self):
        self.found_strings = set()

    def add(self, s):
        if SmartFilter.is_translatable(s):
            self.found_strings.add(s.strip())

    def visit_Call(self, node):
        """扫描函数调用: layout.label(text='...'), pgettext('...')"""
        # 关注的关键字参数
        target_keywords = {'text', 'name', 'description', 'message', 'title', 'default'}
        
        for keyword in node.keywords:
            if keyword.arg in target_keywords:
                val = self._get_str(keyword.value)
                # 特殊逻辑：default 值如果是全大写ID，通常忽略
                if keyword.arg == 'default' and val and val.isupper() and ' ' not in val:
                    continue
                self.add(val)
            
            # EnumProperty(items=[...])
            if keyword.arg == 'items' and isinstance(keyword.value, ast.List):
                self._extract_enum(keyword.value)

        # 显式翻译函数: pgettext("...")
        self._check_translation_func(node)
        self.generic_visit(node)

    def visit_Assign(self, node):
        """扫描赋�? bl_label = '...', items = [...]"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                # 类属�?                if target.id in {'bl_label', 'bl_description', 'bl_category', 'bl_warning', 'bl_info'}:
                    self.add(self._get_str(node.value))
                
                # UI_MESSAGES 字典�?                if target.id == 'UI_MESSAGES' and isinstance(node.value, ast.Dict):
                    for val_node in node.value.values:
                        self.add(self._get_str(val_node))

                # 枚举列表 (启发�?
                is_list_var = "item" in target.id.lower() or "list" in target.id.lower() or target.id.isupper()
                if is_list_var and isinstance(node.value, ast.List):
                    self._extract_enum(node.value)
        self.generic_visit(node)

    def _extract_enum(self, list_node):
        """解析 Blender Enum items: (ID, Name, Description, ...)"""
        for el in list_node.elts:
            if isinstance(el, ast.Tuple) and len(el.elts) >= 3:
                # Index 1: Name, Index 2: Description
                if len(el.elts) > 1: self.add(self._get_str(el.elts[1]))
                if len(el.elts) > 2: self.add(self._get_str(el.elts[2]))

    def _check_translation_func(self, node):
        """检�?pgettext 等函�?""
        func_name = ""
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        
        if func_name in {'pgettext', 'pgettext_iface', 'pgettext_tip', '_', 'iface_'}:
            if node.args:
                self.add(self._get_str(node.args[0]))

    def _get_str(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            l, r = self._get_str(node.left), self._get_str(node.right)
            if l and r: return l + r
        return None

def get_files(root):
    res = []
    root_path = Path(root)
    for p in root_path.rglob("*.py"):
        if p.name in IGNORE_FILES:
            continue
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        res.append(str(p))
    return res

def sync_json(found_keys, json_path, mode='update'):
    """
    核心同步逻辑
    mode:
      - update: 保留旧Key，添加新Key (默认安全)
      - sync:   删除旧Key，添加新Key (保持清洁)
      - clean:  删除旧Key，添加新Key，且清空所有翻译�?(重置)
    """
    data = {"header": {"system": "Extracted by Universal Tool"}, "data": {}}
    
    json_file = Path(json_path)
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"[!] Error reading JSON: {e}")
            
    if "data" not in data: data["data"] = {}
    
    current_data = data["data"]
    existing_keys = set(current_data.keys())
    
    # 统计
    added = 0
    removed = 0
    
    # 1. 决定最终的 Key 集合
    final_keys = set()
    
    if mode == 'update':
        final_keys = existing_keys | found_keys
    else: # sync or clean
        final_keys = found_keys
        removed = len(existing_keys - found_keys)
    
    # 2. 构建新数�?    new_data = {}
    for key in sorted(final_keys):
        # 如果 Key 存在�?mode 不是 clean，保留旧�?        if key in current_data and mode != 'clean':
            new_data[key] = current_data[key]
            # 检查是否有新增的语言列需要补�?            for lang in TARGET_LANGS:
                if lang not in new_data[key]:
                    new_data[key][lang] = key
        else:
            # 新增 Key
            new_data[key] = {}
            for lang in TARGET_LANGS:
                new_data[key][lang] = key # 默认填充原文
            
            if key not in existing_keys:
                added += 1
                
    data["data"] = new_data
    
    # 写入
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    return added, removed, len(final_keys)

def main():
    parser = argparse.ArgumentParser(description="Blender Addon Translation Extractor")
    parser.add_argument("--mode", choices=['update', 'sync', 'clean'], default='update', 
                        help="update: Add new keys only. sync: Remove obsolete keys. clean: Wipe all values.")
    parser.add_argument("--path", default=".", help="Root directory to scan")
    args = parser.parse_args()

    root_dir = Path(args.path).resolve()
    json_path = root_dir / DEFAULT_JSON
    
    print(f"--- Universal Translation Extractor ---")
    print(f"Root: {root_dir}")
    print(f"Mode: {args.mode.upper()}")
    
    files = get_files(root_dir)
    print(f"Scanning {len(files)} files...")
    
    extractor = UniversalExtractor()
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                extractor.visit(ast.parse(fp.read()))
        except Exception as e:
            print(f"[!] Failed to parse {Path(f).name}: {e}")
            
    added, removed, total = sync_json(extractor.found_strings, json_path, args.mode)
    
    print(f"Done. Total Keys: {total}")
    print(f"Stats: +{added} added, -{removed} removed.")
    print(f"Saved to: {DEFAULT_JSON}")

if __name__ == "__main__":
    main()
