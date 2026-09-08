import pytest
import pandas as pd
import networkx as nx
from hina.construction import get_bipartite
from hina.dyad import prune_edges

def create_test_dataframe():
    # Create a sample DataFrame for testing
    df = pd.DataFrame({
        'student': ['Alice', 'Bob', 'Alice', 'Charlie'],
        'object1': ['ask questions', 'answer questions', 'evaluating', 'monitoring'],
        'object2': ['tilt head', 'shake head', 'nod head', 'nod head'],
        'group': ['A', 'B', 'A', 'B'],
        'attr': ['cognitive', 'cognitive', 'metacognitive', 'metacognitive']
    })
    return df

def create_test_bipartite():
    # Create a bipartite network from the test DataFrame
    df = create_test_dataframe()
    B = get_bipartite(
        df,
        student_col='student', 
        object_col='object1', 
        attr_col='attr', 
        group_col='group'
    )
    return B

def _expected_no_fixing(B, alpha):
    # reference implementation of the default null model: W unit interactions placed uniformly over N1*N2 pairs;
    # an edge is significant when its weight strictly exceeds the (1-alpha) quantile of Binomial(W, 1/(N1*N2))
    from scipy import stats
    sets = {}
    for n, d in B.nodes(data=True):
        sets.setdefault(d['bipartite'], set()).add(n)
    N1, N2 = [len(v) for v in sets.values()]
    W = sum(w for _, _, w in B.edges(data='weight'))
    q = stats.binom.ppf(1 - alpha, W, 1.0 / (N1 * N2))
    return {(u, v, w) for u, v, w in B.edges(data='weight') if w > q}

def create_weighted_test_bipartite():
    # The example from the documentation: 18 interactions, 3 students x 4 objects
    df = pd.DataFrame({
        'student': ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob', 'Alice', 'Charlie', 'Alice', 'Bob', 'Alice', 'Charlie', 'Bob',
                    'Charlie', 'Alice', 'Alice', 'Bob', 'Charlie', 'Bob'],
        'object1': ['ask questions', 'answer questions', 'evaluating', 'monitoring', 'answer questions', 'ask questions',
                    'evaluating', 'ask questions', 'answer questions', 'ask questions', 'monitoring', 'answer questions',
                    'evaluating', 'monitoring', 'ask questions', 'ask questions', 'evaluating', 'monitoring'],
        'attr': ['cognitive'] * 18,
    })
    return get_bipartite(df, student_col='student', object_col='object1', attr_col='attr')

def test_prune_edges_no_fixing():
    # Test prune_edges with no degree fixing on a graph with one clearly over-represented edge
    B = create_weighted_test_bipartite()
    result = prune_edges(B, fix_deg='None', alpha=0.05)

    assert isinstance(result, dict)
    assert "pruned network" in result
    assert "significant edges" in result
    assert isinstance(result["significant edges"], set)

    result_edges = {(s, o, w) for s, o, w in result["significant edges"]}
    assert result_edges == _expected_no_fixing(B, 0.05)
    # Alice-ask questions (5 of the 18 interactions on 12 possible pairs) is significant; weight-1 edges are not
    assert ('Alice', 'ask questions', 5) in result_edges
    assert all(w > 1 for _, _, w in result_edges)
    # under the strict rule the null probability of every retained weight is below alpha
    from scipy import stats
    assert all(stats.binom.sf(w - 1, 18, 1.0 / 12) < 0.05 for _, _, w in result_edges)

def test_prune_edges_fix_student():
    # Test prune_edges with fixed degrees for student nodes
    B = create_weighted_test_bipartite()
    result = prune_edges(B, fix_deg='student', alpha=0.05)

    assert "pruned network" in result
    assert "significant edges" in result
    assert isinstance(result["significant edges"], set)

    result_edges = {(s, o, w) for s, o, w in result["significant edges"]}
    # Alice sent 5 of her 7 interactions to 'ask questions' and Bob 4 of his 6 to 'answer questions'
    assert result_edges == {('Alice', 'ask questions', 5), ('Bob', 'answer questions', 4)}

def test_prune_edges_fix_object():
    # Test prune_edges with fixed degrees for object nodes
    B = create_weighted_test_bipartite()
    result = prune_edges(B, fix_deg='object1', alpha=0.05)

    assert "pruned network" in result
    assert "significant edges" in result

    result_edges = {(s, o, w) for s, o, w in result["significant edges"]}
    # 'ask questions' received 5 of its 6 interactions from Alice and 'answer questions' all 4 of its interactions from Bob
    assert result_edges == {('Alice', 'ask questions', 5), ('Bob', 'answer questions', 4)}

def test_prune_edges_stricter_alpha():
    # Test prune_edges with a stricter significance level
    B = create_test_bipartite()
    result = prune_edges(B, fix_deg='None', alpha=0.01)
    
    assert "pruned network" in result
    assert "significant edges" in result    
    assert len(result["significant edges"]) <= 4

