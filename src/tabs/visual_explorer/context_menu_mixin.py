import tkinter as tk
from tkinter import messagebox
import os
import platform
import subprocess
from .syntax_viewer import SyntaxViewer

class VisualExplorerContextMenuMixin:
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
