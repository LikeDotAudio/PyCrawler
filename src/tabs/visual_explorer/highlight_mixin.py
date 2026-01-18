class VisualExplorerHighlightMixin:
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
