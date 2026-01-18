# main.py

import os
import sys
import tkinter as tk

# Ensure src is in path if needed (though standard import should work if run from root)
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.gui_module import FolderCrawlerApp

if __name__ == "__main__":
    root = tk.Tk()
    start_directory = os.path.dirname(os.path.abspath(__file__))
    app = FolderCrawlerApp(root, start_directory)
    root.mainloop()
