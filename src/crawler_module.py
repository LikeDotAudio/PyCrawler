# src/crawler_module.py

import os
import shutil
import inspect
import re
from .file_processor_module import FileProcessor
from .utils_module import debug_log, current_version

class Crawler:
    def __init__(self, target_directory, saver, allowed_extensions=None, log_callback=None):
        self.target_directory = target_directory
        self.saver = saver
        self.allowed_extensions = allowed_extensions
        self.log_callback = log_callback
        self.current_file = os.path.basename(__file__)
        self.file_processor = FileProcessor(log_callback=log_callback)

    def crawl(self):
        current_function = inspect.currentframe().f_code.co_name
        debug_log(message=f"Starting crawl of {self.target_directory}", file=self.current_file, version=current_version, function=current_function)

        if not os.path.isdir(self.target_directory):
            msg = f"❌ Error: '{self.target_directory}' is not a valid directory."
            if self.log_callback:
                self.log_callback(msg, "header")
            self.saver.write_log(msg)
            return

        if self.log_callback:
            self.log_callback(f"Crawling directory: {self.target_directory}", "header")
        self.saver.write_log(f"Crawling directory: {self.target_directory}")

        map_output_lines = []
        root_dir_name = os.path.basename(self.target_directory)
        map_output_lines.append(f"# └── {root_dir_name}/\n")

        for root, dirs, files in os.walk(self.target_directory, topdown=True):
            # Delete __pycache__
            if '__pycache__' in dirs:
                cache_path = os.path.join(root, '__pycache__')
                try:
                    if self.log_callback:
                        self.log_callback(f"  [DELETING] Found and deleted __pycache__: {cache_path}", "header")
                    shutil.rmtree(cache_path)
                    dirs.remove('__pycache__')
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"  ❌ Error deleting __pycache__: {e}", "header")

            # Ignore crawl output directories and ignored folders
            dirs_to_remove = []
            for d in dirs:
                if d.lower() == 'crawl' or d.lower() == '.crawler' or re.match(r'^\d{14}$', d) or d.startswith('.'):
                    dirs_to_remove.append(d)
            for d in dirs_to_remove:
                dirs.remove(d)

            relative_root = os.path.relpath(root, self.target_directory)
            if relative_root == ".":
                current_indent_level = 0
            else:
                current_indent_level = relative_root.count(os.sep) + 1
                display_root = relative_root + os.sep
                if self.log_callback:
                    self.log_callback(f"\n└── {display_root}", "dir")
                self.saver.write_log(f"\n└── {display_root}")
                
                indent_str = "    " * (current_indent_level - 1)
                map_output_lines.append(f"#{indent_str}└── {os.path.basename(root)}/\n")

            all_items = sorted(dirs) + sorted(files)
            for i, item in enumerate(all_items):
                is_last = (i == len(all_items) - 1)
                prefix = "└── " if is_last else "├── "
                indent_str = "    " * current_indent_level

                if item in dirs:
                    map_output_lines.append(f"#{indent_str}{prefix}{item}/\n")
                    if self.log_callback:
                        self.log_callback(f"  {indent_str}{prefix}{item}", "dir")
                    self.saver.write_log(f"  {indent_str}{prefix}{item}")
                elif item in files:
                    if item.lower() == "__init__.py":
                        continue
                    
                    file_path = os.path.join(root, item)
                    
                    # Filter by extension if provided
                    if self.allowed_extensions is not None:
                        _, ext = os.path.splitext(item)
                        if ext.lower() not in self.allowed_extensions:
                            continue

                    line_count = 0
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count = sum(1 for _ in f)
                    except:
                        line_count = 'N/A'
                    
                    file_line = f"#{indent_str}{prefix}{item} (Lines: {line_count})"
                    map_output_lines.append(file_line + "\n")

                    if self.log_callback:
                        self.log_callback(f"  {indent_str}{prefix}{item} (Lines: {line_count})", "file")
                    self.saver.write_log(f"  {indent_str}{prefix}{item}")

                    # File Processing
                    # Check extension against allowed list or default list for processing
                    # Even if allowed, we might only want to process text-based ones for EVERYTHING log
                    if item.lower().endswith(('.py', '.csv', '.ini', '.md', '.json', '.txt', '.xml', '.html', '.css', '.js', '.yml', '.yaml', '.cs', '.sln', '.csproject')) and not item.lower().endswith('.log') and item.lower() != "__init__.py":
                        if item.lower().endswith(".py"):
                            py_lines = self.file_processor.analyze_python_file(file_path, current_indent_level + 1)
                            for line in py_lines:
                                map_output_lines.append(line + "\n")
                        elif item.lower().endswith(".json"):
                            json_lines = self.file_processor.analyze_json_file(file_path, current_indent_level + 1)
                            for line in json_lines:
                                map_output_lines.append(line + "\n")
                        
                        # Write to EVERYTHING log
                        try:
                            with open(file_path, "r", encoding="utf-8", errors='replace') as gf:
                                content = gf.read()
                            
                            relative_path = os.path.join(os.path.basename(self.target_directory), os.path.relpath(file_path, self.target_directory))
                            
                            if self.log_callback:
                                self.log_callback(f"    [APPENDING] {item} to EVERYTHING.py.LOG", "import")
                            
                            self.saver.write_everything(
                                f"#####################################\n"
                                f"### File: {relative_path}\n"
                                f"#####################################\n"
                                f"{content}\n\n"
                            )
                        except Exception as e:
                            if self.log_callback:
                                self.log_callback(f"    ❌ Error reading {item}: {e}", "header")

                    elif item.lower() == "__init__.py":
                        if self.log_callback:
                            self.log_callback(f"    [INFO] Ignoring __init__.py: {item}", "file")
        
        self.saver.write_map(map_output_lines)