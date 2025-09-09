import base64
import io
import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.colors as mcolors
from hina.dyad import prune_edges
from hina.mesoscale import hina_communities
from hina.construction import get_bipartite, get_tripartite
from hina.individual import quantity, diversity

def parse_contents(encoded_contents: str, filename: str) -> pd.DataFrame:
    """
    Decode a base64-encoded file content and return a pandas DataFrame.
    Supports both CSV and XLSX formats.
    """
    decoded = base64.b64decode(encoded_contents)
    if filename.lower().endswith('.csv'):
        return pd.read_csv(io.StringIO(decoded.decode('utf-8')))
    elif filename.lower().endswith('.xlsx'):
        return pd.read_excel(io.BytesIO(decoded))
    else:
        raise ValueError("Unsupported file format. Please upload a .csv or .xlsx file")

def convert_numpy_scalars(obj):
    if isinstance(obj, dict):
        return {(k): convert_numpy_scalars(v) for k, v in obj.items()}
    # elif isinstance(obj, list):
    #     return [convert_numpy_scalars(i) for i in obj]
    elif isinstance(obj, np.generic):  
        return obj.item()
    else:
        return obj

def order_edge(u, v, df: pd.DataFrame, student_col: str, object_col: str, weight: int):
    """
    Given two node identifiers u and v, force the edge tuple to have the node 
    from student_col always first and the node from object_col always second. 
    If both nodes belong to the same attribute, they are sorted lexicographically.
    
    Parameters:
    -----------
    u, v : any
        Node identifiers from the graph
    df : pandas.DataFrame
        The input DataFrame containing the data
    student_col : str
        The column name in the DataFrame representing student nodes
    object_col : str
        The column name in the DataFrame representing object nodes
    weight : int
        The weight of the edge
        
    Returns:
    --------
    tuple
        (student_node, object_node, weight) or sorted nodes with weight if ambiguous
    """
    u_str = str(u)
    v_str = str(v)
    student_nodes = set(df[student_col].astype(str).values)
    object_nodes = set(df[object_col].astype(str).values)
    
    if u_str in student_nodes and v_str in object_nodes:
        return (u_str, v_str, weight)
    elif u_str in object_nodes and v_str in student_nodes:
        return (v_str, u_str, weight)
    else:
        # If both nodes are in the same attribute or ambiguous, sort lexicographically.
        return tuple(sorted([u_str, v_str])) + (weight,)
        
def construct_network(df: pd.DataFrame, group_col: str, student_col: str, object1_col: str, object2_col: str, attr_col: str, pruning):
    # Create the bipartite/tripartite graph
    is_tripartite = object2_col is not None and object2_col not in ['none', 'null', 'undefined', '']
    if is_tripartite:
        G = get_tripartite(df, student_col, object1_col, object2_col, group_col)
        print("\n=== Tripartite Graph Nodes ===")
        print("\n=== Tripartite Graph Edges ===")
    else:
        G = get_bipartite(df, student_col, object1_col, attr_col, group_col)
        print("\n=== Bipartite Graph Nodes ===")
        print("\n=== Bipartite Graph Edges ===")
        
    G_str = nx.Graph()
    for node, attrs in G.nodes(data=True):
        node_str = str(node)
        G_str.add_node(node_str, **attrs)
    for u, v, data in G.edges(data=True):
        G_str.add_edge(str(u), str(v), **data)
    G = G_str        
    G_edges_ordered = [order_edge(u, v, df, student_col, object1_col, int(w.get('weight', 1))) for u, v, w in G.edges(data=True)]

    # Node type and color mapping
    node_types = {}
    node_colors = {}
    student_nodes = set(df[student_col].astype(str).values)
    object_nodes = set()
    
    if is_tripartite:
        for node_str in G.nodes():
            if "**" in str(node_str):
                object_nodes.add(str(node_str))
    else:
        object_nodes = set(df[object1_col].astype(str).values)
    
    # Assign node types and colors
    for node in G.nodes():
        node_str = str(node)
        if is_tripartite and "**" in node_str:
            parts = node_str.split("**")
            if len(parts) == 2:
                obj1_val, obj2_val = parts
                if obj1_val in df[object1_col].astype(str).values and obj2_val in df[object2_col].astype(str).values:
                    node_types[node_str] = 'object1_object2'
                    node_colors[node_str] = 'green'
                    continue
        if node_str in df[student_col].astype(str).values:
            node_types[node_str] = 'student'
            node_colors[node_str] = 'grey'
        elif node_str in df[object1_col].astype(str).values:
            node_types[node_str] = 'object1'
            node_colors[node_str] = 'blue'
        else:
            node_types[node_str] = 'unknown'
            node_colors[node_str] = 'black'

    # Prune edges
    if pruning != "none":
        if isinstance(pruning, dict):
            significant_edges_result = prune_edges(G, **pruning)
        else:
            significant_edges_result = prune_edges(G)
        
        # Extract significant edges
        if isinstance(significant_edges_result, dict) and "significant edges" in significant_edges_result:
            significant_edges = significant_edges_result["significant edges"]
        else:
            significant_edges = significant_edges_result or set()
        
        nx_G = nx.Graph()
        for node, attrs in G.nodes(data=True):
            node_str = str(node)
            new_attrs = dict(attrs)
            if 'bipartite' in new_attrs:
                new_attrs['bipartite'] = str(new_attrs['bipartite'])                
            if node_str in node_types:
                new_attrs['type'] = node_types[node_str]
                new_attrs['color'] = node_colors[node_str]
            nx_G.add_node(node_str, **new_attrs)
        
        # Order edges 
        ordered_edges = []
        for u, v, w in significant_edges:
            u_str = str(u)
            v_str = str(v)
            
            if u_str in student_nodes and v_str in object_nodes:
                ordered_edges.append((u_str, v_str, w))
            else:
                ordered_edges.append((v_str, u_str, w))
        
        # Add edges to the graph
        for u, v, w in ordered_edges:
            nx_G.add_edge(u, v, weight=w)
        G_edges_ordered = ordered_edges

    else:
        # No pruning
        nx_G = nx.Graph()        
        for node, attrs in G.nodes(data=True):
            node_str = str(node)
            new_attrs = dict(attrs)
            if 'bipartite' in new_attrs:
                new_attrs['bipartite'] = str(new_attrs['bipartite'])                
            if node_str in node_types:
                new_attrs['type'] = node_types[node_str]
                new_attrs['color'] = node_colors[node_str]
                
            nx_G.add_node(node_str, **new_attrs)

        ordered_edges = []
        for edge in G_edges_ordered:
            u_str = str(edge[0])
            v_str = str(edge[1])
            weight = edge[2]
            
            if u_str in student_nodes and (v_str in object_nodes or "**" in v_str):
                ordered_edges.append((u_str, v_str, weight))
            elif v_str in student_nodes and (u_str in object_nodes or "**" in u_str):
                ordered_edges.append((v_str, u_str, weight))
            else:
                ordered_edges.append(edge)
        G_edges_ordered = ordered_edges
        
        for edge in G_edges_ordered:
            u_str = str(edge[0])
            v_str = str(edge[1])
            nx_G.add_edge(u_str, v_str, weight=int(edge[2]))
    
    for node in list(nx_G.nodes()):
        if nx_G.degree(node) == 0:
            nx_G.remove_node(node)
    
    for u, v, d in nx_G.edges(data=True):
        d['label'] = str(d.get('weight', ''))
    
    return nx_G, G_edges_ordered

