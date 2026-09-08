import networkx as nx

def save_network(G, filename, format='gml'):
    """
    Saves the bipartite network G (set of tuples (i,j,w)) to a specified file format.
    Supported formats: 'graphml', 'gexf', 'gpickle', etc.
    """
    # Convert edge set to a NetworkX graph
    B = nx.Graph()
    for s, t, w in G:
        B.add_edge(s, t, weight=w)

    if format == 'gml':
        nx.write_gml(B, filename + '.gml')
    elif format == 'gexf':
        nx.write_gexf(B, filename + '.gexf')
    elif format == 'graphml':
        nx.write_graphml(B, filename + '.graphml')
    else:
        raise ValueError("Unsupported format: {}".format(format))

def split_node_sets(G, focal=None):
    """
    Splits the nodes of a bipartite/tripartite HINA graph into its two node sets.

    The split is based on the ``bipartite`` node attribute written by
    ``hina.construction.get_bipartite`` / ``get_tripartite`` (and preserved by the
    web app and by the per-community projections in ``hina.mesoscale``), so it does
    not depend on the order in which nodes or edges were inserted into the graph.

    Parameters
    ----------
    G : networkx.Graph
        Graph whose nodes carry a ``bipartite`` attribute taking exactly two distinct values.
    focal : hashable, optional
        The ``bipartite`` value of the node set to return first. If ``None``, the value of the
        first node in ``G`` (node insertion order) is used, unless nodes carry
        ``tripartite=True``, in which case the non-tripartite (student) set is returned first.

    Returns
    -------
    (set, set)
        ``(set1, set2)`` with ``set1`` the focal node set.

    Raises
    ------
    ValueError
        If the ``bipartite`` attribute is missing on some node or does not take exactly two values.
    """
    attrs = nx.get_node_attributes(G, 'bipartite')
    if len(attrs) != G.number_of_nodes():
        missing = [n for n in G.nodes if n not in attrs]
        raise ValueError(
            "All nodes need a 'bipartite' attribute to identify the two node sets; "
            f"missing on {len(missing)} node(s), e.g. {missing[:3]}. Build the graph with "
            "hina.construction.get_bipartite/get_tripartite or set the attribute manually.")
    values = list(dict.fromkeys(attrs.values()))  # distinct values, insertion order
    if len(values) != 2:
        raise ValueError(f"'bipartite' attribute must take exactly two values, found {values}.")
    if focal is None:
        tri = nx.get_node_attributes(G, 'tripartite')
        non_tri = [v for v in values if not any(tri.get(n) for n, a in attrs.items() if a == v)]
        focal = non_tri[0] if len(non_tri) == 1 else values[0]
    elif focal not in values:
        raise ValueError(f"focal={focal!r} is not one of the 'bipartite' values {values}.")
    set1 = {n for n, a in attrs.items() if a == focal}
    set2 = set(G.nodes) - set1
    return set1, set2
