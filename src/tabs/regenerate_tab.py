# src/tabs/regenerate_tab.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import threading
from ..styles import *

class RegenerateTab(ttk.Frame):
    def __init__(self, parent, regenerate_callback):
        super().__init__(parent)
        self.regenerate_callback = regenerate_callback
        self.log_file_path = None
        self.file_positions = {} # Map full_path -> start_index in text widget
        
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1) # Tree
        self.grid_columnconfigure(1, weight=2) # Code View
        self.grid_rowconfigure(1, weight=1)

        # --- Top Bar ---
        top_frame = ttk.Frame(self)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=15)

        ttk.Button(top_frame, text=" 📂 LOAD LOG FILE ", command=self._load_log).pack(side="left")
        self.file_label = ttk.Label(top_frame, text="No file loaded.", font=("Segoe UI", 10, "italic"), foreground=COLOR_TEXT_MUTED)
        self.file_label.pack(side="left", padx=15)
        
        self.regen_btn = ttk.Button(top_frame, text=" ⚙️ REGENERATE PROJECT ", command=self._on_regenerate, state="disabled")
        self.regen_btn.pack(side="right")
        
        self.regen_single_btn = ttk.Button(top_frame, text=" 📄 REGENERATE SINGLE FILE ", command=self._on_regen_single, state="disabled")
        self.regen_single_btn.pack(side="right", padx=10)

        # --- Left: Tree Preview Frame ---
        tree_container = ttk.LabelFrame(self, text=" 🔍 PROJECT STRUCTURE ")
        tree_container.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 20))
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(1, weight=1)
        
        # Expand/Collapse Buttons
        btn_box = ttk.Frame(tree_container)
        btn_box.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(btn_box, text="Expand All", command=self._expand_all).pack(side="left", padx=2)
        ttk.Button(btn_box, text="Collapse All", command=self._collapse_all).pack(side="left", padx=2)

        # Tree Preview
        self.tree = ttk.Treeview(tree_container)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        vsb.grid(row=1, column=1, sticky="ns")
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=2, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.heading("#0", text=" Nested File Structure ", anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # Key Bindings for Arrow Keys
        self.tree.bind("<Right>", self._on_right_arrow)
        self.tree.bind("<Left>", self._on_left_arrow)

        # --- Right: Code View Frame ---
        code_container = ttk.LabelFrame(self, text=" 📑 EVERYTHING.py.LOG CONTENT ")
        code_container.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))
        code_container.grid_columnconfigure(0, weight=1)
        code_container.grid_rowconfigure(0, weight=1)
        
        self.text_code = tk.Text(code_container, wrap="none", font=("Consolas", 10), 
                                 bg=COLOR_BG_SURFACE, fg=COLOR_TEXT_MAIN, 
                                 bd=0, insertbackground=COLOR_TEXT_MAIN,
                                 highlightthickness=1, highlightbackground=COLOR_BORDER)
        self.text_code.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        ysb2 = ttk.Scrollbar(code_container, orient="vertical", command=self.text_code.yview)
        ysb2.grid(row=0, column=1, sticky="ns")
        xsb2 = ttk.Scrollbar(code_container, orient="horizontal", command=self.text_code.xview)
        xsb2.grid(row=1, column=0, sticky="ew")
        
        self.text_code.configure(yscrollcommand=ysb2.set, xscrollcommand=xsb2.set)
        
        # Add tags for highlighting
        self.text_code.tag_configure("highlight", background=COLOR_PRIMARY, foreground="#121212")

    def _load_log(self):
        f = filedialog.askopenfilename(
            title="Select EVERYTHING.py.LOG",
            filetypes=[("Log files", "EVERYTHING.py.LOG"), ("All files", "*.*")]
        )
        if not f: return
        self.load_log_file(f)

    def load_log_file(self, path):
        self.log_file_path = path
        self.file_label.config(text=os.path.basename(path))
        self.regen_btn.config(state="normal")
        self.regen_single_btn.config(state="disabled")
        
        # Parse and show tree
        threading.Thread(target=self._process_log_file, args=(path,), daemon=True).start()

    def _process_log_file(self, path):
        # 1. Read Content
        try:
            with open(path, 'r', encoding='utf-8', errors="replace") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading log: {e}")
            return

        # 2. Update Text Widget (Main Thread)
        self.after(0, lambda: self._update_text_content(content))
        
        # 3. Parse Structure
        # Find all "### File: path"
        # We also want to find their positions in the text
        files = []
        positions = {}
        
        # Regex to capture path and the start position of the match
        pattern = re.compile(r'#{37}\n### File: (.+)\n#{37}\n')
        
        for match in pattern.finditer(content):
            file_path = match.group(1)
            start_pos = match.start()
            files.append(file_path)
            positions[file_path] = start_pos
            
        self.file_positions = positions
        self.after(0, lambda: self._populate_tree(files))

    def _update_text_content(self, content):
        self.text_code.config(state="normal")
        self.text_code.delete("1.0", "end")
        self.text_code.insert("1.0", content)
        self.text_code.config(state="disabled")

    def _populate_tree(self, file_paths):
        self.tree.delete(*self.tree.get_children())
        added_paths = {}

        for path in file_paths:
            parts = path.replace('\\', '/').split('/')
            current_full = ""
            parent_id = ""
            
            for part in parts:
                if current_full:
                    current_full = f"{current_full}/{part}"
                else:
                    current_full = part
                    
                if current_full not in added_paths:
                    node_id = self.tree.insert(parent_id, "end", text=part, open=True, values=[current_full])
                    added_paths[current_full] = node_id
                    parent_id = node_id
                else:
                    parent_id = added_paths[current_full]

    def _on_tree_select(self, event):
        if not self.tree.selection():
            self.regen_single_btn.config(state="disabled")
            return
        
        item = self.tree.selection()[0]
        # Check children
        if self.tree.get_children(item):
            self.regen_single_btn.config(state="disabled")
        else:
            self.regen_single_btn.config(state="normal")
            
        # Jump to code
        logical_path = self.tree.item(item, "values")[0]
        
        # The log file paths might differ slightly from tree paths if we did normalization
        # But we built tree paths directly from log paths, so they should match?
        # Except we split by / and re-joined. 
        # The key in self.file_positions is the raw path string from the regex capture.
        # Let's try to match.
        
        # Direct lookup
        # We stored the raw logical path in values?
        # No, we reconstructed it: f"{current_full}/{part}"
        # If the original path had backslashes, our key is different.
        # But self.file_positions has raw paths.
        # Let's verify.
        
        # We need to map our reconstructed tree path back to the file_positions key.
        # Or, safer: iterate positions and normalize keys for lookup.
        
        # Let's normalize self.file_positions keys on creation? No, they are positions in raw text.
        # We need to find the key in file_positions that matches our logical_path (normalized).
        
        target_pos = None
        norm_logical = logical_path.replace('\\', '/')
        
        for fpath, pos in self.file_positions.items():
            if fpath.replace('\\', '/') == norm_logical:
                target_pos = pos
                break
        
        if target_pos is not None:
            self._jump_to_position(target_pos)

    def _jump_to_position(self, char_index):
        # Tkinter text index is line.col
        # Converting raw char index to line.col is expensive if we count.
        # But we inserted the whole string.
        # Text widget has "1.0 + N chars"
        
        idx = f"1.0 + {char_index} chars"
        self.text_code.see(idx)
        
        # Highlight line
        self.text_code.tag_remove("highlight", "1.0", "end")
        # Highlight next 5 lines?
        end_idx = f"{idx} + 1 line"
        self.text_code.tag_add("highlight", idx, end_idx)

    def _expand_all(self):
        def expand_recursive(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand_recursive(child)
        
        for item in self.tree.get_children():
            expand_recursive(item)

    def _collapse_all(self):
         def collapse_recursive(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse_recursive(child)
        
         for item in self.tree.get_children():
            collapse_recursive(item)

    def _on_right_arrow(self, event):
        item = self.tree.focus()
        if item:
            # If closed, open. If open and has children, move to first child?
            # Default behavior handles open. We just ensure it expands.
            if not self.tree.item(item, "open"):
                self.tree.item(item, open=True)
            return "break" # Prevent default if needed, or let it pass

    def _on_left_arrow(self, event):
        item = self.tree.focus()
        if item:
            if self.tree.item(item, "open"):
                self.tree.item(item, open=False)
            else:
                # If closed, move to parent
                parent = self.tree.parent(item)
                if parent:
                    self.tree.selection_set(parent)
                    self.tree.focus(parent)
            return "break"

    def _on_regenerate(self):
        if self.log_file_path:
            self.regenerate_callback(self.log_file_path)
            
    def _on_regen_single(self):
        item = self.tree.selection()[0]
        logical_path = self.tree.item(item, "values")[0]
        file_name = self.tree.item(item, "text")
        
        target_dir = filedialog.askdirectory(title=f"Select Folder to Save '{file_name}'")
        if not target_dir: return
        
        threading.Thread(target=self._extract_single_file, args=(logical_path, target_dir), daemon=True).start()

    def _extract_single_file(self, logical_path, target_dir):
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple header find again, this time to extract content
            # We can reuse the stored position to be faster?
            # But we need the END position too.
            # Let's just regex again for safety or substring from known pos.
            
            # Find the key
            norm_logical = logical_path.replace('\\', '/')
            target_pos = None
            for fpath, pos in self.file_positions.items():
                if fpath.replace('\\', '/') == norm_logical:
                    target_pos = pos
                    break
            
            if target_pos is not None:
                # Find start of content
                # Header is roughly 80 chars? We need to find the newline after the header.
                # Regex was: #{37}\n### File: (.+)\n#{37}\n
                # Let's just grab the substring from target_pos to end
                sub = content[target_pos:]
                # Match regex on substring
                pattern = r'(#{37}\n### File: .+?\n#{37}\n)(.*?)(?=\n#{37}\n### File: |\Z)'
                match = re.search(pattern, sub, re.DOTALL)
                
                if match:
                    file_content = match.group(2)
                    out_path = os.path.join(target_dir, os.path.basename(logical_path))
                    with open(out_path, 'w', encoding='utf-8') as out:
                        out.write(file_content)
                    self.after(0, lambda: messagebox.showinfo("Success", f"File saved to:\n{out_path}"))
                    return

            self.after(0, lambda: messagebox.showerror("Error", f"Could not find file content."))
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"Extraction failed: {e}"))
