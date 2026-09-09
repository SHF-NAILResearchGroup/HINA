import scipy.stats as stats
import networkx as nx 
def prune_edges(B,fix_deg='None',alpha=0.05):
    """
    Prunes edges in a bipartite graph to retain only those that are statistically significant under a null model.

    This function identifies and retains edges whose weights are statistically significant based on a binomial distribution
    under a null model. The null model can either fix the degrees of a specified node set (e.g., 'student', 'task') or assume
    no fixed degrees. The significance level is controlled by the `alpha` parameter.

    Parameters:
    -----------
    B : networkx.Graph
        A bipartite graph with weighted edges. Nodes are expected to have a 'bipartite' attribute indicating their partition.
    fix_deg : str, optional
        Specifies the node set whose degrees are fixed in the null model.  For example, if analyzing student 
        involvement in tasks B(student, tasks), you might fix the degrees of the 'student' node set. 
        This ensures the null model preserves the degree distribution of the specified node set.
        If 'None', no degrees are fixed, and the null model assumes random edge weights. Default is 'None'.
    alpha : float, optional
        The significance level for determining statistical significance. Edges with weights below the threshold determined
        by this value are pruned. Default is 0.05.

    Returns:
    --------
    dict
        A dictionary containing two keys:
        - 'pruned network': A networkx.Graph object representing the pruned graph with only statistically significant edges.
        - 'significant edges': A set of tuples representing the statistically significant edges, where each tuple is of the
          form (node1, node2, weight).
    """
    
    G_info = set([(i,j,w['weight'])for i,j,w in B.edges(data=True)])
    
    if not G_info:

        return set()

    if len(G_info) == 1:

        return set(G_info)

    labels = [x for x in dict.fromkeys(d['bipartite'] for n,d in B.nodes(data=True))]
    set1,set2 = {n for n,d in B.nodes(data=True) if d['bipartite']==labels[0]}, {n for n,d in B.nodes(data=True) if d['bipartite']==labels[1]}
    N1,N2 = len(set1),len(set2)

    if fix_deg in ["None", "none", "null", "undefined", "", None]:

        E = sum(e[-1] for e in G_info)
        p = 1./(N1*N2) 
        weight_threshold = stats.binom.ppf(1-alpha, E, p) 

        pruned_edges = set([e for e in G_info if e[-1] > weight_threshold])

    else:
        nodes = {i for i, attr in B.nodes(data=True) if attr.get('bipartite') == fix_deg}
        N_other = len(set(B.nodes) - nodes)
        
        degs = {i: 0 for i in nodes}
        for i, j, w in G_info:
            if i in nodes:
                degs[i] += w
            if j in nodes:
                degs[j] += w

        pruned_edges = set()
        for i, j, w in G_info:
            if i in nodes:
                p = 1.0 / N_other  
                threshold = stats.binom.ppf(1 - alpha, degs[i], p)
                if w > threshold:
                    pruned_edges.add((i, j, w))
            elif j in nodes:
                p = 1.0 / N_other
                threshold = stats.binom.ppf(1 - alpha, degs[j], p)
                if w > threshold:
                    pruned_edges.add((i, j, w))
    
    Pruned_B = nx.Graph()    
    edgelist = [[i[0] ,i[1],{'weight':i[2]}]for i in pruned_edges]
    Pruned_B.add_edges_from(edgelist)
    for i in B.nodes():
        Pruned_B.add_node(i, **B.nodes[i])

    results = {"pruned network": Pruned_B, "significant edges":pruned_edges}
    return results 
