import tkinter as tk
from tkinter import Toplevel
import re

class SyntaxViewer(Toplevel):
    def __init__(self, parent, title, content, file_ext):
        super().__init__(parent)
        self.title(f"Code View: {title}")
        self.geometry("800x600")
        self.configure(bg="#1e1e1e")
        
        self.text_area = tk.Text(self, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 11), 
                                 insertbackground="white", selectbackground="#264f78")
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_area.insert("1.0", content)
        
        self._highlight_syntax(file_ext)
        self.text_area.config(state="disabled") # Read-only

    def _highlight_syntax(self, ext):
        # Basic regex-based highlighting for common keywords
        keywords = {
            ".py": r'\b(def|class|import|from|return|if|else|elif|for|while|try|except|with|as|pass|None|True|False)\b',
            ".js": r'\b(function|const|let|var|if|else|for|while|return|import|export|default|class|this|new)\b',
            ".json": r'\b(true|false|null)\b'
        }
        
        comment_patterns = {
            ".py": r'(#.*)',
            ".js": r'(//.*)',
            ".json": r'' 
        }
        
        string_pattern = r'(".*?"|".*?")'
        
        # Configure tags
        self.text_area.tag_configure("keyword", foreground="#569cd6") # Blue
        self.text_area.tag_configure("string", foreground="#ce9178")  # Orange/Red
        self.text_area.tag_configure("comment", foreground="#6a9955") # Green
        self.text_area.tag_configure("number", foreground="#b5cea8")  # Light Green
        
        content = self.text_area.get("1.0", "end")
        
        # Highlight Strings
        for match in re.finditer(string_pattern, content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.text_area.tag_add("string", start, end)

        # Highlight Keywords
        kw_regex = keywords.get(ext, "")
        if kw_regex:
             for match in re.finditer(kw_regex, content):
                start = f"1.0 + {match.start()} chars"
                end = f"1.0 + {match.end()} chars"
                self.text_area.tag_add("keyword", start, end)
        
        # Highlight Comments
        cmt_regex = comment_patterns.get(ext, "")
        if cmt_regex:
            for match in re.finditer(cmt_regex, content):
                start = f"1.0 + {match.start()} chars"
                end = f"1.0 + {match.end()} chars"
                self.text_area.tag_add("comment", start, end)
