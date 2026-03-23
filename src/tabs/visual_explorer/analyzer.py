import ast
import os
import collections
import csv
import json

class CodeAnalyzer:
    def __init__(self, root_dir, allowed_extensions=None, mode="code"):
        self.root_dir = root_dir
        self.allowed_extensions = allowed_extensions or ['.py']
        self.mode = mode # "code" or "data"
        self.nodes = {}  # path -> node data
        self.edges = []  # (u, v, type)
        self.file_nodes = {} # relative_path -> node_id
        
    def analyze(self):
        print(f"CodeAnalyzer: Starting {self.mode} analysis of {self.root_dir}...")
        # Phase 1: The Crawl
        self._crawl()
        print(f"CodeAnalyzer: Crawl complete. Found {len(self.nodes)} initial nodes.")
        
        # Phase 2: The Deep Parse
        if self.mode == "code":
            self._deep_parse_code()
        else:
            self._deep_parse_data()
        print(f"CodeAnalyzer: Deep parse complete. Total nodes: {len(self.nodes)}.")
        
        # Phase 3: The Reference Hunt
        if self.mode == "code":
            self._reference_hunt()
            print(f"CodeAnalyzer: Reference hunt complete. Found {len(self.edges)} edges.")
        
        return self.nodes, self.edges

    def _crawl(self):
        for root, dirs, files in os.walk(self.root_dir):
            # Ignore hidden dirs and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            rel_root = os.path.relpath(root, self.root_dir)
            if rel_root == ".":
                node_id = "root"
                name = os.path.basename(self.root_dir)
            else:
                node_id = rel_root
                name = os.path.basename(root)
            
            self.nodes[node_id] = {
                'id': node_id,
                'name': name,
                'type': 'dir',
                'path': root,
                'children': [],
                'parent': os.path.dirname(node_id) if node_id != "root" else None
            }
            if self.nodes[node_id]['parent'] == "":
                self.nodes[node_id]['parent'] = "root"
                
            if node_id != "root":
                parent_id = self.nodes[node_id]['parent']
                if parent_id in self.nodes:
                    if node_id not in self.nodes[parent_id]['children']:
                        self.nodes[parent_id]['children'].append(node_id)
                
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in self.allowed_extensions and file != "__init__.py":
                    rel_file_path = os.path.join(rel_root, file) if rel_root != "." else file
                    file_id = rel_file_path
                    self.nodes[file_id] = {
                        'id': file_id,
                        'name': file,
                        'type': 'file',
                        'path': os.path.join(root, file),
                        'parent': node_id,
                        'children': [], 
                        'classes': {}, # Keep for lookup
                        'functions': {}, # Keep for lookup
                        'imports': [],
                        'content': ""
                    }
                    self.file_nodes[rel_file_path] = file_id
                    if file_id not in self.nodes[node_id]['children']:
                        self.nodes[node_id]['children'].append(file_id)

    def _deep_parse_code(self):
        # Use a list to avoid "dictionary changed size during iteration"
        file_nodes = [node for node in self.nodes.values() if node['type'] == 'file']
        
        for node in file_nodes:
            node_id = node['id']
            if not node['path'].endswith('.py'): continue
            
            try:
                with open(node['path'], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                node['content'] = content
                tree = ast.parse(content)
                
                self._parse_ast(node_id, tree)
            except Exception as e:
                print(f"Error parsing {node['path']}: {e}")

    def _deep_parse_data(self):
        file_nodes = [node for node in self.nodes.values() if node['type'] == 'file']
        for node in file_nodes:
            ext = os.path.splitext(node['path'])[1].lower()
            if ext == '.csv':
                self._parse_csv(node)
            elif ext == '.json':
                self._parse_json(node)

    def _parse_csv(self, file_node):
        try:
            with open(file_node['path'], 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if headers:
                    for h in headers:
                        if not h: continue
                        child_id = f"{file_node['id']}::header::{h}"
                        self.nodes[child_id] = {
                            'id': child_id,
                            'name': h,
                            'type': 'function', # Use function style for headers
                            'parent': file_node['id'],
                            'children': []
                        }
                        file_node['children'].append(child_id)
        except Exception as e:
            print(f"Error parsing CSV {file_node['path']}: {e}")

    def _parse_json(self, file_node):
        try:
            with open(file_node['path'], 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    keys = list(data.keys())
                    for k in keys:
                        child_id = f"{file_node['id']}::key::{k}"
                        self.nodes[child_id] = {
                            'id': child_id,
                            'name': k,
                            'type': 'class', # Use class style for keys? Or function?
                            'parent': file_node['id'],
                            'children': []
                        }
                        file_node['children'].append(child_id)
        except Exception as e:
            print(f"Error parsing JSON {file_node['path']}: {e}")

    def _parse_ast(self, file_id, tree):
        file_node = self.nodes[file_id]
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    file_node['imports'].append({'name': alias.name, 'lineno': node.lineno})
            elif isinstance(node, ast.ImportFrom):
                file_node['imports'].append({'module': node.module, 'names': [a.name for a in node.names], 'lineno': node.lineno})
            elif isinstance(node, ast.ClassDef):
                cls_data = self._process_class(file_id, node, file_node['classes'])
                if cls_data['id'] not in file_node['children']:
                    file_node['children'].append(cls_data['id'])
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_data = self._process_function(file_id, node, file_node['functions'])
                if func_data['id'] not in file_node['children']:
                    file_node['children'].append(func_data['id'])

    def _process_class(self, file_id, class_node, parent_lookup):
        class_id = f"{file_id}::{class_node.name}"
        class_data = {
            'id': class_id,
            'name': class_node.name,
            'type': 'class',
            'children': [], # Methods and nested classes
            'methods': {}, # Keep for lookup
            'bases': [self._get_base_name(base) for base in class_node.bases],
            'lineno': class_node.lineno,
            'parent': file_id
        }
        self.nodes[class_id] = class_data
        parent_lookup[class_node.name] = class_data
        
        for node in ast.iter_child_nodes(class_node):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                func_data = self._process_function(class_id, node, class_data['methods'])
                if func_data['id'] not in class_data['children']:
                    class_data['children'].append(func_data['id'])
            elif isinstance(node, ast.ClassDef):
                nested_cls_data = self._process_class(class_id, node, class_data['methods'])
                if nested_cls_data['id'] not in class_data['children']:
                    class_data['children'].append(nested_cls_data['id'])
        return class_data

    def _process_function(self, parent_id, func_node, parent_lookup):
        func_id = f"{parent_id}.{func_node.name}" if '.' in parent_id or '::' in parent_id else f"{parent_id}::{func_node.name}"
        func_data = {
            'id': func_id,
            'name': func_node.name,
            'type': 'function',
            'children': [], # Maybe inner functions?
            'lineno': func_node.lineno,
            'calls': [],
            'parent': parent_id
        }
        self.nodes[func_id] = func_data
        parent_lookup[func_node.name] = func_data
        
        # Find calls inside function
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node.func)
                if call_name:
                    func_data['calls'].append(call_name)
        return func_data

    def _get_base_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_call_name(node)
        return str(node)

    def _get_call_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_call_name(node.value)}.{node.attr}"
        return None

    def _reference_hunt(self):
        # Resolve Red Lines (Imports)
        for file_id, node in self.nodes.items():
            if node['type'] != 'file': continue
            for imp in node['imports']:
                target_module = imp.get('module') or imp.get('name')
                if not target_module: continue
                
                # Try to find the file
                target_file_id = self._resolve_module_to_file(target_module)
                if target_file_id and target_file_id != file_id:
                    self.edges.append((file_id, target_file_id, 'dependency'))

        # Resolve Blue Lines (Inheritance)
        for file_id, node in self.nodes.items():
            if node['type'] != 'file': continue
            for class_name, class_data in node['classes'].items():
                for base in class_data['bases']:
                    target_class_id = self._resolve_class(file_id, base)
                    if target_class_id:
                        self.edges.append((class_data['id'], target_class_id, 'inheritance'))

        # Resolve Orange Lines (Calls)
        for file_id, node in self.nodes.items():
            if node['type'] != 'file': continue
            # Top level functions
            for func_name, func_data in node['functions'].items():
                self._resolve_calls(file_id, func_data)
            # Class methods
            for class_name, class_data in node['classes'].items():
                for method_name, method_data in class_data['methods'].items():
                    self._resolve_calls(file_id, method_data)

    def _resolve_module_to_file(self, module_name):
        # Simple resolution: check if module_name.py exists in our nodes
        # Also check packages (module_name/__init__.py)
        potential_paths = [
            module_name.replace('.', '/') + ".py",
            module_name.replace('.', '/') + "/__init__.py"
        ]
        for p in potential_paths:
            if p in self.file_nodes:
                return self.file_nodes[p]
        
        # Try relative to current file? (Simplified for now)
        return None

    def _resolve_class(self, current_file_id, class_name):
        # 1. Look in same file
        if class_name in self.nodes[current_file_id]['classes']:
            return self.nodes[current_file_id]['classes'][class_name]['id']
        
        # 2. Look in imports
        for imp in self.nodes[current_file_id]['imports']:
            if 'names' in imp: # ImportFrom
                if class_name in imp['names']:
                    target_file_id = self._resolve_module_to_file(imp['module'])
                    if target_file_id and class_name in self.nodes[target_file_id]['classes']:
                        return self.nodes[target_file_id]['classes'][class_name]['id']
            elif 'name' in imp: # Import
                if class_name.startswith(imp['name'] + "."):
                    sub_name = class_name[len(imp['name'])+1:]
                    target_file_id = self._resolve_module_to_file(imp['name'])
                    if target_file_id and sub_name in self.nodes[target_file_id]['classes']:
                        return self.nodes[target_file_id]['classes'][sub_name]['id']
        return None

    def _resolve_calls(self, current_file_id, func_data):
        for call in func_data['calls']:
            # This is very rough approximation
            # Check local functions
            if call in self.nodes[current_file_id]['functions']:
                self.edges.append((func_data['id'], self.nodes[current_file_id]['functions'][call]['id'], 'reference'))
                continue
            
            # Check classes (instantiation)
            class_id = self._resolve_class(current_file_id, call)
            if class_id:
                self.edges.append((func_data['id'], class_id, 'reference'))
                continue
            
            # Check imported functions
            for imp in self.nodes[current_file_id]['imports']:
                if 'names' in imp and call in imp['names']:
                    target_file_id = self._resolve_module_to_file(imp['module'])
                    if target_file_id and call in self.nodes[target_file_id]['functions']:
                        self.edges.append((func_data['id'], self.nodes[target_file_id]['functions'][call]['id'], 'reference'))
