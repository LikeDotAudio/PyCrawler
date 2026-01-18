import json
import os
from tkinter import filedialog, messagebox

class VisualExplorerPersistenceMixin:
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
