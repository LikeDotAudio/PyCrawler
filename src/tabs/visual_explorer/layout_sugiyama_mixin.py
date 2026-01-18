import math

class VisualExplorerLayoutSugiyamaMixin:
    def _calculate_layout_sugiyama(self):
        if not self.nodes: return
        
        self._compute_pagerank()
        
        adj = {u: [] for u in self.nodes}
        for u, v, etype in self.edges:
             # Treat 'hierarchy' edges as structural backbone (stronger)
             if u in adj: adj[u].append(v)
        
        safe_edges = self._remove_cycles(adj)
        layers = self._assign_layers(safe_edges)
        ordered_layers = self._minimize_crossings(layers, safe_edges)
        
        # Spacing
        layer_height = 300 
        node_spacing_x = 280 
        start_y = 200
        start_x = 200
        
        max_layer_width = 0
        for layer in ordered_layers.values():
            if len(layer) > max_layer_width: max_layer_width = len(layer)
            
        canvas_center_x = (max_layer_width * node_spacing_x) / 2 + start_x
        
        for rank, nodes_in_layer in ordered_layers.items():
            y = start_y + (rank * layer_height)
            
            layer_width = len(nodes_in_layer) * node_spacing_x
            x_offset = canvas_center_x - (layer_width / 2)
            
            for i, node_id in enumerate(nodes_in_layer):
                node = self.nodes[node_id]
                node['rank'] = rank
                node['order'] = i
                
                # Apply PageRank to Size (Only for files)
                if node['type'] == 'file':
                    pr_scale = 1 + (node['pagerank'] * 12) 
                    if pr_scale > 4: pr_scale = 4
                    node['w'] = 200 * math.sqrt(pr_scale)
                    node['h'] = (80 + (len(node['contents']) * 15)) * math.sqrt(pr_scale)
                
                node['x'] = x_offset + (i * node_spacing_x)
                node['y'] = y

    def _compute_pagerank(self, damping=0.85, iterations=20):
        in_links = {u: [] for u in self.nodes}
        out_degree = {u: 0 for u in self.nodes}
        
        for u, v, _ in self.edges:
            if v in in_links: in_links[v].append(u)
            if u in out_degree: out_degree[u] += 1
            
        N = len(self.nodes)
        pagerank = {u: 1.0 / N for u in self.nodes}
        
        for _ in range(iterations):
            new_pagerank = {}
            for u in self.nodes:
                rank_sum = 0
                for incoming in in_links[u]:
                    if out_degree[incoming] > 0:
                        rank_sum += pagerank[incoming] / out_degree[incoming]
                
                new_pagerank[u] = (1 - damping) / N + damping * rank_sum
            pagerank = new_pagerank
            
        max_pr = max(pagerank.values()) if pagerank else 1
        for u, val in pagerank.items():
            self.nodes[u]['pagerank'] = val / max_pr

    def _remove_cycles(self, adj):
        visited = set()
        recursion_stack = set()
        safe_edges = []
        
        def dfs(u):
            visited.add(u)
            recursion_stack.add(u)
            
            if u in adj:
                for v in adj[u]:
                    if v not in visited:
                        safe_edges.append((u, v))
                        dfs(v)
                    elif v in recursion_stack:
                        pass 
                    else:
                        safe_edges.append((u, v))
            
            recursion_stack.remove(u)

        for node in self.nodes:
            if node not in visited:
                dfs(node)
                
        return safe_edges

    def _assign_layers(self, safe_edges):
        in_degree = {u: 0 for u in self.nodes}
        for u, v in safe_edges:
            in_degree[v] += 1
            
        queue = [u for u in self.nodes if in_degree[u] == 0]
        rank = {u: 0 for u in self.nodes}
        
        processed_count = 0
        while queue:
            u = queue.pop(0)
            processed_count += 1
            
            neighbors = [v for src, v in safe_edges if src == u]
            
            for v in neighbors:
                rank[v] = max(rank[v], rank[u] + 1)
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
        
        layers = {}
        for u, r in rank.items():
            if r not in layers: layers[r] = []
            layers[r].append(u)
            
        return layers

    def _minimize_crossings(self, layers, safe_edges):
        max_rank = max(layers.keys()) if layers else 0
        
        down_adj = {u: [] for u in self.nodes} 
        up_adj = {v: [] for v in self.nodes}
        for u, v in safe_edges:
            down_adj[u].append(v)
            up_adj[v].append(u)
            
        for _ in range(4):
            for r in range(1, max_rank + 1):
                if r not in layers: continue
                current_nodes = layers[r]
                
                def barycenter(n):
                    parents = up_adj[n]
                    if not parents: return 0
                    parent_indices = []
                    prev_layer = layers.get(r-1, [])
                    for p in parents:
                        if p in prev_layer:
                            parent_indices.append(prev_layer.index(p))
                    if not parent_indices: return 0
                    return sum(parent_indices) / len(parent_indices)
                
                current_nodes.sort(key=barycenter)
                layers[r] = current_nodes
                
            for r in range(max_rank - 1, -1, -1):
                if r not in layers: continue
                current_nodes = layers[r]
                
                def barycenter_down(n):
                    children = down_adj[n]
                    if not children: return 0
                    child_indices = []
                    next_layer = layers.get(r+1, [])
                    for c in children:
                        if c in next_layer:
                            child_indices.append(next_layer.index(c))
                    if not child_indices: return 0
                    return sum(child_indices) / len(child_indices)
                
                current_nodes.sort(key=barycenter_down)
                layers[r] = current_nodes
                
        return layers
