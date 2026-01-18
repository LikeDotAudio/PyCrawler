# src/file_processor_module.py

import ast
import os
import inspect
import json
from .utils_module import debug_log, current_version

class FileProcessor:
    def __init__(self, log_callback=None, file_log_callback=None):
        self.log_callback = log_callback
        self.file_log_callback = file_log_callback # Callback to write to the physical log file
        self.current_file = os.path.basename(__file__)

    def analyze_json_file(self, file_path, indent_level):
        """
        Parses a JSON file and extracts top-level keys.
        Returns a list of formatted strings for MAP.txt.
        """
        analysis_lines = []
        indent_str = "    " * indent_level
        inner_item_indent_prefix = indent_str + "    |   "
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                keys = list(data.keys())
                # specific request: break it out into a tree with at least 2 of it's key values
                # We will list up to 10 keys to be safe and useful
                shown_keys = keys[:10]
                
                if keys:
                     if self.log_callback:
                        self.log_callback(f"    [JSON] Keys in {os.path.basename(file_path)}: {', '.join(shown_keys)}", "file")

                     for key in shown_keys:
                         val_type = type(data[key]).__name__
                         analysis_lines.append(f"#{inner_item_indent_prefix}-> Key: {key} ({val_type})")
                     
                     if len(keys) > 10:
                         analysis_lines.append(f"#{inner_item_indent_prefix}-> ... ({len(keys) - 10} more keys)")
            else:
                 # It might be a list
                 analysis_lines.append(f"#{inner_item_indent_prefix}-> [Root is a List with {len(data)} items]")

        except json.JSONDecodeError as e:
            analysis_lines.append(f"#{indent_str}    - JSON Decode Error: {e}")
        except Exception as e:
            analysis_lines.append(f"#{indent_str}    - Error analyzing JSON: {e}")
            
        return analysis_lines

    def analyze_python_file(self, file_path, indent_level):
        """
        Parses a Python file and extracts function, class, import definitions.
        Returns a list of formatted strings for MAP.txt.
        """
        current_function = inspect.currentframe().f_code.co_name
        debug_log(message=f"Analyzing Python file: {file_path}. Parsing! 🧐",
                    file=self.current_file, version=current_version, function=current_function)

        analysis_lines = []
        indent_str = "    " * indent_level
        inner_item_indent_prefix = indent_str + "    |   "

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            imports_found = set()
            functions_found = []
            classes_found = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_found.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports_found.add(node.module)
                elif isinstance(node, ast.FunctionDef):
                    params = [a.arg for a in node.args.posonlyargs] + \
                             [a.arg for a in node.args.args] + \
                             [a.arg for a in node.args.kwonlyargs]
                    function_signature = f"{node.name}({', '.join(params)})"
                    functions_found.append(function_signature)
                elif isinstance(node, ast.ClassDef):
                    classes_found.append(node.name)

            if functions_found or classes_found or imports_found:
                # Log to GUI/File via callback
                if self.log_callback:
                    self.log_callback(f"    [PY] Analysis for {os.path.basename(file_path)}:", "python_file")
                
                if imports_found:
                    imports_str = ', '.join(sorted(list(imports_found)))
                    if self.log_callback:
                        self.log_callback(f"      Imports: {imports_str}", "import")
                    for imp_name in sorted(list(imports_found)):
                        analysis_lines.append(f"#{inner_item_indent_prefix}-> Import: {imp_name}")

                if classes_found:
                    classes_str = ', '.join(sorted(classes_found))
                    if self.log_callback:
                        self.log_callback(f"      Classes: {classes_str}", "class")
                    for cls_name in sorted(classes_found):
                        analysis_lines.append(f"#{inner_item_indent_prefix}-> Class: {cls_name}")

                if functions_found:
                    functions_str = ', '.join(sorted(functions_found))
                    if self.log_callback:
                        self.log_callback(f"      Functions: {functions_str}", "function")
                    for func_signature in sorted(functions_found):
                        analysis_lines.append(f"#{inner_item_indent_prefix}-> Function: {func_signature}")
            else:
                msg = f"    [PY] No functions, classes, or imports found in {os.path.basename(file_path)}"
                if self.log_callback:
                    self.log_callback(msg, "python_file")
                analysis_lines.append(f"#{indent_str}    - No functions, classes, or imports found.")

        except SyntaxError as e:
            msg = f"    ❌ [PY] Syntax Error in {os.path.basename(file_path)}: {e}"
            if self.log_callback:
                self.log_callback(msg, "python_file")
            analysis_lines.append(f"#{indent_str}    - Syntax Error: {e}")
            debug_log(message=f"Error analyzing {file_path}: {e}", file=self.current_file, version=current_version, function=current_function)
        except Exception as e:
            msg = f"    ❌ [PY] Error analyzing {os.path.basename(file_path)}: {e}"
            if self.log_callback:
                self.log_callback(msg, "python_file")
            analysis_lines.append(f"#{indent_str}    - Error analyzing: {e}")
            debug_log(message=f"Error analyzing {file_path}: {e}", file=self.current_file, version=current_version, function=current_function)
            
        return analysis_lines
