class VisualExplorerInteractionMixin:
    
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
        
        # Optimize: Move all items on canvas instead of full redraw
        self.canvas.move("all", dx, dy)

    def on_zoom_btn(self, factor):
        # Zoom centered on canvas center
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        event = type('event', (), {'x': canvas_w/2, 'y': canvas_h/2, 'delta': 1 if factor > 1 else -1, 'num': 4 if factor > 1 else 5})
        self.on_zoom(event)

    def fit_to_view(self, target_nodes=None):
        if target_nodes is None:
            target_nodes = list(self.nodes.values())
            
        if not target_nodes: return
        
        # Calculate Bounding Box
        min_x = min(n['x'] for n in target_nodes)
        max_x = max(n['x'] + n['w'] for n in target_nodes)
        min_y = min(n['y'] for n in target_nodes)
        max_y = max(n['y'] + n['h'] for n in target_nodes)
        
        graph_w = max_x - min_x
        graph_h = max_y - min_y
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if graph_w == 0 or graph_h == 0: return
        
        # Calculate scale to fit
        scale_x = (canvas_w - 100) / graph_w
        scale_y = (canvas_h - 100) / graph_h
        self.scale = min(scale_x, scale_y)
        
        # Cap scale
        if self.scale > 1.0: self.scale = 1.0
        if self.scale < 0.05: self.scale = 0.05
        
        # Center the bounding box
        self.offset_x = (canvas_w / 2) - ((min_x + graph_w/2) * self.scale)
        self.offset_y = (canvas_h / 2) - ((min_y + graph_h/2) * self.scale)
        
        self.draw()

    def on_drag(self, event):
        # Node Dragging (Left Click)
        if self.drag_data['item']:
            nid = self.drag_data['item']
            if nid in self.nodes:
                dx = (event.x - self.drag_data['x']) / self.scale
                dy = (event.y - self.drag_data['y']) / self.scale
                
                self._move_node_recursive(nid, dx, dy)
                
                self.drag_data['x'] = event.x
                self.drag_data['y'] = event.y
                
                self.draw() 
                self.highlight_node(nid) 
            return 
        
        # Fallback to panning if not dragging a node (Left Click Pan)
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _move_node_recursive(self, nid, dx, dy):
        node = self.nodes[nid]
        node['x'] += dx
        node['y'] += dy
        for cid in node.get('children', []):
            self._move_node_recursive(cid, dx, dy)

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

    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection: return
        node_id = selection[0]
        
        # Filtering Logic
        self.visible_nodes.clear()
        node = self.nodes.get(node_id)
        if node:
            if node['type'] == 'dir' and node_id == 'root':
                # Show all if root selected
                pass
            else:
                # Add current node and all its children/descendants
                self._add_to_visible_recursive(node_id)
                
                # Add ancestors
                curr = node.get('parent')
                while curr and curr in self.nodes:
                    self.visible_nodes.add(curr)
                    curr = self.nodes[curr].get('parent')
                
                # If it's a file, also add related nodes (imports/dependencies/references)
                if node['type'] == 'file':
                    for u, v, etype in self.edges:
                        if u == node_id: self._add_to_visible_recursive(v)
                        if v == node_id: self._add_to_visible_recursive(u)

        self.draw()
        
        # Auto-fit to the new selection
        if self.visible_nodes:
            self.fit_to_view([self.nodes[nid] for nid in self.visible_nodes if nid in self.nodes])
        else:
            self.fit_to_view()
            
        self.highlight_node(node_id)

    def _add_to_visible_recursive(self, nid):
        if nid not in self.nodes: return
        self.visible_nodes.add(nid)
        for cid in self.nodes[nid].get('children', []):
            self._add_to_visible_recursive(cid)

    def center_on_node(self, node_id):
        if node_id not in self.nodes: return
        
        node = self.nodes[node_id]
        
        # Target position (center of canvas)
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Set scale to something readable if it's too small/large
        if self.scale < 0.5: self.scale = 0.8
        
        # Calculate offsets to center the node
        # world_x * scale + offset_x = canvas_w / 2
        # offset_x = canvas_w / 2 - (world_x * scale)
        
        self.offset_x = (canvas_w / 2) - ((node['x'] + node['w']/2) * self.scale)
        self.offset_y = (canvas_h / 2) - ((node['y'] + node['h']/2) * self.scale)
        
        self.draw()
        self.highlight_node(node_id)
