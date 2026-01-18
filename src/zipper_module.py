# src/zipper_module.py

import shutil
import inspect
import os
from .utils_module import debug_log, current_version

def zip_output_directory(output_dir, log_callback=None):
    """
    Zips the output directory.
    """
    current_file = os.path.basename(__file__)
    current_function = inspect.currentframe().f_code.co_name
    
    try:
        zip_filename = output_dir
        shutil.make_archive(zip_filename, 'zip', output_dir)
        
        msg = f"✅ Zipped output directory to: {zip_filename}.zip"
        if log_callback:
            log_callback(msg, "header")
            
        debug_log(message=f"Zipped output directory to: {zip_filename}.zip. ✅",
                  file=current_file, version=current_version, function=current_function)
        return True
    except Exception as e:
        msg = f"❌ Error zipping directory: {e}"
        if log_callback:
            log_callback(msg, "header")
        debug_log(message=f"Error zipping directory: {e}. ❌",
                  file=current_file, version=current_version, function=current_function)
        return False
