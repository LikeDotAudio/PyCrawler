import os
import re
from tkinter import filedialog, messagebox

class VisualExplorerDataMixin:
    def reload_map(self):
        map_path = None
        if hasattr(self.root_app, 'output_dir') and self.root_app.output_dir:
            potential_path = os.path.join(self.root_app.output_dir, "MAP.txt")
            if os.path.exists(potential_path):
                map_path = potential_path
        
        if not map_path:
            map_path = filedialog.askopenfilename(title="Select MAP.txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
            
        if map_path:
            self.load_data(map_path)
        else:
             self.status_label.config(text="No Map Loaded")

    def load_data(self, map_path):
        self.nodes = {}
        self.edges = []
        self.file_nodes = {}
        self.folder_colors = {} 
        self.status_label.config(text=f"Loading {os.path.basename(map_path)}...")
        self.update_idletasks()
        
        self.current_map_dir = os.path.dirname(map_path)
        
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self._parse_map_lines(lines)
            # self._calculate_layout_sugiyama()
            self._calculate_layout_universe()
            self.draw()
            self.status_label.config(text=f"Loaded {len(self.nodes)} nodes")
        except Exception as e:
            self.status_label.config(text=f"Error loading map: {e}")
            print(f"Error: {e}")

    def _get_folder_color(self, full_path):
        parts = full_path.split(os.sep)
        if len(parts) > 1:
            key = parts[1] if len(parts) > 1 else "root"
            if key not in self.folder_colors:
                idx = len(self.folder_colors) % len(self.folder_palettes)
                self.folder_colors[key] = self.folder_palettes[idx]
            return self.folder_colors[key]
        return "#888888"

    def _parse_map_lines(self, lines):
        stack = []
        
        for line in lines:
            line = line.rstrip()
            if not line.startswith("#"): continue
            
            content = line[1:]
            
            # Improved Indentation detection including tree characters
            # Matches spaces, |, ├, └, ─ at the start of the line
            match = re.match(r'^([\s|├└─]+)(.*)', content)
            
            if match:
                prefix = match.group(1)
                raw_text = match.group(2)
                # Calculate level: 4 characters per level is standard for 'tree'
                # But we might have a leading space from the '# ' parsing.
                # If prefix is " ", len 1 -> level 0.
                # If prefix is " ├── ", len 5 -> level 1.
                # If prefix is " |   ├── ", len 9 -> level 2.
                level = len(prefix) // 4
            else:
                # No prefix (e.g. "#Root")
                raw_text = content
                level = 0
            
            clean_text = raw_text.strip()
            if not clean_text: continue
            
            item_type = "unknown"
            name = clean_text
            
            # Sub-content (Functions/Classes)
            meta_match = re.match(r'-> (Function|Class|Import|Key): (.*)', clean_text)
            if meta_match:
                meta_type = meta_match.group(1).lower()
                meta_name = meta_match.group(2)
                
                # Attach to nearest file
                parent_file = None
                for i in range(len(stack)-1, -1, -1):
                    if stack[i][2] == 'file':
                        parent_file = stack[i]
                        break
                
                if parent_file:
                    file_id = parent_file[3]
                    if file_id in self.nodes:
                        if meta_type == 'import':
                            self.nodes[file_id]['imports'].append(meta_name)
                        else:
                            self.nodes[file_id]['contents'].append({'type': meta_type, 'name': meta_name})
                continue
            
            # File or Directory
            if clean_text.endswith("/"):
                item_type = "dir"
                name = clean_text.rstrip("/")
            elif "(Lines:" in clean_text:
                item_type = "file"
                name = clean_text.split(" (Lines:")[0]
            else:
                if level == 0:
                    item_type = "root"
                    name = clean_text.rstrip("/")
                else:
                    item_type = "file" # assumption fallback

            while len(stack) > level:
                stack.pop()
            
            # Construct Full Path (Logical)
            if item_type == "root":
                full_path = name
            else:
                parent_path = stack[-1][3] if stack else ""
                if parent_path:
                    full_path = os.path.join(parent_path, name)
                else:
                    full_path = name
            
            stack.append((level, name, item_type, full_path))
            
            # Create Nodes for BOTH Files and Directories to build the "Universe" structure
            if item_type in ['file', 'dir', 'root']:
                node_id = full_path
                node_color = self._get_folder_color(full_path)
                
                # Directory node style
                if item_type in ['dir', 'root']:
                    self.nodes[node_id] = {
                        'id': node_id,
                        'name': name,
                        'type': 'dir',
                        'contents': [], 
                        'imports': [],
                        'x': 0, 'y': 0,
                        'w': 250, 'h': 60, # Wider, flatter for headers
                        'color': node_color,
                        'rank': 0, 
                        'order': 0,
                        'pagerank': 1.0
                    }
                else:
                    self.nodes[node_id] = {
                        'id': node_id,
                        'name': name,
                        'type': 'file',
                        'contents': [], 
                        'imports': [],
                        'x': 0, 'y': 0,
                        'w': 200, 'h': 120,
                        'color': node_color,
                        'rank': 0, 
                        'order': 0,
                        'pagerank': 1.0
                    }
                    self.file_nodes[full_path] = node_id # Keep track of files for imports
            
            # Hierarchy Edges: Connect Parent Directory -> Current Item
            if len(stack) > 1:
                parent_id = stack[-2][3] # Parent full path
                current_id = stack[-1][3]
                self.edges.append((parent_id, current_id, 'hierarchy'))

        # Dependency Edges (Imports)
        for node_id, node in self.nodes.items():
            if node['type'] == 'file':
                for imp in node['imports']:
                    for target_path in self.file_nodes:
                        if os.path.basename(target_path) == imp or os.path.basename(target_path).replace(".py", "") == imp:
                            self.edges.append((node_id, target_path, 'dependency'))

    def _build_hierarchy_tree(self):
        tree = {nid: {'files': [], 'dirs': []} for nid in self.nodes}
        roots = []
        
        # Find Root (nodes with no parent in hierarchy edges)
        child_ids = set()
        for u, v, etype in self.edges:
            if etype == 'hierarchy':
                child_ids.add(v)
                # Determine type of v
                if self.nodes[v]['type'] == 'file':
                    tree[u]['files'].append(v)
                else:
                    tree[u]['dirs'].append(v)
        
        # Roots are those not in child_ids
        for nid in self.nodes:
            if nid not in child_ids:
                roots.append(nid)
        
        return tree, roots
