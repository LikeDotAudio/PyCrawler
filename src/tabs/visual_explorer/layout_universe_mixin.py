class VisualExplorerLayoutUniverseMixin:
    def _calculate_layout_universe(self):
        """
        Layout that treats folders as 'Universes' (containers).
        Files are stacked inside. Sub-folders are zones treeing off.
        """
        if not self.nodes:
            print("Layout Universe: No nodes to layout.")
            return
        
        # 1. Build Tree Structure
        tree, roots = self._build_hierarchy_tree()
        print(f"Layout Universe: Found {len(roots)} roots and {len(self.nodes)} total nodes.")
        
        if not roots:
            print("Layout Universe: No roots found! Is the hierarchy parsing correct?")
            # Fallback: Treat all as roots if hierarchy failed completely
            roots = list(self.nodes.keys())

        # 2. Measure Sizes (Bottom-Up)
        for root_id in roots:
            self._measure_universe(root_id, tree)
        
        # 3. Position Nodes (Top-Down) - Arrange roots horizontally
        current_x = 0
        current_y = 0
        padding = 50
        
        for root_id in roots:
            self._position_universe(root_id, tree, current_x, current_y)
            # Move next root to the right
            width = self.nodes[root_id]['w']
            if width <= 0: width = 250 # Fallback width
            current_x += width + padding
            
        print(f"Layout Universe: Completed. Total width {current_x}.")
        
    def _build_hierarchy_tree(self):
        tree = {nid: {'files': [], 'dirs': []} for nid in self.nodes}
        roots = []
        
        # Find Root (nodes with no parent in hierarchy edges)
        child_ids = set()
        for u, v, etype in self.edges:
            if etype == 'hierarchy':
                child_ids.add(v)
                # Determine type of v
                if self.nodes[v]['type'] == 'file':
                    tree[u]['files'].append(v)
                else:
                    tree[u]['dirs'].append(v)
        
        # Roots are those not in child_ids
        for nid in self.nodes:
            if nid not in child_ids:
                roots.append(nid)
        
        return tree, roots

    def _measure_universe(self, node_id, tree):
        node = self.nodes[node_id]
        padding = 20
        header_height = 40
        
        if node['type'] == 'file':
            # Files have fixed or content-based size
            # Currently using fixed for consistency, or calculation from Sugiyama
            # Let's use a standard file size
            node['w'] = 220
            # Height depends on content (functions/classes)
            content_count = len(node['contents'])
            node['h'] = 60 + (content_count * 18)
            return
            
        # It's a directory
        children_files = tree[node_id]['files']
        children_dirs = tree[node_id]['dirs']
        
        # Measure Children
        max_file_w = 0
        total_files_h = 0
        
        for fid in children_files:
            self._measure_universe(fid, tree)
            if self.nodes[fid]['w'] > max_file_w: max_file_w = self.nodes[fid]['w']
            total_files_h += self.nodes[fid]['h'] + padding
            
        # Measure Subdirs
        total_subdirs_w = 0
        max_subdir_h = 0
        
        for did in children_dirs:
            self._measure_universe(did, tree)
            total_subdirs_w += self.nodes[did]['w'] + padding
            if self.nodes[did]['h'] > max_subdir_h: max_subdir_h = self.nodes[did]['h']
            
        # Calculate Universe Dimensions
        # Layout: Files in a column on Left. Subdirs in a row on Right (or below if no files).
        
        # Width
        content_w = 0
        if children_files and children_dirs:
            content_w = max_file_w + padding + total_subdirs_w
        elif children_files:
            content_w = max_file_w
        elif children_dirs:
            content_w = total_subdirs_w
        else:
            content_w = 200 # Empty folder
            
        node['w'] = content_w + (padding * 2)
        
        # Height
        # Files column height
        col_h = total_files_h
        # Subdirs row height
        row_h = max_subdir_h
        
        content_h = max(col_h, row_h)
        if content_h == 0: content_h = 100
        
        node['h'] = header_height + content_h + (padding * 2)

    def _position_universe(self, node_id, tree, x, y):
        node = self.nodes[node_id]
        padding = 20
        header_height = 40
        
        node['x'] = x
        node['y'] = y
        
        if node['type'] == 'file':
            return
            
        # Position Children
        start_x = x + padding
        start_y = y + header_height + padding
        
        children_files = tree[node_id]['files']
        children_dirs = tree[node_id]['dirs']
        
        # 1. Stack Files
        current_y = start_y
        max_file_w = 0
        for fid in children_files:
            fnode = self.nodes[fid]
            self._position_universe(fid, tree, start_x, current_y)
            current_y += fnode['h'] + padding
            if fnode['w'] > max_file_w: max_file_w = fnode['w']
            
        # 2. Tree off Subdirs (to the right of files)
        subdir_start_x = start_x
        if children_files:
            subdir_start_x += max_file_w + padding
            
        # For subdirs, we arrange them in a row for now
        current_x = subdir_start_x
        for did in children_dirs:
            dnode = self.nodes[did]
            self._position_universe(did, tree, current_x, start_y)
            current_x += dnode['w'] + padding
