import tkinter as tk
from tkinter import ttk, Canvas

class VisualExplorerUIMixin:
    def _setup_ui(self):
        # Controls
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.pack(fill="x", side="top", padx=5, pady=5)
        
        ttk.Button(ctrl_frame, text="Analyze Codebase", command=self.analyze_codebase).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Examine Database", command=self.examine_database).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Reverse Layout", command=self.toggle_reverse_layout).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Load Map", command=self.reload_map).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Reset View", command=self.reset_view).pack(side="left", padx=5)
        
        ttk.Separator(ctrl_frame, orient="vertical").pack(side="left", padx=10, fill="y")
        ttk.Button(ctrl_frame, text="Zoom In", command=lambda: self.on_zoom_btn(1.2)).pack(side="left", padx=2)
        ttk.Button(ctrl_frame, text="Zoom Out", command=lambda: self.on_zoom_btn(0.8)).pack(side="left", padx=2)
        ttk.Button(ctrl_frame, text="Fit View", command=self.fit_to_view).pack(side="left", padx=2)
        
        # New Export/Import Buttons
        ttk.Separator(ctrl_frame, orient="vertical").pack(side="left", padx=10, fill="y")
        ttk.Button(ctrl_frame, text="Save Layout", command=self.save_layout).pack(side="left", padx=5)
        ttk.Button(ctrl_frame, text="Load Layout", command=self.load_layout).pack(side="left", padx=5)

        self.status_label = ttk.Label(ctrl_frame, text="Ready", foreground="gray")
        self.status_label.pack(side="right", padx=5)

        # Main Area with Sidebar
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        # Sidebar (Treeview)
        sidebar = ttk.Frame(self.paned)
        self.paned.add(sidebar, weight=1)

        self.tree = ttk.Treeview(sidebar, show="tree", selectmode="browse")
        self.tree.pack(fill="both", expand=True, side="left")
        
        tree_scroll = ttk.Scrollbar(sidebar, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(fill="y", side="right")
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Canvas Area
        canvas_frame = ttk.Frame(self.paned)
        self.paned.add(canvas_frame, weight=4)

        self.canvas = Canvas(canvas_frame, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.canvas.bind("<ButtonPress-2>", self.on_pan_start)
        self.canvas.bind("<B2-Motion>", self.on_pan_drag)
        
        self.canvas.bind("<MouseWheel>", self.on_zoom) # Windows/MacOS
        self.canvas.bind("<Button-4>", self.on_zoom) # Linux Up
        self.canvas.bind("<Button-5>", self.on_zoom) # Linux Down
        
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.show_context_menu) # Right Click

    def _setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="View Code", command=self.view_node_code)
        self.context_menu.add_command(label="Open in Editor", command=self.open_node_in_editor)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Highlight Dependencies", command=lambda: self.highlight_node(self.current_context_node))
