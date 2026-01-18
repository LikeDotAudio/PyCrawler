# src/regenerator_module.py

import os
import re
import threading
import inspect
from tkinter import messagebox
from .utils_module import debug_log, current_version

class ProjectRegenerator:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.current_file = os.path.basename(__file__)

    def regenerate(self, log_file_path, destination_dir):
        """
        Regenerates files from the EVERYTHING.py.LOG file.
        """
        current_function = inspect.currentframe().f_code.co_name
        
        if self.log_callback:
             self.log_callback(f"--- Starting regeneration from: {os.path.basename(log_file_path)} ---", "header")
             self.log_callback(f"Restoring to: {destination_dir}", "header")

        debug_log(message=f"Starting regeneration from log: {log_file_path}",
                  file=self.current_file, version=current_version, function=current_function)
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Regex to split files based on the separator used in saver_module
            file_blocks = re.split(r'#{37}\n### File: (.+)\n#{37}\n', content)
            
            if len(file_blocks) <= 1:
                if self.log_callback:
                    self.log_callback("❌ Error: Invalid log file format.", "header")
                return False
            
            # Heuristic to find root
            if len(file_blocks) > 1:
                # file_blocks[1] is the first file path
                first_path = file_blocks[1].strip()
                original_root_name = os.path.basename(os.path.dirname(first_path))
            else:
                original_root_name = ""

            # The first block [0] is the MAP.txt header/content before the first file, ignore it or process separately
            
            for i in range(1, len(file_blocks), 2):
                original_file_path = file_blocks[i].strip()
                file_content = file_blocks[i+1]
                
                # Normalize path
                normalized_path = original_file_path.replace('\\', os.sep).replace('/', os.sep)
                
                # Attempt to preserve structure relative to the original root folder name if found
                if original_root_name:
                    root_index = normalized_path.find(original_root_name)
                    if root_index != -1:
                        # logical path starting after the root name
                        # e.g. "Project/src/main.py" -> "src/main.py"
                        # But wait, we usually want to keep the root folder?
                        # The original script kept the relative structure.
                        # Let's just join it to destination.
                        pass

                # If the file path in log is relative "Crawler/src/main.py", we want to put it in "Destination/Crawler/src/main.py"
                # OR "Destination/src/main.py"?
                # The original script tried to be smart. Let's stick to simple joining for now, 
                # but removing the leading directory component if it duplicates the destination?
                # Actually, `os.path.join` is safest.
                
                # However, original_file_path usually includes the top-level directory name.
                # e.g. "MyProject/main.py"
                
                new_file_path = os.path.join(destination_dir, normalized_path)
                
                if self.log_callback:
                    self.log_callback(f"Processing: {new_file_path}", "file")

                try:
                    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                    with open(new_file_path, 'w', encoding='utf-8') as outfile:
                        outfile.write(file_content.strip()) # strip specific newlines added by split?
                        # Actually file_content usually has a trailing newline from the read
                except Exception as e:
                    if self.log_callback:
                        self.log_callback(f"❌ Error creating {new_file_path}: {e}", "header")
                    
            if self.log_callback:
                self.log_callback("\n--- Regeneration complete. 👍 ---", "header")
            
            return True

        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Critical error during regeneration: {e}", "header")
            return False
