# src/config_manager.py

import configparser
import os
import datetime

class ConfigManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
        
        # Ensure sections exist
        if 'General' not in self.config:
            self.config['General'] = {}
        if 'ProcessLog' not in self.config:
            self.config['ProcessLog'] = {}

    def get_last_folder(self):
        return self.config['General'].get('last_folder', '')

    def set_last_folder(self, path):
        self.config['General']['last_folder'] = path
        self._add_recent_folder(path)
        self._save_config()

    def _add_recent_folder(self, path):
        recents = self.get_recent_folders()
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        # Keep max 20
        recents = recents[:20]
        self.config['General']['recent_folders'] = '||'.join(recents)

    def get_recent_folders(self):
        raw = self.config['General'].get('recent_folders', '')
        if not raw:
            # Fallback: if we have a last_folder but no recents list, use it
            last = self.get_last_folder()
            if last:
                return [last]
            return []
        return raw.split('||')

    def get_make_zip(self):
        return self.config['General'].getboolean('make_zip', True)

    def set_make_zip(self, value):
        self.config['General']['make_zip'] = str(value)
        self._save_config()

    def get_selected_extensions(self):
        exts = self.config['General'].get('selected_extensions', '')
        return set(exts.split(',')) if exts else set()

    def set_selected_extensions(self, extensions):
        self.config['General']['selected_extensions'] = ','.join(extensions)
        self._save_config()

    def get_drive_url(self):
        return self.config['General'].get('drive_url', 'https://drive.google.com/drive/u/0/folders/0B0yR0b5T78SKazVhQ3JGLXNrUk0?resourcekey=0-q-4Rsd1Q611mSbfvYImUAQ')

    def log_process(self, action, details):
        """
        Logs a process action with a timestamp.
        """
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # We use the timestamp as the key to ensure uniqueness and order
        log_entry = f"{action}: {details}"
        self.config['ProcessLog'][timestamp] = log_entry
        self._save_config()

    def _save_config(self):
        try:
            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"Error saving config: {e}")
