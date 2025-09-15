import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from hina.dyad import prune_edges
from hina.mesoscale import hina_communities

def plot_hina(B, layout='bipartite', group_name = [None, None], pruning_kwargs=None, NetworkX_kwargs=None, weight_scaler = 1., show=True):
    """
    Visualizes a bipartite network with customizable layout, node grouping, and edge pruning.

    This function creates a visualization of a bipartite graph `B` using a specified layout. It supports
    pruning edges based on statistical significance, grouping nodes by a selected group information, and customizing
    the appearance of the graph using NetworkX visualization parameters.

    Parameters:
    -----------
    B : networkx.Graph
        A bipartite graph to visualize. Nodes must have a 'bipartite' attribute indicating their partition.
        If using HINA to analyze tripartite networks, it is recommended to visualize the object-object graphs for 
        each community after detecting communities with hina_communities(). These projected graphs represent 
        relationships between objects within each community and provide additional insights into the 
        structure and interactions of the network.
    layout : str, optional
        The layout to use for node positioning. Supported layouts are:
        - 'bipartite': Nodes are positioned in two vertical columns (default).
        - 'spring': Force-directed layout for a visually appealing arrangement.
        - 'circular': Nodes are arranged in a circle.
    group_name : list, optional
        AA list of two elements specifying the node attribute and its corresponding value to filter nodes 
        for visualization. The first element is the name of the node attribute (e.g., 'group'), 
        which corresponds to a column in the input dataframe. The second element is the specific value of the 
        attribute (e.g., 'A'), used to filter nodes. Only nodes with this attribute value will be included 
        in the visualization. For example, ['group', 'A'] will include only nodes where the 'group' attribute is 'A'.
        Default is `[None, None]`, which includes all nodes.
    pruning_kwargs : dict, optional
        A dictionary of parameters for pruning edges based on statistical significance. 
        If provided, the prune_edges function is called to remove edges that are not 
        statistically significant before visualization.For example, {'fix_deg': 'students'} 
        specifies that the degrees of the 'students' node set should be fixed during pruning. 
        Default is `None`, which skips pruning.
    NetworkX_kwargs : dict, optional
        Additional keyword arguments for customizing the NetworkX visualization (e.g., node size, edge color).
        Default is `None`.
    weight_scaler : float, optional
        Changes thickness of edge weights.
        Default value is 1.

    Returns:
    --------
        Displays a plot of the bipartite network.
    """
    if NetworkX_kwargs is None:
        NetworkX_kwargs = {}

    # Prune edges if pruning_kwargs is provided
    if pruning_kwargs is not None:
        B = prune_edges(B, **pruning_kwargs)['pruned network']

    if group_name is not None:
        
        G_sub = nx.Graph()
        u_nodes = [i for i, j in B.nodes(data=True) if j.get(group_name[0]) == group_name[1]]
        for u_node in u_nodes:
            G_sub.add_node(u_node, **B.nodes[u_node])
        v_nodes = set()
        for u_node in u_nodes:
            for v_node in B.neighbors(u_node):
                v_nodes.add(v_node)
                G_sub.add_node(v_node, **B.nodes[v_node])
        for u_node in u_nodes:
            for v_node in B.neighbors(u_node):
                if B.has_edge(u_node, v_node):
                    G_sub.add_edge(u_node, v_node, **B.edges[u_node, v_node])
        B = G_sub
        
    v = set()
    bipartite_top = [x for x in [data['bipartite'] for n, data in B.nodes(data=True)] \
                    if not (x in v or v.add(x))][0]

    # Create a color dictionary
    color_dict = {n: 'red' if data['bipartite'] == bipartite_top else 'blue'
                  for n, data in B.nodes(data=True)}

    # Get the list of nodes in the top partition for bipartite layout
    top_nodes = [n for n, data in B.nodes(data=True) if data['bipartite'] == bipartite_top]

  

    # Set the layout
    if layout == 'bipartite':
        pos = nx.bipartite_layout(B, top_nodes, align='vertical', scale=2, aspect_ratio=4)
    elif layout == 'spring':
        pos = nx.spring_layout(B, k=0.2)
    elif layout == 'circular':
        pos = nx.circular_layout(B)
    else:
        raise ValueError(f"Unsupported layout: {layout}")

    # Calculate label offset
    max_y = max(abs(y) for _, y in pos.values())
    label_offset = max_y * 0.03

    # Set node colors and edge widths
    node_colors = [color_dict[n] for n in B.nodes()]
    edge_widths = [d.get('weight', 1) * weight_scaler for _, _, d in B.edges(data=True)]  # Default weight = 1 if not specify weight_scaler 

    # Plot the graph
    plt.figure(figsize=(12, 12))
    
    draw_kwargs = {
    'with_labels': False,
    'node_color': node_colors,  
    'width': edge_widths,     
    'node_size': 200,     
    **NetworkX_kwargs          
    }
    
    nx.draw(B, pos, **draw_kwargs)
    
    # Add labels
    for node, (x, y) in pos.items():
        label = str(node)
        plt.text(
            x, y + label_offset,
            label,
            fontsize=9,
            ha='center',
            va='center',
            color='black'
        )

    plt.title("HINA Network Visualization")
    if show:
        plt.show()



