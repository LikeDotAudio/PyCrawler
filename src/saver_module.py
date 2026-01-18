# src/saver_module.py

import os
import datetime
import inspect
from .utils_module import debug_log, current_version

class DataSaver:
    def __init__(self, output_dir, log_callback=None):
        self.output_dir = output_dir
        self.log_callback = log_callback
        self.current_file = os.path.basename(__file__)
        self.log_file = None
        self.map_file = None
        self.everything_log_file = None

    def open_files(self):
        current_function = inspect.currentframe().f_code.co_name
        
        log_file_path = os.path.join(self.output_dir, "Crawl.log")
        map_file_path = os.path.join(self.output_dir, "MAP.txt")
        everything_log_file_path = os.path.join(self.output_dir, "EVERYTHING.py.LOG")

        try:
            self.log_file = open(log_file_path, "w", encoding="utf-8")
            self.log_file.write(f"--- Crawl Log Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n")
            if self.log_callback:
                self.log_callback(f"--- Crawl Log Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---", "header")
            debug_log(message=f"Crawl.log opened at {log_file_path}", file=self.current_file, version=current_version, function=current_function)
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Error opening Crawl.log: {e}", "header")
            self.log_file = None

        try:
            self.map_file = open(map_file_path, "w", encoding="utf-8")
            map_header = f"""# Program Map:
# Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
"""
            self.map_file.write(map_header)
            debug_log(message=f"MAP.txt opened at {map_file_path}", file=self.current_file, version=current_version, function=current_function)
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Error opening MAP.txt: {e}", "header")
            self.map_file = None

        try:
            self.everything_log_file = open(everything_log_file_path, "w", encoding="utf-8")
            everything_header = f"""# ====================================================================================
# EVERYTHING.py.LOG
# Log started at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# ====================================================================================\n\n"""
            self.everything_log_file.write(everything_header)
            debug_log(message=f"EVERYTHING.py.LOG opened at {everything_log_file_path}", file=self.current_file, version=current_version, function=current_function)
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"❌ Error opening EVERYTHING.py.LOG: {e}", "header")
            self.everything_log_file = None

    def write_log(self, message):
        if self.log_file:
            try:
                self.log_file.write(message + "\n")
            except Exception:
                pass

    def write_map(self, lines):
        if self.map_file:
            try:
                self.map_file.writelines(lines)
            except Exception:
                pass

    def write_everything(self, content):
        if self.everything_log_file:
            try:
                self.everything_log_file.write(content)
            except Exception:
                pass

    def close_files(self):
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        if self.map_file:
            self.map_file.close()
            self.map_file = None
        if self.everything_log_file:
            self.everything_log_file.close()
            self.everything_log_file = None

    def prepend_map_to_everything(self):
        try:
            map_file_path = os.path.join(self.output_dir, "MAP.txt")
            everything_log_file_path = os.path.join(self.output_dir, "EVERYTHING.py.LOG")

            with open(map_file_path, 'r', encoding='utf-8') as f_map:
                map_content = f_map.read()
            
            with open(everything_log_file_path, 'r', encoding='utf-8') as f_everything:
                everything_content = f_everything.read()

            with open(everything_log_file_path, 'w', encoding='utf-8') as f_everything:
                f_everything.write(map_content)
                f_everything.write("\n\n" + "-"*50 + "\n\n")
                f_everything.write(everything_content)
        except Exception as e:
             debug_log(message=f"Error prepending MAP to EVERYTHING: {e}", file=self.current_file, version=current_version, function="prepend_map_to_everything")
