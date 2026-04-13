#!/usr/bin/env python3
import os
import shutil

# Determine the absolute path of the project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DESKTOP_FILE_SOURCE = os.path.join(PROJECT_DIR, "Crawler.desktop")
DESKTOP_FILE_DEST = os.path.expanduser("~/.local/share/applications/Crawler.desktop")
ICON_PATH = os.path.join(PROJECT_DIR, "crawler_icon.svg")
EXEC_PATH = os.path.join(PROJECT_DIR, "run_crawler.sh")

def update_desktop_file():
    """Updates the paths in the Crawler.desktop file to match the current directory."""
    print(f"Updating {DESKTOP_FILE_SOURCE} with correct paths...")
    
    with open(DESKTOP_FILE_SOURCE, "r") as f:
        lines = f.readlines()
    
    with open(DESKTOP_FILE_SOURCE, "w") as f:
        for line in lines:
            if line.startswith("Exec="):
                f.write(f"Exec=\"{EXEC_PATH}\"\n")
            elif line.startswith("Icon="):
                f.write(f"Icon={ICON_PATH}\n")
            else:
                f.write(line)

def install_desktop_shortcut():
    """Copies the desktop shortcut to the user's applications folder."""
    print(f"Installing desktop shortcut to {DESKTOP_FILE_DEST}...")
    
    # Ensure the destination directory exists
    os.makedirs(os.path.dirname(DESKTOP_FILE_DEST), exist_ok=True)
    
    # Copy the desktop file
    shutil.copy2(DESKTOP_FILE_SOURCE, DESKTOP_FILE_DEST)
    
    # Ensure the desktop file is executable
    os.chmod(DESKTOP_FILE_DEST, 0o755)
    
    # Ensure run_crawler.sh is executable
    os.chmod(EXEC_PATH, 0o755)
    
    print("Installation complete. You should now find 'Crawler' in your applications menu and can pin it to your taskbar.")

if __name__ == "__main__":
    update_desktop_file()
    install_desktop_shortcut()
