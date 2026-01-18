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
