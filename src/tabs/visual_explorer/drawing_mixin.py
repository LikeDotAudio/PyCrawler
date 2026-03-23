import tkinter as tk

class VisualExplorerDrawingMixin:
    def draw(self):
        import time
        start_time = time.time()
        self.canvas.delete("all")
        if not self.nodes: return
        
        # 1. Draw Nodes (Recursive to ensure parents are behind children)
        roots = [nid for nid, node in self.nodes.items() if not node.get('parent') or node.get('parent') not in self.nodes]
        for root_id in roots:
            self._draw_node_recursive(root_id)
            
        # 2. Draw Edges
        edge_count = 0
        for u, v, etype in self.edges:
            if u not in self.nodes or v not in self.nodes: continue
            if self.visible_nodes and (u not in self.visible_nodes or v not in self.visible_nodes):
                continue
            self._draw_edge(u, v, etype)
            edge_count += 1
            
        end_time = time.time()
        print(f"VisualExplorer: Drawing completed in {end_time - start_time:.3f}s (Edges: {edge_count})")

    def _is_node_or_child_visible(self, nid):
        if not self.visible_nodes or nid in self.visible_nodes: return True
        node = self.nodes.get(nid)
        if not node: return False
        return any(self._is_node_or_child_visible(cid) for cid in node.get('children', []))

    def _draw_node_recursive(self, nid):
        if self.visible_nodes and not self._is_node_or_child_visible(nid):
            return

        node = self.nodes[nid]
        x = self.tx(node['x'])
        y = self.ty(node['y'])
        w = node['w'] * self.scale
        h = node['h'] * self.scale
        
        ntype = node['type']
        
        if ntype == 'dir':
            # Level 1: Directories - Large, light-grey rounded rectangles with thick borders
            self.canvas.create_rectangle(x, y, x+w, y+h, fill="#333333", outline="#555555", width=2, tags=("node", nid, "node_box", f"box_{nid}"))
            
            if getattr(self, 'layout_reverse', False):
                self.canvas.create_text(x+w-10, y+15, text=node['name'], fill="#aaaaaa", font=("Arial", int(12*self.scale), "bold"), anchor="e", tags=("node", nid, "node_text", f"text_{nid}"))
            else:
                self.canvas.create_text(x+10, y+15, text=node['name'], fill="#aaaaaa", font=("Arial", int(12*self.scale), "bold"), anchor="w", tags=("node", nid, "node_text", f"text_{nid}"))
            
        elif ntype == 'file':
            # Level 2: Files - Solid white rectangles (using slightly off-white for dark theme)
            self.canvas.create_rectangle(x, y, x+w, y+h, fill="#ffffff", outline="#cccccc", width=1, tags=("node", nid, "node_box", f"box_{nid}"))
            self.canvas.create_text(x+10, y+15, text=node['name'], fill="#333333", font=("Arial", int(10*self.scale), "bold"), anchor="w", tags=("node", nid, "node_text", f"text_{nid}"))
            
        elif ntype == 'class':
            # Level 3: Classes - Rectangles with a slight blue tint
            self.canvas.create_rectangle(x, y, x+w, y+h, fill="#e6f0ff", outline="#0000ff", width=1, tags=("node", nid, "node_box", f"box_{nid}"))
            self.canvas.create_text(x+10, y+15, text=node['name'], fill="#000088", font=("Arial", int(9*self.scale), "bold"), anchor="w", tags=("node", nid, "node_text", f"text_{nid}"))
            
        elif ntype == 'function':
            # Level 4: Functions/Methods - Small capsules or ovals
            self.canvas.create_oval(x, y, x+w, y+h, fill="#fff9e6", outline="#ffcc00", width=1, tags=("node", nid, "node_box", f"box_{nid}"))
            self.canvas.create_text(x+w/2, y+h/2, text=node['name'], fill="#665500", font=("Arial", int(8*self.scale)), tags=("node", nid, "node_text", f"text_{nid}"))

        # Draw children
        for cid in node.get('children', []):
            self._draw_node_recursive(cid)

    def _draw_edge(self, u, v, etype):
        n1 = self.nodes[u]
        n2 = self.nodes[v]
        
        x1 = self.tx(n1['x'] + n1['w']/2)
        y1 = self.ty(n1['y'] + n1['h']/2)
        x2 = self.tx(n2['x'] + n2['w']/2)
        y2 = self.ty(n2['y'] + n2['h']/2)
        
        # Determine colors from prescription
        color = "#777777"
        dash = None
        width = 1
        
        if etype == 'inheritance':
            color = "#0000FF" # BLUE
            width = 2
        elif etype == 'dependency':
            color = "#FF0000" # RED
            width = 2
        elif etype == 'reference':
            color = "#FFA500" # ORANGE
            dash = (4, 2)
            
        # Draw curved line (Bezier-ish using smooth line)
        mid_x = (x1 + x2) / 2
        points = [x1, y1, mid_x, y1, mid_x, y2, x2, y2]
        
        edge_tag = f"edge_{u}_{v}"
        self.canvas.create_line(points, fill=color, width=width, dash=dash, smooth=True, arrow=tk.LAST, tags=("edge", edge_tag))

        def tx(self, x):

            return (x * self.scale) + self.offset_x

    

        def ty(self, y):

            return (y * self.scale) + self.offset_y

    