# src/gui_module.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading
import datetime
import subprocess

from .crawler_module import Crawler
from .saver_module import DataSaver
from .zipper_module import zip_output_directory
from .regenerator_module import ProjectRegenerator
from .config_manager import ConfigManager
from .styles import *
from .utils_module import current_version

# Import Tabs
from .tabs.select_folder_tab import SelectFolderTab
from .tabs.file_types_tab import FileTypesTab
from .tabs.regenerate_tab import RegenerateTab
from .tabs.view_logs_tab import ViewLogsTab

class FolderCrawlerApp:
    def __init__(self, root, start_directory):
        self.root = root
        self.root.title("Py Crawl")
        self.root.geometry("1200x800")

        self.output_dir = None
        self.config_manager = ConfigManager()
        
        self._setup_styles()
        self._setup_main_ui()
        self._load_initial_state(start_directory)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Apply Global Background
        self.root.configure(bg=COLOR_BG_APP)
        
        # General widget style
        style.configure(".", 
                        background=COLOR_BG_APP, 
                        foreground=COLOR_TEXT_MAIN, 
                        fieldbackground=COLOR_BG_SURFACE,
                        bordercolor=COLOR_BORDER,
                        lightcolor=COLOR_BORDER,
                        darkcolor=COLOR_BORDER)

        style.configure("TFrame", background=COLOR_BG_APP)
        style.configure("TLabelframe", background=COLOR_BG_APP, foreground=COLOR_PRIMARY, bordercolor=COLOR_BORDER)
        style.configure("TLabelframe.Label", background=COLOR_BG_APP, foreground=COLOR_PRIMARY)
        style.configure("TLabel", background=COLOR_BG_APP, foreground=COLOR_TEXT_MAIN)
        
        # Buttons
        style.configure("TButton", 
                        background=COLOR_BG_INPUT, 
                        foreground=COLOR_TEXT_MAIN, 
                        borderwidth=1, 
                        focusthickness=3, 
                        focuscolor=COLOR_PRIMARY)
        style.map("TButton", 
                  background=[('active', COLOR_BG_SURFACE), ('pressed', COLOR_PRIMARY)],
                  foreground=[('active', COLOR_PRIMARY_HOVER)])
        
        # Special Accent Button Style (Optional: could apply to Start Crawl)
        style.configure("Accent.TButton", background=COLOR_PRIMARY, foreground="#121212")
        style.map("Accent.TButton", background=[('active', COLOR_PRIMARY_HOVER)])

        # Notebook / Tabs
        style.configure("TNotebook", background=COLOR_BG_APP, borderwidth=0)
        style.configure("TNotebook.Tab", 
                        background=COLOR_BG_SURFACE, 
                        foreground=COLOR_TEXT_MUTED, 
                        padding=[15, 5], 
                        borderwidth=1)
        style.map("TNotebook.Tab", 
                  background=[("selected", COLOR_PRIMARY), ("active", COLOR_BG_INPUT)],
                  foreground=[("selected", "#121212"), ("active", COLOR_TEXT_MAIN)])

        # Treeview
        style.configure("Treeview", 
                        background=COLOR_BG_SURFACE, 
                        foreground=COLOR_TEXT_MAIN, 
                        fieldbackground=COLOR_BG_SURFACE,
                        rowheight=25,
                        borderwidth=0)
        style.map("Treeview", 
                  background=[('selected', COLOR_PRIMARY)], 
                  foreground=[('selected', "#121212")])
        
        # Scrollbars
        style.configure("Vertical.TScrollbar", 
                        background=COLOR_BG_INPUT, 
                        troughcolor=COLOR_BG_APP, 
                        borderwidth=0, 
                        arrowcolor=COLOR_TEXT_MUTED)
        style.configure("Horizontal.TScrollbar", 
                        background=COLOR_BG_INPUT, 
                        troughcolor=COLOR_BG_APP, 
                        borderwidth=0, 
                        arrowcolor=COLOR_TEXT_MUTED)

    def _setup_main_ui(self):
        # 1. Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # 2. Instantiate Tabs
        self.tab_select = SelectFolderTab(self.notebook, self._on_folder_selected)
        self.tab_files = FileTypesTab(self.notebook, self._start_crawl)
        self.tab_view = ViewLogsTab(self.notebook)
        self.tab_regen = RegenerateTab(self.notebook, self._start_regeneration)

        self.notebook.add(self.tab_select, text=" 📁 1. SELECT FOLDER ")
        self.notebook.add(self.tab_files, text=" ⚙️ 2. FILE TYPES ")
        self.notebook.add(self.tab_view, text=" 📑 3. VIEW LOGS ")
        self.notebook.add(self.tab_regen, text=" 🛠️ 4. REGENERATE ")

        # 3. Bottom Area for Global Actions
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(bottom_frame, text=" 📂 OPEN OUTPUT FOLDER ", command=self._open_output_folder).pack(side="right", padx=5)

        # 4. Console Log
        self.console_frame = ttk.LabelFrame(self.root, text="System Output")
        self.console_frame.pack(fill="both", expand=False, padx=10, pady=(5, 10))
        
        self.text_area = tk.Text(self.console_frame, height=6, state="disabled", 
                                 bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_MAIN, 
                                 font=("Consolas", 10), insertbackground=COLOR_TEXT_MAIN,
                                 highlightthickness=1, highlightbackground=COLOR_BORDER, bd=0)
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.text_area.tag_configure("dir", foreground=COLOR_DIR)
        self.text_area.tag_configure("file", foreground=COLOR_FILE)
        self.text_area.tag_configure("header", foreground=COLOR_PRIMARY, font=("Consolas", 10, "bold"))
        self.text_area.tag_configure("import", foreground=COLOR_IMPORT)

    def _load_initial_state(self, default_start_dir):
        # Check config for last folder
        last_folder = self.config_manager.get_last_folder()
        if last_folder and os.path.exists(last_folder):
             self._log(f"Restored last session folder: {last_folder}", "header")
             # Pre-select in tree? That might be hard without expanding everything.
             # We can just update the label and state in tab 1 via a method if we wanted,
             # OR just pretend the user selected it (but maybe don't jump tabs yet).
             # For now, let's just log it. The user still has to navigate. 
             # Or we can update the tab_select internal state.
             pass
        else:
             self._log(f"Welcome! Please select a folder to start.", "header")

    def _log(self, message, tag=None):
        def _write():
            self.text_area.config(state="normal")
            self.text_area.insert("end", message + "\n", tag)
            self.text_area.see("end")
            self.text_area.config(state="disabled")
        self.root.after(0, _write)

    # ---

    # -- Callbacks --

    def _on_folder_selected(self, path):
        self._log(f"Selected Target: {path}", "header")
        
        # Save to config
        self.config_manager.set_last_folder(path)
        self.config_manager.log_process("Selection", f"Selected folder {path}")
        
        self.tab_files.update_directory(path)
        self.notebook.select(self.tab_files)

    def _start_crawl(self, target_dir, allowed_extensions, make_zip):
        self._log(f"Starting crawl on {target_dir}", "header")
        ext_list_str = ", ".join(allowed_extensions)
        self.config_manager.log_process("Crawl Start", f"Target: {target_dir}, Types: [{ext_list_str}]")
        
        # New Output Location: Inside target/.crawler/folder_name-timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        folder_name = os.path.basename(target_dir)
        self.output_dir = os.path.join(target_dir, ".crawler", f"{folder_name}-{timestamp}")
        
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 1. Create a .gitignore INSIDE .crawler so everything inside is ignored
            crawler_root = os.path.join(target_dir, ".crawler")
            with open(os.path.join(crawler_root, ".gitignore"), "w") as f:
                f.write("*\n")
            
            # 2. Add .crawler/ to the TARGET directory's .gitignore if it exists
            target_gitignore = os.path.join(target_dir, ".gitignore")
            ignore_line = "\n.crawler/\n"
            
            if os.path.exists(target_gitignore):
                with open(target_gitignore, "r") as f:
                    content = f.read()
                if ".crawler/" not in content:
                    with open(target_gitignore, "a") as f:
                        f.write(ignore_line)
            else:
                # Optional: create a .gitignore in the target folder if it's not there?
                # Usually better to only do it if the user wants it, but for a crawler 
                # that creates hidden folders, it's polite.
                with open(target_gitignore, "w") as f:
                    f.write(ignore_line.strip() + "\n")
                    
        except OSError as e:
             self._log(f"❌ Error creating output dir or gitignore: {e}", "header")
             return
        
        threading.Thread(target=self._crawl_thread, args=(target_dir, allowed_extensions, make_zip), daemon=True).start()

    def _crawl_thread(self, target_dir, allowed_extensions, make_zip):
        saver = DataSaver(self.output_dir, log_callback=self._log)
        saver.open_files()
        
        crawler = Crawler(target_dir, saver, allowed_extensions=allowed_extensions, log_callback=self._log)
        crawler.crawl()
        
        saver.prepend_map_to_everything()
        saver.close_files()
        
        if make_zip:
            zip_output_directory(self.output_dir, log_callback=self._log)
        
        self.config_manager.log_process("Crawl Finish", f"Output: {self.output_dir}")
        self._log(f"\n--- Crawl complete. Output at: {self.output_dir} ---", "header")
        
        # Auto-load into View Logs Tab
        self.root.after(0, lambda: self.tab_view.load_files(self.output_dir))
        self.root.after(0, lambda: self.notebook.select(self.tab_view))
        
        # Also prepare Regenerate Tab just in case
        everything_log = os.path.join(self.output_dir, "EVERYTHING.py.LOG")
        if os.path.exists(everything_log):
             self.root.after(0, lambda: self.tab_regen.load_log_file(everything_log))

        messagebox.showinfo("Crawl Complete", "The crawl has finished successfully.")
        
        # Open the configured URL
        url = self.config_manager.get_drive_url()
        if url:
             try:
                 import webbrowser
                 webbrowser.open(url)
             except Exception as e:
                 self._log(f"❌ Error opening URL: {e}", "header")

    def _start_regeneration(self, log_path):
        destination_dir = filedialog.askdirectory(title="Select Destination for Regeneration")
        if not destination_dir: return
        
        self._log(f"Starting regeneration from {os.path.basename(log_path)} to {destination_dir}", "header")
        self.config_manager.log_process("Regeneration Start", f"Source: {log_path}, Dest: {destination_dir}")
        
        threading.Thread(target=self._regen_thread, args=(log_path, destination_dir), daemon=True).start()

    def _regen_thread(self, log_path, dest_dir):
        regenerator = ProjectRegenerator(log_callback=self._log)
        success = regenerator.regenerate(log_path, dest_dir)
        
        if success:
            self.config_manager.log_process("Regeneration Success", f"Restored to {dest_dir}")
            messagebox.showinfo("Success", f"Restored to:\n{dest_dir}")
        else:
            self.config_manager.log_process("Regeneration Fail", "Error occurred")
            messagebox.showerror("Error", "Regeneration failed. Check log.")

    # ---

    # -- File Opening Helpers --

    def _open_file(self, path):
        if not os.path.exists(path):
            self._log(f"❌ File not found: {path}", "header")
            return
        try:
            if os.name == 'nt': os.startfile(path)
            elif os.uname().sysname == 'Darwin': subprocess.run(['open', path], check=True)
            else: subprocess.run(['xdg-open', path], check=True)
        except Exception as e:
            self._log(f"❌ Error opening file: {e}", "header")

    def _open_output_folder(self):
        if self.output_dir and os.path.exists(self.output_dir):
            self._open_file(self.output_dir)
        else:
            self._log("ℹ️ No active output directory found.", "header")