def plot_hina_projection (B, target_nodeset, layout='circle', group_name = [None, None],\
                          pruning_kwargs=None, NetworkX_kwargs=None):

    """
    Visualizes a projected one-mode network based on the defined nodeset in a B with circular layout, node grouping, and edge pruning.

    This function creates a visualization of a projected bipartite graph `B` based on the designated nodeset using a circular layout. The edge weights are convereted in the 
    projected network. It supports the projection of a pruned bipartite network B based on statistical significance, projected a certain group of nodes, and customizing
    the appearance of the graph using NetworkX visualization parameters.

    Parameters:
    -----------
    B : networkx.Graph
        Nodes must have a 'bipartite' attribute indicating their partition.
        If using HINA to analyze tripartite networks, it is recommended to visualize the object-object graphs for 
        each community after detecting communities with hina_communities(). These projected graphs represent 
        relationships between objects within each community and provide additional insights into the 
        structure and interactions of the network.
    nodeset: the desginated nodeset in B, normally is the same as the column name while constructing the B. e.g. 'coded behaviors'. 
    This is in the value of the bipartite node attribute ['bipartite']
    layout : str, optional
        The layout to use for node positioning. Supported layouts are:
        - 'circular': Nodes are arranged in a circle (default).
        - 'spring': Force-directed layout for a visually appealing arrangement.
    group_name : list, optional
        AA list of two elements specifying the node attribute and its corresponding value to filter nodes 
        for visualization. The first element is the name of the node attribute (e.g., 'group'), 
        which corresponds to a column in the input dataframe. The second element is the specific value of the 
        attribute (e.g., 'A'), used to filter nodes. Only nodes with this attribute value will be included 
        in the visualization. For example, ['group', 'A'] will include only nodes where the 'group' attribute is 'A'.
        Default is `[None, None]`, which includes all nodes.
    pruning_kwargs : dict, optional
        A dictionary of parameters for pruning edges based on statistical significance. 
        If provided, the prune_edges function is called to remove edges that are not 
        statistically significant before visualization. For example, {'fix_deg': 'students'} 
        specifies that the degrees of the 'students' node set should be fixed during pruning. 
        Default is `None`, which skips pruning.
    NetworkX_kwargs : dict, optional
        Additional keyword arguments for customizing the NetworkX visualization (e.g., node size, edge color).
        Default is `None`.
        
        Additional keyword arguments to customize NetworkX visualization. Overrides default 
        styling. Common options include:
        - 'node_size': int - Size of nodes (default: 300)
        - 'node_color': str - Node fill color (default: '#2E86AB' - blue)
        - 'edgecolors': str - Node border color (default: '#A23B72' - purple)  
        - 'font_size': int - Label font size (default: 8)
        - 'with_labels': bool - Whether to show node labels (default: True)
        - 'edge_color': str - Edge color (default: 'gray')
        - 'alpha': float - Transparency (default: 0.7)

    Returns:
    --------
        Displays a plot of a projected one-mode network based on the defined nodeset in a B with circular layout.
    """
    if NetworkX_kwargs is None:
        NetworkX_kwargs = {}

    # Prune edges if pruning_kwargs is provided
    if pruning_kwargs is not None:
        B = prune_edges(B, **pruning_kwargs)['pruned network']

    if group_name is not None:
        
        G_sub = nx.Graph()
        u_nodes = [i for i, j in B.nodes(data=True) if j.get(group_name[0]) == group_name[1]]
        for u_node in u_nodes:
            G_sub.add_node(u_node, **B.nodes[u_node])
        v_nodes = set()
        for u_node in u_nodes:
            for v_node in B.neighbors(u_node):
                v_nodes.add(v_node)
                G_sub.add_node(v_node, **B.nodes[v_node])
        for u_node in u_nodes:
            for v_node in B.neighbors(u_node):
                if B.has_edge(u_node, v_node):
                    G_sub.add_edge(u_node, v_node, **B.edges[u_node, v_node])
        B = G_sub

    def create_projection(graph, nodeset):

        projection = nx.Graph()
        nodes_to_project = [n for n, data in graph.nodes(data=True) 
                           if data.get('bipartite') == nodeset]
        
        projection.add_nodes_from(nodes_to_project)
        
        # Add edges based on common neighbors
        for i, node1 in enumerate(nodes_to_project):
            for node2 in nodes_to_project[i+1:]:
                neighbors1 = set(graph.neighbors(node1))
                neighbors2 = set(graph.neighbors(node2))

                ###old method: count common neighbors to get projection weight
                # common_neighbors = neighbors1.intersection(neighbors2)
                
                # if common_neighbors:
                #     weight = len(common_neighbors)
                #     projection.add_edge(node1, node2, weight=weight)

                ####new method: cosine similarity among corresponding rows of weighted adjacency matrix
                total1,total2 = 0,0
                for n in neighbors1: total1 += graph[node1][n]['weight']
                for n in neighbors2: total2 += graph[node2][n]['weight']
        
                sim = 0
                for n in neighbors1:
                     if n in neighbors2:
                         sim += (graph[node1][n]['weight']/total1)*(graph[node2][n]['weight']/total2)
                projection.add_edge(node1, node2, weight=sim)
                
        return projection

    # Create the projection
    G_projected = create_projection(B, target_nodeset)

    plt.figure(figsize=(8, 8))
    
    if layout == 'circle':
        pos = nx.circular_layout(G_projected)
    elif layout == 'spring':
        pos = nx.spring_layout(G_projected, k=1/np.sqrt(len(G_projected.nodes())), iterations=50)

    # Set default visualization parameters
    default_kwargs = {
        'node_size': 300,
        'node_color': '#2E86AB',
        'edgecolors': '#A23B72',
        'linewidths': 0.5,
        'width': 1,
        'edge_color': 'gray',
        'alpha': 0.7,
        'with_labels': True,
        'font_size': 8
    }
    
    # Update with user-provided kwargs
    default_kwargs.update(NetworkX_kwargs)

    # Set node colors and edge widths
    nx.draw_networkx_nodes(G_projected, pos, 
                          node_size=default_kwargs['node_size'],
                          node_color=default_kwargs['node_color'],
                          edgecolors=default_kwargs['edgecolors'],
                          linewidths=default_kwargs['linewidths'])

    # Draw edges with weights
    edge_widths = [d.get('weight', 1) * weight_scaler for u, v, d in G_projected.edges(data=True)]
    nx.draw_networkx_edges(G_projected, pos, 
                          width=edge_widths,
                          edge_color=default_kwargs['edge_color'],
                          alpha=default_kwargs['alpha'])

    # Draw labels
    if default_kwargs['with_labels']:
        nx.draw_networkx_labels(G_projected, pos, 
                               font_size=default_kwargs['font_size'])

    plt.title(f"HINA Network Projection - {target_nodeset} Nodeset\n", fontsize=14, pad=20)
    plt.axis('off')
    plt.margins(0.15)  
    plt.tight_layout()
    plt.show()