def build_hina_network(df: pd.DataFrame, group_col: str, group: str, student_col: str, object1_col: str, object2_col: str, attr_col: str, pruning, layout: str):
    """
    Build a NetworkX graph for the HINA network, supporting both bipartite and tripartite networks.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The input DataFrame containing the data to construct the bipartite graph.
    group_col : str
        The column name in the DataFrame representing group information for student nodes.
    group : str
        The specific group to filter by, or 'All' to include all groups.
    student_col : str
        The column name in the DataFrame representing student nodes.
    object1_col : str
        The column name in the DataFrame representing the studied object nodes.
    attr_col : str
        The column name in the DataFrame representing attributes for object nodes.
    pruning : str or dict
        Controls edge pruning strategy. "none" for no pruning, or a dictionary with 
        parameters for the prune_edges function.
    layout : str
        Layout for node positioning: "bipartite", "spring", or "circular".
    
    Returns:
    --------
    tuple
        (nx_G, pos, G_edges_ordered) - The network graph, node positions, and edge list.
    """
    # Filter by group 
    if group != 'All' and group_col in df.columns:
        df = df[df[group_col].astype(str) == str(group)]

    nx_G, G_edges_ordered = construct_network(df, group_col, student_col, object1_col, object2_col, attr_col, pruning)
    # print("G_edges_ordered_hina", nx_G.edges)
    # Set the layout
    if layout == 'bipartite':
        student_nodes = {n for n, d in nx_G.nodes(data=True) if d['type'] == 'student'}
        if not nx.is_bipartite(nx_G):
            raise ValueError("The graph is not bipartite; check the input data.")
        pos = nx.bipartite_layout(nx_G, student_nodes, align='vertical', scale=1.5, aspect_ratio=0.7)
    elif layout == 'spring':
        pos = nx.spring_layout(nx_G, k=0.2)
    elif layout == 'circular':
        pos = nx.circular_layout(nx_G)
    else:
        raise ValueError(f"Unsupported layout: {layout}")
    
    return nx_G, pos, G_edges_ordered

def cy_elements_from_graph(G: nx.Graph, pos: dict):
    """
    Convert a NetworkX graph and its layout positions into Cytoscape elements.
    Each node element now includes its color in its data.
    """
    elements = []
    for node, data in G.nodes(data=True):
        node_str = str(node)
        # print('node_str_pos', node_str, pos[node])
        x = pos[node][0] * 400 + 300
        y = pos[node][1] * 400 + 300
        elements.append({
            'data': {
                'id': node_str,
                'label': node_str,
                'color': data.get('color', 'black'),
				'type': data.get('type', '')
            },
            'position': {'x': x, 'y': y},
        })
    for u, v, d in G.edges(data=True):
        elements.append({
            'data': {
                'source': str(u),
                'target': str(v),
                'weight': d.get('weight', 0),
                'label': d.get('label', str(d.get('weight', ''))),
				'type': data.get('type', '')
            }
        })
    return elements

