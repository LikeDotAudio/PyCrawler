# src/tabs/file_types_tab.py

import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
from ..config_manager import ConfigManager
from ..styles import *

class FileTypesTab(ttk.Frame):
    def __init__(self, parent, start_crawl_callback):
        super().__init__(parent)
        self.start_crawl_callback = start_crawl_callback
        self.target_directory = None
        self.extension_vars = {}
        self.config_manager = ConfigManager()
        self.column_exts = {} # Map column name to list of extensions
        
        self.categories = {
            "Compiler Caches": {'.o', '.pyc', '.d', '.rmeta'},
            "Runtime & Index": {'.log', '.tag'},
            "Backups": {'.old', '.tmp', '.bak'},
            "Programming": {'.py', '.rs', '.rlib', '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.ipp', '.js', '.sh', '.bat', 
                            '.java', '.cs', '.rb', '.go', '.php', '.swift', '.kt', '.kts', '.ps1'},
            "Data & Config": {'.json', '.jsonl', '.yaml', '.yml', '.toml', '.ini', '.csv', '.proto', 
                              '.xml', '.env', '.sql', '.db', '.sqlite', '.sqlite3', '.mdb', '.accdb', '.dat'},
            "Web & Markup": {'.html', '.htm', '.svg', '.css', '.jsx', '.ts', '.tsx', '.vue'},
            "Build & Infra": {'.a', '.so', '.cmake', '.lock', '.in', '.nsi', '.desktop', '.sln', '.csproject'},
            "Docs": {'.md', '.txt', '.pdf', '.rst', '.rtf'},
            "Media": {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.webp'},
            "Misc": {'.zip', '.mib', '.expr', '.shw', '.2'}
        }
        
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Top info
        self.info_label = ttk.Label(self, text="No folder selected.", font=("Segoe UI", 10, "bold"), foreground=COLOR_PRIMARY)
        self.info_label.grid(row=0, column=0, pady=15, padx=20, sticky="w")

        # Container for checkboxes
        self.check_frame = ttk.LabelFrame(self, text=" DISCOVERED FILE TYPES ")
        self.check_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(self.check_frame, bg=COLOR_BG_SURFACE, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.check_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.scrollbar.pack(side="right", fill="y")

        # Action Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, pady=15, sticky="ew")
        
        self.scan_btn = ttk.Button(btn_frame, text=" 🔄 RE-SCAN ", command=self._scan_extensions)
        self.scan_btn.pack(side="left", padx=20)

        self.select_all_btn = ttk.Button(btn_frame, text=" SELECT ALL ", command=self._select_all)
        self.select_all_btn.pack(side="left", padx=5)

        self.deselect_all_btn = ttk.Button(btn_frame, text=" DESELECT ALL ", command=self._deselect_all)
        self.deselect_all_btn.pack(side="left", padx=5)

        # Zip Checkbox
        self.make_zip_var = tk.BooleanVar(value=self.config_manager.get_make_zip())
        self.zip_chk = ttk.Checkbutton(btn_frame, text=" ZIP OUTPUT ", variable=self.make_zip_var)
        self.zip_chk.pack(side="right", padx=20)

        # Accent Start Crawl Button
        self.crawl_btn = ttk.Button(btn_frame, text=" 🚀 START CRAWL ", command=self._on_crawl_click, state="disabled")
        self.crawl_btn.pack(side="right", padx=5)

    def update_directory(self, path):
        self.target_directory = path
        self.info_label.config(text=f" 📂 TARGET: {path}")
        self.crawl_btn.config(state="normal")
        # Auto scan
        self._scan_extensions()

    def _scan_extensions(self):
        if not self.target_directory: return
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        extensions = {} # Change set to dict to count
        try:
            for root, dirs, files in os.walk(self.target_directory):
                # Ignore hidden folders like .git, .crawler
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for f in files:
                    _, ext = os.path.splitext(f)
                    if ext:
                        ext_lower = ext.lower()
                        extensions[ext_lower] = extensions.get(ext_lower, 0) + 1
        except Exception as e:
            print(f"Error scanning: {e}")

        self.after(0, lambda: self._populate_checkboxes(extensions))

    def _populate_checkboxes(self, extensions_dict):
        # Clear old
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.extension_vars.clear()
        self.column_exts.clear()

        # Load saved selection
        saved_exts = self.config_manager.get_selected_extensions()
        
        # Default checked: exclude Caches, Runtime, Backups, and Misc by default
        default_checked = self.categories["Programming"].union(
            self.categories["Data & Config"]
        ).union(
            self.categories["Web & Markup"]
        ).union(
            self.categories["Build & Infra"]
        ).union(
            self.categories["Docs"]
        )

        # Categorize
        categorized_exts = {cat: [] for cat in self.categories.keys()}
        categorized_exts["Other"] = []

        # extensions_dict keys are the extensions
        for ext in extensions_dict.keys():
            found = False
            for cat, known_exts in self.categories.items():
                if ext in known_exts:
                    categorized_exts[cat].append(ext)
                    found = True
                    break
            if not found:
                categorized_exts["Other"].append(ext)

        self.column_exts = categorized_exts

        # Setup Columns
        columns = list(self.categories.keys()) + ["Other"]
        
        for i, col_name in enumerate(columns):
            # Column Header
            header = ttk.Label(self.scrollable_frame, text=col_name.upper(), font=("Segoe UI", 10, "bold"), foreground=COLOR_PRIMARY)
            header.grid(row=0, column=i, sticky="nw", padx=15, pady=(10, 5))

            # Items first to determine button state
            exts_in_col = sorted(categorized_exts[col_name])
            row_idx = 2
            for ext in exts_in_col:
                if saved_exts:
                    is_checked = ext in saved_exts
                else:
                    is_checked = ext in default_checked
                
                count = extensions_dict[ext]
                label_text = f"{ext} ({count})"
                    
                var = tk.BooleanVar(value=is_checked)
                chk = ttk.Checkbutton(self.scrollable_frame, text=label_text, variable=var)
                chk.grid(row=row_idx, column=i, sticky="w", padx=15, pady=2)
                self.extension_vars[ext] = var
                # Update button text if state changes manually
                var.trace_add("write", lambda *args, c=col_name: self._sync_column_button(c))
                row_idx += 1

            # Select All Column Button
            all_sel = all(self.extension_vars[ext].get() for ext in exts_in_col) if exts_in_col else False
            btn_text = "DESELECT" if all_sel else "SELECT"
            
            btn = ttk.Button(self.scrollable_frame, text=btn_text, width=10)
            btn.config(command=lambda b=btn, c=col_name: self._toggle_column(b, c))
            btn.grid(row=1, column=i, sticky="w", padx=15, pady=(0, 15))
            
            if not hasattr(self, 'column_buttons'):
                self.column_buttons = {}
            self.column_buttons[col_name] = btn

        for i in range(len(columns)):
            self.scrollable_frame.grid_columnconfigure(i, weight=1, minsize=160)


    def _sync_column_button(self, col_name):
        if not hasattr(self, 'column_buttons') or col_name not in self.column_buttons:
            return
        exts = self.column_exts.get(col_name, [])
        if not exts: return
        all_selected = all(self.extension_vars[ext].get() for ext in exts if ext in self.extension_vars)
        self.column_buttons[col_name].config(text="DESELECT" if all_selected else "SELECT")

    def _toggle_column(self, btn, col_name):
        exts = self.column_exts.get(col_name, [])
        if not exts: return
        
        all_selected = all(self.extension_vars[ext].get() for ext in exts if ext in self.extension_vars)
        target_state = not all_selected
        
        for ext in exts:
            if ext in self.extension_vars:
                self.extension_vars[ext].set(target_state)
        
        btn.config(text="DESELECT" if target_state else "SELECT")

    def _select_all(self):
        for var in self.extension_vars.values():
            var.set(True)

    def _deselect_all(self):
        for var in self.extension_vars.values():
            var.set(False)

    def _on_crawl_click(self):
        if not self.target_directory: return
        
        selected_exts = [ext for ext, var in self.extension_vars.items() if var.get()]
        if not selected_exts:
            messagebox.showwarning("No types", "Please select at least one file type to crawl.")
            return

        # Save preferences
        self.config_manager.set_selected_extensions(selected_exts)
        self.config_manager.set_make_zip(self.make_zip_var.get())

        self.start_crawl_callback(self.target_directory, selected_exts, self.make_zip_var.get())