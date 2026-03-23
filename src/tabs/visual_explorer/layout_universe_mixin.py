class VisualExplorerLayoutUniverseMixin:
    def _calculate_layout_universe(self):
        """
        Layout that treats folders, files, and classes as containers.
        """
        if not self.nodes:
            return
        
        # 1. Build Roots (nodes with no parent in self.nodes)
        roots = []
        for nid, node in self.nodes.items():
            parent_id = node.get('parent')
            if not parent_id or parent_id not in self.nodes:
                roots.append(nid)

        # 2. Measure Sizes (Bottom-Up)
        for root_id in roots:
            self._measure_node(root_id)
        
        # 3. Position Nodes (Top-Down)
        current_x = 50
        current_y = 50
        padding = 50
        
        for root_id in roots:
            self._position_node(root_id, current_x, current_y)
            current_x += self.nodes[root_id]['w'] + padding
            
    def _measure_node(self, node_id):
        node = self.nodes[node_id]
        padding = 20
        header_height = 40
        
        if node['type'] == 'function':
            node['w'] = 140
            node['h'] = 35
            return

        children = node.get('children', [])
        if not children:
            node['w'] = 180
            node['h'] = 60
            return

        # Recursive Measure
        for cid in children:
            self._measure_node(cid)
            
        # Sort children to minimize crossing (simple heuristic)
        # Sort by dependency count or name
        children.sort(key=lambda x: self.nodes[x]['name'])
            
        # Layout strategy depends on type
        if node['type'] == 'dir':
            # Folders: Arrange all children (files and subdirs) in a horizontal row
            total_w = 0
            max_h = 0
            
            for cid in children:
                cnode = self.nodes[cid]
                total_w += cnode['w'] + padding
                if cnode['h'] > max_h: max_h = cnode['h']
            
            node['w'] = max(200, total_w + padding)
            node['h'] = header_height + max_h + (padding * 2)
            
        elif node['type'] == 'file' or node['type'] == 'class':
            # Stack children vertically
            max_w = 0
            total_h = 0
            for cid in children:
                cnode = self.nodes[cid]
                if cnode['w'] > max_w: max_w = cnode['w']
                total_h += cnode['h'] + 10 # Tighter padding for internal items
                
            node['w'] = max_w + (padding * 2)
            node['h'] = header_height + total_h + padding

    def _position_node(self, node_id, x, y):
        node = self.nodes[node_id]
        node['x'] = x
        node['y'] = y
        
        padding = 20
        header_height = 40
        
        children = node.get('children', [])
        if not children:
            return
            
        if node['type'] == 'dir':
            if getattr(self, 'layout_reverse', False):
                # Reverse: Children are to the LEFT of the folder container's logical start
                # This is tricky because the container's box already measured its width including children.
                # Let's arrange children from right-to-left.
                curr_x = x + node['w'] - padding
                curr_y = y + header_height + padding
                for cid in reversed(children):
                    cnode = self.nodes[cid]
                    curr_x -= cnode['w']
                    self._position_node(cid, curr_x, curr_y)
                    curr_x -= padding
            else:
                curr_x = x + padding
                curr_y = y + header_height + padding
                for cid in children:
                    self._position_node(cid, curr_x, curr_y)
                    curr_x += self.nodes[cid]['w'] + padding
                
        elif node['type'] == 'file' or node['type'] == 'class':
            # Vertical stacking remains vertical, but we could offset it if we wanted.
            curr_y = y + header_height + 10
            for cid in children:
                self._position_node(cid, x + padding, curr_y)
                curr_y += self.nodes[cid]['h'] + 10

    def _build_hierarchy_tree(self):
        # This might be used by treeview population
        tree = {nid: {'files': [], 'dirs': [], 'classes': [], 'functions': []} for nid in self.nodes}
        roots = []
        
        for nid, node in self.nodes.items():
            parent_id = node.get('parent')
            if not parent_id or parent_id not in self.nodes:
                roots.append(nid)
            else:
                ntype = node['type']
                if ntype == 'file': tree[parent_id]['files'].append(nid)
                elif ntype == 'dir': tree[parent_id]['dirs'].append(nid)
                elif ntype == 'class': tree[parent_id]['classes'].append(nid)
                elif ntype == 'function': tree[parent_id]['functions'].append(nid)
        
        return tree, roots