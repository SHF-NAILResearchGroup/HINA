Network Construction
+++++++++

Source Code
------------

.. code-block:: python

    import scipy.stats as stats
    import networkx as nx
    from hina.utils import split_node_sets

.. _prune-edges:

.. code-block:: python

    def prune_edges(B,fix_deg='None',alpha=0.05):
        """
        Prunes edges in a bipartite graph to retain only those that are statistically significant under a null model.

        This function identifies and retains edges whose weights are statistically significant based on a binomial distribution
        under a null model. An edge is retained when its weight strictly exceeds the (1-alpha) quantile of the null
        distribution, i.e. when the null probability of a weight at least as large as the observed one is below alpha. The null model can either fix the degrees of a specified node set (e.g., 'student', 'task') or assume
        no fixed degrees. The significance level is controlled by the `alpha` parameter.

        Parameters:
        -----------
        B : networkx.Graph
            A bipartite graph with weighted edges. Every node must have a 'bipartite' attribute indicating its partition
            (as written by `hina.construction.get_bipartite`/`get_tripartite`); the two node sets, and hence the null model,
            are determined from this attribute.
        fix_deg : str, optional
            Specifies the node set whose degrees are fixed in the null model.  For example, if analyzing student 
            involvement in tasks B(student, tasks), you might fix the degrees of the 'student' node set. 
            This ensures the null model preserves the degree distribution of the specified node set.
            If 'None', no degrees are fixed, and the null model assumes random edge weights. Default is 'None'.
        alpha : float, optional
            The significance level for determining statistical significance. Edges whose weight does not strictly exceed the
            (1-alpha) quantile of the null distribution are pruned, so that the null probability of a retained edge's weight
            is below alpha. Default is 0.05.

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

        # The two node sets are identified from the 'bipartite' node attribute rather than from the
        # position of each node in the edge tuples returned by networkx: that position reflects node
        # insertion order, not node type, so it is arbitrary for graphs that were not built with all
        # nodes of one set inserted first (e.g. the per-community projections from hina.mesoscale).
        set1,set2 = split_node_sets(B)
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
