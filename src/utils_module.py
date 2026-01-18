# src/utils_module.py

import inspect

# --- Global Version Information ---
current_version = "Version 20260117.010000.1" # Updated date
current_version_hash = (20260117 * 10000 * 1)

def debug_log(message, file, version, function, **kwargs):
    # A simplified debug logging function for this script.
    print(f"DEBUG: {file} - {function} - {message} - Version: {version}")
