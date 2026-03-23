class VisualExplorerHighlightMixin:
    def highlight_node(self, node_id):
        if node_id not in self.nodes: return
        
        # Dim all nodes and edges
        self.canvas.itemconfig("node_box", fill="#1a1a1a", outline="#333333")
        self.canvas.itemconfig("node_text", fill="#444444")
        self.canvas.itemconfig("edge", fill="#222222", width=1)
        
        # Identify related nodes
        related_nodes = {node_id}
        for u, v, etype in self.edges:
            if u == node_id: related_nodes.add(v)
            if v == node_id: related_nodes.add(u)
            
        # Re-highlight related nodes
        for nid in related_nodes:
            node = self.nodes[nid]
            ntype = node['type']
            
            # Determine original colors
            fill, outline, text_color = "#333", "#555", "#aaa"
            if ntype == 'file': fill, outline, text_color = "#fff", "#ccc", "#333"
            elif ntype == 'class': fill, outline, text_color = "#e6f0ff", "#00f", "#008"
            elif ntype == 'function': fill, outline, text_color = "#fff9e6", "#fc0", "#650"
            
            self.canvas.itemconfig(f"box_{nid}", fill=fill, outline=outline, width=2 if nid == node_id else 1)
            self.canvas.itemconfig(f"text_{nid}", fill=text_color)
            
        # Highlight related edges
        for u, v, etype in self.edges:
            if u == node_id or v == node_id:
                color = "#777"
                if etype == 'inheritance': color = "#0000FF"
                elif etype == 'dependency': color = "#FF0000"
                elif etype == 'reference': color = "#FFA500"
                
                self.canvas.itemconfig(f"edge_{u}_{v}", fill=color, width=2)

    def reset_highlight(self):
        self.draw()
