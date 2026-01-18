import tkinter as tk
from tkinter import ttk

from .ui_mixin import VisualExplorerUIMixin
from .data_mixin import VisualExplorerDataMixin
from .layout_universe_mixin import VisualExplorerLayoutUniverseMixin
from .layout_sugiyama_mixin import VisualExplorerLayoutSugiyamaMixin
from .drawing_mixin import VisualExplorerDrawingMixin
from .interaction_mixin import VisualExplorerInteractionMixin
from .highlight_mixin import VisualExplorerHighlightMixin
from .persistence_mixin import VisualExplorerPersistenceMixin
from .context_menu_mixin import VisualExplorerContextMenuMixin

class VisualExplorerTab(ttk.Frame, 
                        VisualExplorerUIMixin, 
                        VisualExplorerDataMixin, 
                        VisualExplorerLayoutUniverseMixin,
                        VisualExplorerLayoutSugiyamaMixin,
                        VisualExplorerDrawingMixin,
                        VisualExplorerInteractionMixin,
                        VisualExplorerHighlightMixin,
                        VisualExplorerPersistenceMixin,
                        VisualExplorerContextMenuMixin):
    
    def __init__(self, notebook, root_app):
        super().__init__(notebook)
        self.notebook = notebook
        self.root_app = root_app 
        
        self.nodes = {} # id -> NodeData
        self.edges = [] # list of (from_id, to_id, type)
        self.file_nodes = {} # file_path -> node_id
        
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.pan_data = {"x": 0, "y": 0}
        
        # Defined Palettes for Hierarchy
        self.folder_palettes = [
            "#FF5733", "#33FF57", "#3357FF", "#FF33F6", "#33FFF6", 
            "#F6FF33", "#FF8C33", "#8C33FF", "#FF338C", "#33FF8C",
            "#D4AC0D", "#1ABC9C", "#9B59B6", "#E74C3C", "#2ECC71"
        ]
        self.folder_colors = {} # folder_path -> color

        self._setup_ui()
        self._setup_context_menu()