def build_clustered_network(df: pd.DataFrame, group_col: str, student_col: str, object1_col: str, object2_col: str, attr_col: str, pruning, layout: str, number_cluster=None):
    """
    Build a clustered network using get_bipartite/get_tripartite and hina_communities.
    
    Colors:
      - Nodes in student_col are colored based on their community using TABLEAU_COLORS.
      - Nodes in object1_col are fixed as blue.
      - Nodes in object2_col are fixed as green.
    """
    nx_G, G_edges_ordered = construct_network(df, group_col, student_col, object1_col, object2_col, attr_col, pruning)
    # print("G_edges_ordered_cluster", nx_G.edges)
    if number_cluster not in (None, "", "none"):
        try:
            number_cluster = int(number_cluster)
        except ValueError:
            number_cluster = None
    else:
        number_cluster = None
    
    # Run community detection (clustering)
    cluster_result = hina_communities(nx_G, fix_B=number_cluster)
    # print('cluster_result', cluster_result)
    cluster_labels = cluster_result['node communities']
    compression_ratio = cluster_result['community quality (compression ratio)']
    
    object_object_graphs = {}
    if 'object-object graphs for each community' in cluster_result:
        object_object_graphs = cluster_result['object-object graphs for each community']
        # print(f"Found {len(object_object_graphs)} object-object graphs for communities")
    
    for node in nx_G.nodes():
        nx_G.nodes[node]['cluster'] = str(cluster_labels.get(str(node), "-1"))
    
    # Build color mapping for student nodes based on community labels.
    communities = sorted({nx_G.nodes[node]['cluster'] 
                          for node in nx_G.nodes() 
                          if nx_G.nodes[node]['type'] == 'student'})
    comm_colors = dict(zip(communities, list(mcolors.TABLEAU_COLORS.values())[:len(communities)]))

    # Apply community colors to student nodes
    for node in nx_G.nodes():
        if nx_G.nodes[node]['type'] == 'student':
            comm = nx_G.nodes[node]['cluster']
            if comm in comm_colors:
                nx_G.nodes[node]['color'] = comm_colors[comm]
                nx_G.nodes[node]['original_type'] = 'student'
    
    # Check if tripartite graph
    is_tripartite = object2_col is not None and object2_col not in ['none', 'null', 'undefined', '']
    student_nodes = set(df[student_col].astype(str).values)
    object1_values = df[object1_col].fillna('NA').astype(str).values
    object1_nodes = set(object1_values)
        
    # Create a set of combined nodes for tripartite case
    combined_nodes = set()
    if is_tripartite:
        for node in nx_G.nodes():
            if '**' in str(node) or nx_G.nodes[node].get('type') == 'object1_object2':
                combined_nodes.add(str(node))

    offset = np.random.rand() * np.pi
    radius = 1  # radius of the circle 20/3 * radius/noise_scale
    noise_scale = 0.16 
    
    # For nodes in student node: position based on community label.
    set1_pos = {}
    for node in student_nodes.intersection(set(nx_G.nodes())):
        comm = nx_G.nodes[node].get('cluster', "-1")
        comm_index = communities.index(comm) if comm in communities else 0
        angle = 2 * np.pi * comm_index / len(communities) + offset
        x = radius * np.cos(angle) + (2 * np.random.rand() - 1) * noise_scale
        y = radius * np.sin(angle) + (2 * np.random.rand() - 1) * noise_scale
        set1_pos[node] = (x, y)
    
    # For nodes in object1 node: arrange in a circle (half radius)
    set2_pos = {}
    obj_nodes = object1_nodes.intersection(set(nx_G.nodes()))
    obj_list = sorted(list(obj_nodes))
    num_obj = len(obj_list)
    for i, node in enumerate(obj_list):
        angle = 2 * np.pi * i / num_obj + offset
        x = 0.5 * radius * np.cos(angle)
        y = 0.5 * radius * np.sin(angle)
        set2_pos[node] = (x, y)
    
    # For combined nodes in tripartite graph: arrange in a circle (0.7 radius)
    set3_pos = {}
    if is_tripartite:
        combined_list = sorted(list(combined_nodes))
        num_combined = len(combined_list)
        for i, node in enumerate(combined_list):
            angle = 2 * np.pi * i / num_combined + offset + np.pi/num_combined 
            x = 0.7 * radius * np.cos(angle)
            y = 0.7 * radius * np.sin(angle)
            set3_pos[node] = (x, y)
    
    pos_custom = {**set1_pos, **set2_pos, **set3_pos}
    
    if layout == 'bipartite':
        pos = pos_custom
    elif layout == 'spring':
        pos = nx.spring_layout(nx_G, k=0.2)
    elif layout == 'circular':
        pos = nx.circular_layout(nx_G)
    else:
        pos = pos_custom
    
    return nx_G, pos, G_edges_ordered, cluster_labels, compression_ratio, object_object_graphs

