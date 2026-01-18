import tkinter as tk

class VisualExplorerDrawingMixin:
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
