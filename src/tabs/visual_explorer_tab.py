import tkinter as tk
from tkinter import ttk, Canvas, filedialog, messagebox, Toplevel
import os
import math
import random
import re
import json
import subprocess
import platform

class SyntaxViewer(Toplevel):
    def __init__(self, parent, title, content, file_ext):
        super().__init__(parent)
        self.title(f"Code View: {title}")
        self.geometry("800x600")
        self.configure(bg="#1e1e1e")
        
        self.text_area = tk.Text(self, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 11), 
                                 insertbackground="white", selectbackground="#264f78")
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_area.insert("1.0", content)
        
        self._highlight_syntax(file_ext)
        self.text_area.config(state="disabled") # Read-only

    def _highlight_syntax(self, ext):
        # Basic regex-based highlighting for common keywords
        keywords = {
            ".py": r'\b(def|class|import|from|return|if|else|elif|for|while|try|except|with|as|pass|None|True|False)\b',
            ".js": r'\b(function|const|let|var|if|else|for|while|return|import|export|default|class|this|new)\b',
            ".json": r'\b(true|false|null)\b'
        }
        
        comment_patterns = {
            ".py": r'(#.*)',
            ".js": r'(//.*)',
            ".json": r'' 
        }
        
        string_pattern = r'(".*?"|".*?")'
        
        # Configure tags
        self.text_area.tag_configure("keyword", foreground="#569cd6") # Blue
        self.text_area.tag_configure("string", foreground="#ce9178")  # Orange/Red
        self.text_area.tag_configure("comment", foreground="#6a9955") # Green
        self.text_area.tag_configure("number", foreground="#b5cea8")  # Light Green
        
        content = self.text_area.get("1.0", "end")
        
        # Highlight Strings
        for match in re.finditer(string_pattern, content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("string", start, end)

        # Highlight Keywords
        kw_regex = keywords.get(ext, "")
        if kw_regex:
             for match in re.finditer(kw_regex, content):
                start = f"1.0 + {match.start()} chars"
                end = f"1.0 + {match.end()} chars"
                self.text_area.tag_add("keyword", start, end)
        
        # Highlight Comments
        cmt_regex = comment_patterns.get(ext, "")
        if cmt_regex:
            for match in re.finditer(cmt_regex, content):
                start = f"1.0 + {match.start()} chars"
                end = f"1.0 + {match.end()} chars"
                self.text_area.tag_add("comment", start, end)

class VisualExplorerTab(ttk.Frame):
    def __init__(self, notebook, root_app):
        super().__init__(notebook)
        self.notebook = notebook
        self.root_app = root_app 
        
        self.nodes = {} # id -> NodeData
        self.edges = [] # list of (from_id, to_id, type)
        self.file_nodes = {} # file_path -> node_id
        
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.pan_data = {"x": 0, "y": 0}
        
        # Defined Palettes for Hierarchy
        self.folder_palettes = [
            "#FF5733", "#33FF57", "#3357FF", "#FF33F6", "#33FFF6", 
            "#F6FF33", "#FF8C33", "#8C33FF", "#FF338C", "#33FF8C",
            "#D4AC0D", "#1ABC9C", "#9B59B6", "#E74C3C", "#2ECC71"
        ]
        self.folder_colors = {} # folder_path -> color

        self._setup_ui()
        self._setup_context_menu()

    def _setup_ui(self):
        # Controls
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(fill="x", side="top", padx=5, pady=5)
        
        ttk.Button(ctrl_frame, text="Load Map", command=self.reload_map).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Reset View", command=self.reset_view).pack(side="left", padx=5)
        
        # New Export/Import Buttons
        ttk.Separator(ctrl_frame, orient="vertical").pack(side="left", padx=10, fill="y")
        ttk.Button(ctrl_frame, text="Save Layout", command=self.save_layout).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Load Layout", command=self.load_layout).pack(side="left", padx=5)

        self.status_label = ttk.Label(ctrl_frame, text="Ready", foreground="gray")
        self.status_label.pack(side="right", padx=5)

        # Canvas
        self.canvas = Canvas(self, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        
        self.canvas.bind("<MouseWheel>", self.on_zoom) # Windows/MacOS
        self.canvas.bind("<Button-4>", self.on_zoom) # Linux Up
        self.canvas.bind("<Button-5>", self.on_zoom) # Linux Down
        
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.show_context_menu) # Right Click

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="View Code", command=self.view_node_code)
        self.context_menu.add_command(label="Open in Editor", command=self.open_node_in_editor)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Highlight Dependencies", command=lambda: self.highlight_node(self.current_context_node))

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
            indent_match = re.match(r'(\s*)(.*)', content)
            if not indent_match: continue
            
            indent_str = indent_match.group(1)
            raw_text = indent_match.group(2)
            level = len(indent_str) // 4
            
            clean_text = raw_text.replace("└── ", "").replace("├── ", "").replace("|   ", "").strip()
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

    # --- Universe Layout Algorithm ---

    def _calculate_layout_universe(self):
        """
        Layout that treats folders as 'Universes' (containers).
        Files are stacked inside. Sub-folders are zones treeing off.
        """
        if not self.nodes: return
        
        # 1. Build Tree Structure
        tree, root_id = self._build_hierarchy_tree()
        if not root_id: return
        
        # 2. Measure Sizes (Bottom-Up)
        self._measure_universe(root_id, tree)
        
        # 3. Position Nodes (Top-Down)
        self._position_universe(root_id, tree, 0, 0)
        
    def _build_hierarchy_tree(self):
        tree = {nid: {'files': [], 'dirs': []} for nid in self.nodes}
        root_id = None
        
        # Find Root (first node with no parent in hierarchy edges, or just depth 0)
        # Actually, _parse_map_lines usually puts root first.
        # Let's rely on hierarchy edges.
        child_ids = set()
        for u, v, etype in self.edges:
            if etype == 'hierarchy':
                child_ids.add(v)
                # Determine type of v
                if self.nodes[v]['type'] == 'file':
                    tree[u]['files'].append(v)
                else:
                    tree[u]['dirs'].append(v)
        
        # Root is the one not in child_ids
        for nid in self.nodes:
            if nid not in child_ids:
                root_id = nid
                break
        
        return tree, root_id

    def _measure_universe(self, node_id, tree):
        node = self.nodes[node_id]
        padding = 20
        header_height = 40
        
        if node['type'] == 'file':
            # Files have fixed or content-based size
            # Currently using fixed for consistency, or calculation from Sugiyama
            # Let's use a standard file size
            node['w'] = 220
            # Height depends on content (functions/classes)
            content_count = len(node['contents'])
            node['h'] = 60 + (content_count * 18)
            return
            
        # It's a directory
        children_files = tree[node_id]['files']
        children_dirs = tree[node_id]['dirs']
        
        # Measure Children
        max_file_w = 0
        total_files_h = 0
        
        for fid in children_files:
            self._measure_universe(fid, tree)
            if self.nodes[fid]['w'] > max_file_w: max_file_w = self.nodes[fid]['w']
            total_files_h += self.nodes[fid]['h'] + padding
            
        # Measure Subdirs
        total_subdirs_w = 0
        max_subdir_h = 0
        
        for did in children_dirs:
            self._measure_universe(did, tree)
            total_subdirs_w += self.nodes[did]['w'] + padding
            if self.nodes[did]['h'] > max_subdir_h: max_subdir_h = self.nodes[did]['h']
            
        # Calculate Universe Dimensions
        # Layout: Files in a column on Left. Subdirs in a row on Right (or below if no files).
        
        # Width
        content_w = 0
        if children_files and children_dirs:
            content_w = max_file_w + padding + total_subdirs_w
        elif children_files:
            content_w = max_file_w
        elif children_dirs:
            content_w = total_subdirs_w
        else:
            content_w = 200 # Empty folder
            
        node['w'] = content_w + (padding * 2)
        
        # Height
        # Files column height
        col_h = total_files_h
        # Subdirs row height
        row_h = max_subdir_h
        
        content_h = max(col_h, row_h)
        if content_h == 0: content_h = 100
        
        node['h'] = header_height + content_h + (padding * 2)

    def _position_universe(self, node_id, tree, x, y):
        node = self.nodes[node_id]
        padding = 20
        header_height = 40
        
        node['x'] = x
        node['y'] = y
        
        if node['type'] == 'file':
            return
            
        # Position Children
        start_x = x + padding
        start_y = y + header_height + padding
        
        children_files = tree[node_id]['files']
        children_dirs = tree[node_id]['dirs']
        
        # 1. Stack Files
        current_y = start_y
        max_file_w = 0
        for fid in children_files:
            fnode = self.nodes[fid]
            self._position_universe(fid, tree, start_x, current_y)
            current_y += fnode['h'] + padding
            if fnode['w'] > max_file_w: max_file_w = fnode['w']
            
        # 2. Tree off Subdirs (to the right of files)
        subdir_start_x = start_x
        if children_files:
            subdir_start_x += max_file_w + padding
            
        # For subdirs, we arrange them in a row for now
        current_x = subdir_start_x
        for did in children_dirs:
            dnode = self.nodes[did]
            self._position_universe(did, tree, current_x, start_y)
            current_x += dnode['w'] + padding

    # --- Sugiyama & PageRank Algorithms ---

    def _calculate_layout_sugiyama(self):
        if not self.nodes: return
        
        self._compute_pagerank()
        
        adj = {u: [] for u in self.nodes}
        for u, v, etype in self.edges:
             # Treat 'hierarchy' edges as structural backbone (stronger)
             if u in adj: adj[u].append(v)
        
        safe_edges = self._remove_cycles(adj)
        layers = self._assign_layers(safe_edges)
        ordered_layers = self._minimize_crossings(layers, safe_edges)
        
        # Spacing
        layer_height = 300 
        node_spacing_x = 280 
        start_y = 200
        start_x = 200
        
        max_layer_width = 0
        for layer in ordered_layers.values():
            if len(layer) > max_layer_width: max_layer_width = len(layer)
            
        canvas_center_x = (max_layer_width * node_spacing_x) / 2 + start_x
        
        for rank, nodes_in_layer in ordered_layers.items():
            y = start_y + (rank * layer_height)
            
            layer_width = len(nodes_in_layer) * node_spacing_x
            x_offset = canvas_center_x - (layer_width / 2)
            
            for i, node_id in enumerate(nodes_in_layer):
                node = self.nodes[node_id]
                node['rank'] = rank
                node['order'] = i
                
                # Apply PageRank to Size (Only for files)
                if node['type'] == 'file':
                    pr_scale = 1 + (node['pagerank'] * 12) 
                    if pr_scale > 4: pr_scale = 4
                    node['w'] = 200 * math.sqrt(pr_scale)
                    node['h'] = (80 + (len(node['contents']) * 15)) * math.sqrt(pr_scale)
                
                node['x'] = x_offset + (i * node_spacing_x)
                node['y'] = y

    def _compute_pagerank(self, damping=0.85, iterations=20):
        in_links = {u: [] for u in self.nodes}
        out_degree = {u: 0 for u in self.nodes}
        
        for u, v, _ in self.edges:
            if v in in_links: in_links[v].append(u)
            if u in out_degree: out_degree[u] += 1
            
        N = len(self.nodes)
        pagerank = {u: 1.0 / N for u in self.nodes}
        
        for _ in range(iterations):
            new_pagerank = {}
            for u in self.nodes:
                rank_sum = 0
                for incoming in in_links[u]:
                    if out_degree[incoming] > 0:
                        rank_sum += pagerank[incoming] / out_degree[incoming]
                
                new_pagerank[u] = (1 - damping) / N + damping * rank_sum
            pagerank = new_pagerank
            
        max_pr = max(pagerank.values()) if pagerank else 1
        for u, val in pagerank.items():
            self.nodes[u]['pagerank'] = val / max_pr

    def _remove_cycles(self, adj):
        visited = set()
        recursion_stack = set()
        safe_edges = []
        
        def dfs(u):
            visited.add(u)
            recursion_stack.add(u)
            
            if u in adj:
                for v in adj[u]:
                    if v not in visited:
                        safe_edges.append((u, v))
                        dfs(v)
                    elif v in recursion_stack:
                        pass 
                    else:
                        safe_edges.append((u, v))
            
            recursion_stack.remove(u)

        for node in self.nodes:
            if node not in visited:
                dfs(node)
                
        return safe_edges

    def _assign_layers(self, safe_edges):
        in_degree = {u: 0 for u in self.nodes}
        for u, v in safe_edges:
            in_degree[v] += 1
            
        queue = [u for u in self.nodes if in_degree[u] == 0]
        rank = {u: 0 for u in self.nodes}
        
        processed_count = 0
        while queue:
            u = queue.pop(0)
            processed_count += 1
            
            neighbors = [v for src, v in safe_edges if src == u]
            
            for v in neighbors:
                rank[v] = max(rank[v], rank[u] + 1)
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        layers = {}
        for u, r in rank.items():
            if r not in layers: layers[r] = []
            layers[r].append(u)
            
        return layers

    def _minimize_crossings(self, layers, safe_edges):
        max_rank = max(layers.keys()) if layers else 0
        
        down_adj = {u: [] for u in self.nodes} 
        up_adj = {v: [] for v in self.nodes}
        for u, v in safe_edges:
            down_adj[u].append(v)
            up_adj[v].append(u)
            
        for _ in range(4):
            for r in range(1, max_rank + 1):
                if r not in layers: continue
                current_nodes = layers[r]
                
                def barycenter(n):
                    parents = up_adj[n]
                    if not parents: return 0
                    parent_indices = []
                    prev_layer = layers.get(r-1, [])
                    for p in parents:
                        if p in prev_layer:
                            parent_indices.append(prev_layer.index(p))
                    if not parent_indices: return 0
                    return sum(parent_indices) / len(parent_indices)
                
                current_nodes.sort(key=barycenter)
                layers[r] = current_nodes
                
            for r in range(max_rank - 1, -1, -1):
                if r not in layers: continue
                current_nodes = layers[r]
                
                def barycenter_down(n):
                    children = down_adj[n]
                    if not children: return 0
                    child_indices = []
                    next_layer = layers.get(r+1, [])
                    for c in children:
                        if c in next_layer:
                            child_indices.append(next_layer.index(c))
                    if not child_indices: return 0
                    return sum(child_indices) / len(child_indices)
                
                current_nodes.sort(key=barycenter_down)
                layers[r] = current_nodes
                
        return layers

    def draw(self):
        self.canvas.delete("all")
        
        for u, v, etype in self.edges:
            if u not in self.nodes or v not in self.nodes: continue
            
            n1 = self.nodes[u]
            n2 = self.nodes[v]
            
            x1 = self.tx(n1['x'] + n1['w']/2)
            y1 = self.ty(n1['y'] + n1['h']) 
            x2 = self.tx(n2['x'] + n2['w']/2)
            y2 = self.ty(n2['y']) 
            
            edge_tag = f"edge_{u}_{v}"
            mid_y = (y1 + y2) / 2
            points = [x1, y1, x1, mid_y, x2, mid_y, x2, y2]
            
            # Styling based on type
            if etype == 'hierarchy':
                self.canvas.create_line(points, fill="#444", width=2, arrow=tk.LAST, tags=("edge", edge_tag))
            else:
                self.canvas.create_line(points, fill="#777", width=1, dash=(4, 2), arrow=tk.LAST, tags=("edge", edge_tag))

        for nid, node in self.nodes.items():
            x = self.tx(node['x'])
            y = self.ty(node['y'])
            w = node['w'] * self.scale
            h = node['h'] * self.scale
            
            # Shadow
            self.canvas.create_rectangle(x+5, y+5, x+w+5, y+h+5, fill="#111", outline="", tags=("node", nid, "node_shadow"))
            
            # Main Box
            if node['type'] == 'dir':
                # Directory Style (Flatter, Header-like)
                rect = self.canvas.create_rectangle(x, y, x+w, y+h, fill="#222", outline=node['color'], width=3, tags=("node", nid, "node_box", f"box_{nid}"))
                self.canvas.create_text(x+w/2, y+h/2, text=node['name'].upper(), fill=node['color'], font=("Arial", int(16*self.scale), "bold"), tags=("node", nid, "node_text", f"text_{nid}"))
            else:
                # File Style
                rect = self.canvas.create_rectangle(x, y, x+w, y+h, fill="#2d2d2d", outline=node['color'], width=2, tags=("node", nid, "node_box", f"box_{nid}"))
                
                title = node['name']
                font_size = int(14 * self.scale) 
                header_height = 40 * self.scale
                
                display_title = title
                if len(title) > 20:
                    mid = len(title) // 2
                    display_title = title[:mid] + "-\n" + title[mid:]
                    header_height = 55 * self.scale 
                
                self.canvas.create_text(x+10, y+(header_height/2), text=display_title, fill="white", font=("Arial", font_size, "bold"), anchor="w", tags=("node", nid, "node_text", f"text_{nid}"))
                self.canvas.create_line(x, y+header_height, x+w, y+header_height, fill=node['color'], tags=("node", nid, "node_line", f"line_{nid}"))
                
                cy = y + header_height + (10 * self.scale)
                limit = 6
                if node['pagerank'] > 0.5: limit = 10
                
                count = 0
                for item in node['contents']:
                    if count >= limit: break
                    itype = item['type']
                    iname = item['name']
                    if len(iname) > 30: iname = iname[:27] + "..."
                    
                    icon = "ƒ" if itype == 'function' else "C" if itype == 'class' else "K"
                    color = "#4ec9b0" if itype == 'class' else "#dcdcaa" if itype == 'function' else "#9cdcfe"
                    
                    self.canvas.create_text(x+15, cy, text=f"{icon} {iname}", fill=color, font=("Consolas", int(10*self.scale)), anchor="w", tags=("node", nid, "node_text", f"text_{nid}"))
                    cy += 18 * self.scale
                    if cy > y + h - 10: break
                    count += 1
                    
                if len(node['contents']) > limit:
                     self.canvas.create_text(x+15, cy, text=f"... (+{len(node['contents']) - limit})", fill="#888", font=("Consolas", int(10*self.scale), "italic"), anchor="w", tags=("node", nid, "node_text", f"text_{nid}"))

    # --- Interaction ---
    
    def tx(self, x): return (x * self.scale) + self.offset_x
    def ty(self, y): return (y * self.scale) + self.offset_y
    def rx(self, x): return (x - self.offset_x) / self.scale
    def ry(self, y): return (y - self.offset_y) / self.scale

    def on_click(self, event):
        self.canvas.scan_mark(event.x, event.y)
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        node_id = None
        for t in tags:
            if t in self.nodes:
                node_id = t
                break
        
        if node_id:
            self.drag_data['item'] = node_id
            self.highlight_node(node_id)
        else:
            self.drag_data['item'] = None
            self.reset_highlight()

    # Panning Logic (Middle Click)
    def on_pan_start(self, event):
        self.canvas.config(cursor="fleur")
        self.pan_data['x'] = event.x
        self.pan_data['y'] = event.y

    def on_pan_drag(self, event):
        dx = event.x - self.pan_data['x']
        dy = event.y - self.pan_data['y']
        
        self.offset_x += dx
        self.offset_y += dy
        
        self.pan_data['x'] = event.x
        self.pan_data['y'] = event.y
        self.draw()

    def on_drag(self, event):
        # Node Dragging (Left Click)
        if self.drag_data['item']:
            nid = self.drag_data['item']
            if nid in self.nodes:
                dx = (event.x - self.drag_data['x']) / self.scale
                dy = (event.y - self.drag_data['y']) / self.scale
                
                self.nodes[nid]['x'] += dx
                self.nodes[nid]['y'] += dy
                
                self.drag_data['x'] = event.x
                self.drag_data['y'] = event.y
                
                self.draw() 
                self.highlight_node(nid) 
            return 
        
        # Fallback to panning if not dragging a node (Left Click Pan)
        # Note: on_click sets scan_mark, so standard scan_dragto works here for Button-1
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def on_release(self, event):
        self.drag_data['item'] = None
        self.canvas.config(cursor="") # Reset cursor

    def on_zoom(self, event):
        # Zoom towards the mouse pointer
        old_scale = self.scale
        
        if event.num == 5 or event.delta < 0:
            scale_factor = 0.9
        else:
            scale_factor = 1.1
            
        new_scale = old_scale * scale_factor
        
        # Cap zoom
        if new_scale < 0.1: new_scale = 0.1
        if new_scale > 5.0: new_scale = 5.0
        
        # Calculate offset adjustment to keep mouse point stationary
        # World coordinates of mouse
        world_x = (event.x - self.offset_x) / old_scale
        world_y = (event.y - self.offset_y) / old_scale
        
        # New offset
        self.offset_x = event.x - (world_x * new_scale)
        self.offset_y = event.y - (world_y * new_scale)
        
        self.scale = new_scale
        self.draw()
        
        if self.drag_data['item']:
            self.highlight_node(self.drag_data['item'])

    def on_double_click(self, event):
        self.reset_view()

    def reset_view(self):
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.draw()

    def highlight_node(self, node_id):
        # Dim all
        self.canvas.itemconfig("node_box", fill="#222", outline="#444")
        self.canvas.itemconfig("node_text", fill="#666")
        self.canvas.itemconfig("node_line", fill="#444")
        self.canvas.itemconfig("edge", fill="#333", width=1)
        
        # Highlight Selected
        self.canvas.itemconfig(f"box_{node_id}", fill="#383838", outline="#fff", width=3)
        self.canvas.itemconfig(f"text_{node_id}", fill="#fff")
        self.canvas.itemconfig(f"line_{node_id}", fill="#fff")
        
        # Highlight Neighbors
        for u, v, _ in self.edges:
            if u == node_id:
                self.canvas.itemconfig(f"edge_{u}_{v}", fill="#ff5555", width=2, dash=())
                self.canvas.itemconfig(f"box_{v}", outline="#ff5555", width=2)
                self.canvas.itemconfig(f"text_{v}", fill="#ffaaaa")
            elif v == node_id:
                self.canvas.itemconfig(f"edge_{u}_{v}", fill="#55ff55", width=2, dash=())
                self.canvas.itemconfig(f"box_{u}", outline="#55ff55", width=2)
                self.canvas.itemconfig(f"text_{u}", fill="#aaffaa")

    def reset_highlight(self):
        self.draw()

    def save_layout(self):
        if not self.nodes:
            messagebox.showinfo("Info", "No layout to save.")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Save Layout",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        
        if file_path:
            layout_data = {}
            for nid, node in self.nodes.items():
                layout_data[nid] = {'x': node['x'], 'y': node['y']}
            
            try:
                with open(file_path, 'w') as f:
                    json.dump(layout_data, f, indent=4)
                self.status_label.config(text=f"Layout saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save layout: {e}")

    def load_layout(self):
        file_path = filedialog.askopenfilename(
            title="Load Layout",
            filetypes=[("JSON Files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    layout_data = json.load(f)
                
                match_count = 0
                for nid, pos in layout_data.items():
                    if nid in self.nodes:
                        self.nodes[nid]['x'] = pos['x']
                        self.nodes[nid]['y'] = pos['y']
                        match_count += 1
                
                self.draw()
                self.status_label.config(text=f"Layout loaded ({match_count} nodes updated)")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load layout: {e}")

    def show_context_menu(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        node_id = None
        for t in tags:
            if t in self.nodes:
                node_id = t
                break
        
        if node_id:
            self.current_context_node = node_id
            self.context_menu.post(event.x_root, event.y_root)

    def view_node_code(self):
        if not hasattr(self, 'current_context_node') or not self.current_context_node:
            return
            
        node = self.nodes[self.current_context_node]
        if node['type'] != 'file':
            messagebox.showinfo("Info", "Can only view code for files.")
            return
            
        file_path = node['id'] # id is full path
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                _, ext = os.path.splitext(file_path)
                SyntaxViewer(self, os.path.basename(file_path), content, ext)
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file: {e}")
        else:
             messagebox.showerror("Error", "File not found on disk.")

    def open_node_in_editor(self):
        if not hasattr(self, 'current_context_node') or not self.current_context_node:
            return

        file_path = self.nodes[self.current_context_node]['id']
        if not os.path.exists(file_path):
             messagebox.showerror("Error", "File not found on disk.")
             return
             
        try:
            if platform.system() == 'Darwin':       # macOS
                subprocess.call(('open', file_path))
            elif platform.system() == 'Windows':    # Windows
                os.startfile(file_path)
            else:                                   # linux variants
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not open editor: {e}")