def test_prune_edges_custom_weights():
    # Test prune_edges with repeated rows producing edge weights > 1
    df = pd.DataFrame({
        'student': ['Alice', 'Bob', 'Alice', 'Alice', 'Bob'],
        'object1': ['ask questions', 'answer questions', 'ask questions', 'evaluating', 'evaluating'],
        'group': ['A', 'B', 'A', 'A', 'B'],
        'attr': ['cognitive', 'cognitive', 'cognitive', 'metacognitive', 'metacognitive']
    })
    B = get_bipartite(df, student_col='student', object_col='object1', attr_col='attr', group_col='group')
    assert B.edges['Alice', 'ask questions']['weight'] == 2

    result = prune_edges(B, fix_deg='None', alpha=0.05)
    assert "pruned network" in result
    assert "significant edges" in result
    result_edges = {(s, o, w) for s, o, w in result["significant edges"]}
    assert result_edges == _expected_no_fixing(B, 0.05)
    # with only 5 interactions on 6 pairs no edge reaches significance at alpha = 0.05 ...
    assert result_edges == set()
    # ... but the weight-2 edge is the only one retained at a permissive level
    lenient = {(s, o, w) for s, o, w in prune_edges(B, fix_deg='None', alpha=0.5)["significant edges"]}
    assert lenient == {('Alice', 'ask questions', 2)}

def test_prune_edges_empty_graph():
    # Test prune_edges with an empty graph with no edges
    # Create an empty bipartite graph with no edges between nodes
    B = nx.Graph()
    B.add_node("Alice", bipartite="student")
    B.add_node("question1", bipartite="object1")
    result = prune_edges(B, fix_deg="None", alpha=0.05)
    assert result == set()

def test_prune_edges_single_edge():
    # Test prune_edges with a graph containing only one edge
    # Create a bipartite graph with a single edge
    B = nx.Graph()
    B.add_node("Alice", bipartite="student")
    B.add_node("question1", bipartite="object1")
    B.add_edge("Alice", "question1", weight=1)
    result = prune_edges(B, fix_deg="None", alpha=0.05)
    
    # The single edge should always be significant
    expected_edge = ("Alice", "question1", 1)
    assert expected_edge in result

def test_prune_edges_no_nodes():
    # Test prune_edges with a completely empty graph with no nodes or edges
    B = nx.Graph()
    result = prune_edges(B, fix_deg="None", alpha=0.05)
    assert result == set()

def test_prune_edges_invalid_fix_deg():
    # Test prune_edges with an invalid fix_deg parameter."""
    B = create_test_bipartite()
    result = prune_edges(B, fix_deg="invalid_value", alpha=0.05)
    
    assert "pruned network" in result
    assert "significant edges" in result
    assert isinstance(result["significant edges"], set)
    assert len(result["significant edges"]) == 0

def test_prune_edges_extreme_alpha():
    # Test prune_edges with extreme alpha values 
    B = create_test_bipartite()
    
    # With alpha=0, no edges should be significant
    result_zero = prune_edges(B, fix_deg="None", alpha=0)
    assert len(result_zero["significant edges"]) == 0
    
    # With alpha=1, all edges should be significant
    result_one = prune_edges(B, fix_deg="None", alpha=1)
    assert len(result_one["significant edges"]) == len(B.edges())
    expected_edges = {
        ("Alice", "ask questions", 1), 
        ("Alice", "evaluating", 1),
        ("Bob", "answer questions", 1), 
        ("Charlie", "monitoring", 1)
    }
    result_edges = {(s, o, w) for s, o, w in result_one["significant edges"]}
    assert result_edges == expected_edges
    
def test_prune_edges_threshold_uses_node_types_not_insertion_order():
    # Regression test: the null model's success probability must be 1/(N1*N2) with N1, N2 the sizes of the
    # two node *types* (from the 'bipartite' attribute), regardless of the order in which nodes were inserted.
    # Before this test, N1 and N2 were read off the position of nodes in networkx edge tuples, which follows
    # insertion order; for graphs whose two node sets are interleaved (e.g. the per-community projections
    # returned by hina_communities on tripartite graphs) this mixed the sets and lowered the threshold.
    import scipy.stats as stats
    edges = [("code_A", "AI", 5), ("Peer", "code_B", 20), ("code_C", "Peer", 6), ("AI", "code_D", 4),
             ("code_E", "Peer", 3), ("code_F", "AI", 2), ("Peer", "code_G", 8)]
    G = nx.Graph()
    G.add_weighted_edges_from(edges)            # nodes are created in edge order: types interleaved
    for n in G.nodes():
        G.nodes[n]["bipartite"] = "target" if n in ("AI", "Peer") else "code"
    n_code, n_target, W = 7, 2, sum(w for _, _, w in edges)
    threshold = stats.binom.ppf(0.95, W, 1.0 / (n_code * n_target))
    expected = {(u, v, w) for u, v, w in edges if w > threshold}
    result = prune_edges(G, fix_deg="None", alpha=0.05)
    assert result["significant edges"] == expected
    # the same graph with the same edges in reversed tuple order must give the same answer
    G_rev = nx.Graph()
    G_rev.add_weighted_edges_from([(v, u, w) for u, v, w in reversed(edges)])
    for n in G_rev.nodes():
        G_rev.nodes[n]["bipartite"] = G.nodes[n]["bipartite"]
    result_rev = prune_edges(G_rev, fix_deg="None", alpha=0.05)
    assert {frozenset((u, v)) for u, v, _ in result_rev["significant edges"]} == \
           {frozenset((u, v)) for u, v, _ in expected}

def test_prune_edges_requires_bipartite_attribute():
    G = nx.Graph()
    G.add_weighted_edges_from([("Alice", "ask questions", 2), ("Bob", "evaluating", 1)])
    with pytest.raises(ValueError):
        prune_edges(G)

if __name__ == "__main__":
    pytest.main()