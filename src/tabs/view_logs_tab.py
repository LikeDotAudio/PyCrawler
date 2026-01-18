# src/tabs/view_logs_tab.py

import tkinter as tk
from tkinter import ttk
import os
from ..styles import *

class ViewLogsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # We want 2 columns with Text widgets
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Crawl.log Column
        self.frame_log = ttk.LabelFrame(self, text=" 📝 Crawl.log ")
        self.frame_log.grid(row=0, column=0, sticky="nsew", padx=5, pady=10)
        self.text_log = self._create_text_area(self.frame_log)

        # 2. MAP.txt Column
        self.frame_map = ttk.LabelFrame(self, text=" 🗺️ MAP.txt ")
        self.frame_map.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        self.text_map = self._create_text_area(self.frame_map)

        # State for lazy loading
        self.file_handlers = {} # widget -> file_handle
        self.loading_active = {} # widget -> bool

    def _create_text_area(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        text = tk.Text(parent, wrap="none", font=("Consolas", 9), 
                       bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_MAIN, 
                       bd=0, insertbackground=COLOR_TEXT_MAIN,
                       highlightthickness=1, highlightbackground=COLOR_BORDER)
        text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ysb = ttk.Scrollbar(parent, orient="vertical", command=text.yview)
        ysb.grid(row=0, column=1, sticky="ns")
        
        xsb = ttk.Scrollbar(parent, orient="horizontal", command=text.xview)
        xsb.grid(row=1, column=0, sticky="ew")
        
        # Custom scroll handler for infinite scroll
        def on_scroll(*args):
            ysb.set(*args)
            if float(args[1]) > 0.99:
                self._load_more(text)

        text.configure(yscrollcommand=on_scroll, xscrollcommand=xsb.set)
        return text

    def load_files(self, output_dir):
        if not output_dir or not os.path.isdir(output_dir):
            return
        
        # Close old handles
        for f in self.file_handlers.values():
            if f: f.close()
        self.file_handlers.clear()

        self._init_lazy_load(os.path.join(output_dir, "Crawl.log"), self.text_log)
        self._init_lazy_load(os.path.join(output_dir, "MAP.txt"), self.text_map)

    def _init_lazy_load(self, path, text_widget):
        text_widget.config(state="normal")
        text_widget.delete("1.0", "end")
        text_widget.config(state="disabled")
        
        if os.path.exists(path):
            try:
                f = open(path, "r", encoding="utf-8", errors="replace")
                self.file_handlers[text_widget] = f
                self.loading_active[text_widget] = False
                self._load_more(text_widget)
            except Exception as e:
                text_widget.config(state="normal")
                text_widget.insert("1.0", f"Error opening file: {e}")
                text_widget.config(state="disabled")
        else:
            text_widget.config(state="normal")
            text_widget.insert("1.0", "File not found.")
            text_widget.config(state="disabled")

    def _load_more(self, text_widget):
        if self.loading_active.get(text_widget, False): return
        if text_widget not in self.file_handlers: return
        
        f = self.file_handlers[text_widget]
        if f.closed: return

        self.loading_active[text_widget] = True
        
        try:
            lines = []
            for _ in range(500): # Read 500 lines at a time
                line = f.readline()
                if not line:
                    f.close()
                    del self.file_handlers[text_widget]
                    break
                lines.append(line)
            
            if lines:
                text_widget.config(state="normal")
                text_widget.insert("end", "".join(lines))
                text_widget.config(state="disabled")
        except Exception as e:
            pass
        
        self.loading_active[text_widget] = False
