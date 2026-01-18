# src/tabs/select_folder_tab.py

import tkinter as tk
from tkinter import ttk
import os
import platform
from ..styles import *
from ..config_manager import ConfigManager

class SelectFolderTab(ttk.Frame):
    def __init__(self, parent, on_folder_selected_callback):
        super().__init__(parent)
        self.on_folder_selected_callback = on_folder_selected_callback
        self.selected_path = None
        self.config_manager = ConfigManager()
        
        self._setup_ui()
        self._populate_roots()
        self._load_recents()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1) # Left: Recents
        self.grid_columnconfigure(1, weight=3) # Right: Tree (wider)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel: Recent Projects ---
        self.left_frame = ttk.LabelFrame(self, text=" 🕒 RECENT PROJECTS ")
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Listbox for recents
        self.recent_list = tk.Listbox(self.left_frame, bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_MAIN,
                                      selectbackground=COLOR_PRIMARY, selectforeground="#121212",
                                      bd=0, highlightthickness=0, font=("Segoe UI", 9))
        self.recent_list.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        l_scroll = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.recent_list.yview)
        l_scroll.pack(side="right", fill="y")
        self.recent_list.config(yscrollcommand=l_scroll.set)
        
        self.recent_list.bind("<<ListboxSelect>>", self._on_recent_select)
        self.recent_list.bind("<Double-Button-1>", self._on_recent_double_click)

        # --- Right Panel: Explorer ---
        self.right_frame = ttk.LabelFrame(self, text=" 📂 EXPLORER ")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)

        # Treeview
        self.tree = ttk.Treeview(self.right_frame, selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        vsb = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(self.right_frame, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.bind("<<TreeviewOpen>>", self._on_tree_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        self.tree.heading("#0", text=" File System ", anchor="w")

        # --- Bottom Area ---
        bottom_frame = ttk.Frame(self)
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.path_label = ttk.Label(bottom_frame, text="Please select a folder...", font=("Segoe UI", 10, "italic"), foreground=COLOR_TEXT_MUTED)
        self.path_label.grid(row=0, column=0, padx=20, sticky="w")

        self.select_btn = ttk.Button(bottom_frame, text=" 📁 SELECT THIS FOLDER ", command=self._on_confirm_click, state="disabled")
        self.select_btn.grid(row=0, column=1, padx=20)

    def _populate_roots(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if platform.system() == "Windows":
            import string
            drives = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
            for drive in drives:
                node = self.tree.insert("", "end", text=drive, values=[drive])
                self.tree.insert(node, "end")
        else:
            node = self.tree.insert("", "end", text="/", values=["/"])
            self.tree.insert(node, "end")
            
            home = os.path.expanduser("~")
            node = self.tree.insert("", "end", text="Home", values=[home])
            self.tree.insert(node, "end")
            
        self.selected_path = None
        self.path_label.config(text="Please select a folder...", font=("Segoe UI", 10, "italic"))
        self.select_btn.config(state="disabled")

    def _load_recents(self):
        self.recent_list.delete(0, tk.END)
        recents = self.config_manager.get_recent_folders()
        for path in recents:
            if os.path.exists(path):
                self.recent_list.insert(tk.END, path)

    def _on_tree_open(self, event):
        item = self.tree.focus()
        path = self.tree.item(item, "values")[0]
        
        if self.tree.get_children(item):
            self.tree.delete(*self.tree.get_children(item))
            
        try:
            for p in sorted(os.listdir(path)):
                full_path = os.path.join(path, p)
                if os.path.isdir(full_path) and not p.startswith('.'):
                    node = self.tree.insert(item, "end", text=p, values=[full_path])
                    self.tree.insert(node, "end")
        except PermissionError: pass
        except OSError: pass

    def _on_tree_select(self, event):
        if not self.tree.selection(): return
        item = self.tree.selection()[0]
        path = self.tree.item(item, "values")[0]
        self._set_selection(path)
        
        # Deselect listbox
        self.recent_list.selection_clear(0, tk.END)

    def _on_recent_select(self, event):
        selection = self.recent_list.curselection()
        if not selection: return
        path = self.recent_list.get(selection[0])
        self._set_selection(path)
        self._navigate_tree_to_path(path)

    def _on_recent_double_click(self, event):
        self._on_recent_select(event)
        # Double click already triggers select, but we can ensure expansion is handled
        # _navigate_tree_to_path already expands.

    def _navigate_tree_to_path(self, target_path):
        # 1. Normalize path
        target_path = os.path.normpath(target_path)
        parts = target_path.split(os.sep)
        
        # 2. Find matching root in tree
        current_node = None
        
        # Check roots
        for child in self.tree.get_children():
            root_val = self.tree.item(child, "values")[0]
            # Handle Windows drive letters or Linux root
            if platform.system() == "Windows":
                # Drive letters usually "C:" or "C:\"
                if os.path.normpath(root_val) == os.path.splitdrive(target_path)[0]:
                     current_node = child
                     break
            else:
                if root_val == "/":
                     current_node = child
                     break
                elif root_val == os.path.expanduser("~") and target_path.startswith(root_val):
                     current_node = child
                     break
        
        if not current_node: return

        # 3. Traverse down
        # If we started at Home, we need to adjust parts to match relative path from Home
        root_path = self.tree.item(current_node, "values")[0]
        if target_path.startswith(root_path):
             rel_path = os.path.relpath(target_path, root_path)
             if rel_path == ".": 
                 self.tree.selection_set(current_node)
                 self.tree.see(current_node)
                 return
             sub_parts = rel_path.split(os.sep)
        else:
             # Should be absolute path traversal from system root
             # This is complex across platforms. 
             # For now, let's try to just open if it's a direct child, or rely on user to navigate deep.
             # Implementing full deep tree expansion from scratch is non-trivial without pre-loading.
             # We will try one level at a time.
             sub_parts = parts[1:] if parts[0] == '' else parts # Linux vs Windows

        # Attempt to walk down
        # We need to expand current_node to load children
        self._expand_node(current_node)
        
        for part in sub_parts:
            found = False
            for child in self.tree.get_children(current_node):
                text = self.tree.item(child, "text")
                if text == part:
                    current_node = child
                    self._expand_node(current_node)
                    found = True
                    break
            if not found:
                break
        
        self.tree.selection_set(current_node)
        self.tree.see(current_node)
        self.tree.focus(current_node)

    def _expand_node(self, item):
        self.tree.item(item, open=True)
        # Trigger population if dummy is present
        if len(self.tree.get_children(item)) == 1:
             dummy = self.tree.get_children(item)[0]
             # If dummy doesn't have values, it's likely our dummy
             if not self.tree.item(dummy, "values"):
                 self._on_tree_open_manual(item)

    def _on_tree_open_manual(self, item):
        # Re-use logic from _on_tree_open but for manual call
        path = self.tree.item(item, "values")[0]
        if self.tree.get_children(item):
            self.tree.delete(*self.tree.get_children(item))
            
        try:
            for p in sorted(os.listdir(path)):
                full_path = os.path.join(path, p)
                if os.path.isdir(full_path) and not p.startswith('.'):
                    node = self.tree.insert(item, "end", text=p, values=[full_path])
                    self.tree.insert(node, "end")
        except: pass

    def _set_selection(self, path):
        self.selected_path = path
        self.path_label.config(text=f"Selected: {path}", font=("Segoe UI", 10, "normal"), foreground=COLOR_TEXT_MAIN)
        self.select_btn.config(state="normal")

    def _on_confirm_click(self):
        if self.selected_path and self.on_folder_selected_callback:
            # Refresh recents next time or now?
            # The main app will save it to config, so if we reload recents we see it.
            self.on_folder_selected_callback(self.selected_path)
            self._load_recents() # Reload to show the one we just picked at top

    def get_selected_path(self):
        return self.selected_path