def plot_bipartite_clusters(G, noise_scale=3, radius=20., encode_labels=False,
                           node_labels=True, edge_labels=False,
                           scale_nodes_by_degree=False, node_scale=2000.,
                           node_kwargs={'edgecolors': 'black'}, edge_kwargs={'edge_color': 'black'},  weight_scaler = 1., show=True):
    """
    Visualizes a bipartite graph with nodes grouped into communities, highlighting the community structure.

    This function plots a bipartite graph `G` with nodes arranged in a circular layout. Nodes from the first set
    are positioned around the circumference, grouped by their community labels, while nodes from the second set
    are positioned inside the circle. The visualization supports customizing node sizes, colors, and labels.

    Parameters:
    -----------
    G : networkx.Graph
        A bipartite graph with weighted edges. Nodes must belong to one of two sets (e.g., 'set1' and 'set2').
    noise_scale : float, optional
        Controls the dispersion of nodes in the first set around their community centroids. Higher values increase
        randomness in node positions. Default is 3.
    radius : float, optional
        Controls the radius of the circle on which community centers are placed. Default is 20.
    encode_labels : bool, optional
        If True, encodes node labels as unique integers and prints the encoding map. Default is False.
    node_labels : bool, optional
        If True, displays labels for all nodes. If False, only displays labels for nodes in the second set.
        Default is True.
    edge_labels : bool, optional
        If True, displays edge weights as labels. Default is False.
    scale_nodes_by_degree : bool, optional
        If True, scales node sizes proportionally to their weighted degree. Default is False.
    node_scale : float, optional
        Controls the average size of nodes. Default is 2000.
    node_kwargs : dict, optional
        Additional keyword arguments for customizing node appearance in `nx.draw_networkx_nodes`.
        Default is `{'edgecolors': 'black'}`.
    edge_kwargs : dict, optional
        Additional keyword arguments for customizing edge appearance in `nx.draw_networkx_edges`.
        Default is `{'edge_color': 'black'}`.
     weight_scaler : float, optional
        Changes thickness of edge weights.
        Default value is 1.

    Returns:
    --------
    None
        Displays a plot of the bipartite graph with nodes grouped by communities.
    """

    community_labels = hina_communities(G)['node communities']
    G_info = set([(i, j, w['weight']) for i, j, w in G.edges(data=True)])
    set1 = set([str(e[0]) for e in G_info])
    set2 = set([str(e[1]) for e in G_info])

    offset = np.random.rand() * np.pi

    B = len(set(community_labels.values()))
    comm2ind = dict(zip(list(set(community_labels.values())), range(B)))

    set1_pos = {}
    for node in set1:
        c = comm2ind[community_labels[node]]
        angle = 2 * np.pi * c / B + offset
        x = radius * np.cos(angle) + (2. * np.random.rand() - 1.) * noise_scale
        y = radius * np.sin(angle) + (2. * np.random.rand() - 1.) * noise_scale
        set1_pos[node] = (x, y)

    set2_pos = {}
    num_s2 = len(set2)
    for c, node in enumerate(set2):
        angle = 2 * np.pi * c / num_s2 + offset
        x = 0.5 * radius * np.cos(angle)
        y = 0.5 * radius * np.sin(angle)
        set2_pos[node] = (x, y)

    pos = {**set1_pos, **set2_pos}

    comm_colors = dict(zip(list(set(community_labels.values())), list(mcolors.TABLEAU_COLORS.values())))
    color_dict = {node: comm_colors[community_labels[node]] for node in set1} | {node: 'Gray' for node in set2}
    node_colors = {node: color_dict[node] for node in G.nodes()}

    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    max_weight = max(edge_weights)
    edge_widths = [weight / max_weight * 5 for weight in edge_weights]

    weighted_degrees = {node: sum(weight for _, _, weight in G.edges(node, data='weight'))
                        for node in G.nodes()}
    if scale_nodes_by_degree:
        avg = np.mean(list(weighted_degrees.values()))
        node_sizes = {node: weighted_degrees[node] / avg * node_scale for node in G.nodes()}
    else:
        node_sizes = {node: node_scale for node in G.nodes()}

    plt.figure(figsize=(20, 20))

    nodes = [str(n) for n in set1] + [str(n) for n in set2]
    if encode_labels:
        codes = [i for i in range(len(nodes))]
        labelmap = dict(zip(nodes, codes))
        for node in set1:
            print('Original Label (Set 1):', node, '| Encoded Label:', labelmap[node])
        for node in set2:
            print('Original Label (Set 2):', node, '| Encoded Label:', labelmap[node])
    else:
        labelmap = dict(zip(nodes, nodes))

    shapes = {node: 'o' for node in set1} | {node: '^' for node in set2}
    for node, shape in shapes.items():
        nx.draw_networkx_nodes(G, pos, nodelist=[node], node_shape=shape,
                              node_color=node_colors[node], node_size=node_sizes[node], **node_kwargs)

    nx.draw_networkx_edges(G, pos, width=edge_widths, **edge_kwargs)

    label_options = {'bbox': {'facecolor': 'white', 'alpha': 1, 'edgecolor': 'black'}}
    if node_labels:
        # Show all node labels (both set1 and set2)
        nx.draw_networkx_labels(G, pos, labels=labelmap, **label_options)
    else:
        # Show only set2 labels
        set2_labelmap = {node: labelmap[node] for node in set2}
        nx.draw_networkx_labels(G, pos, labels=set2_labelmap, **label_options)

    if edge_labels:
        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    if show:
        plt.show()
