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

def test_prune_edges_no_fixing():
    # Test prune_edges with no degree fixing
    B = create_test_bipartite()
    result = prune_edges(B, fix_deg='None', alpha=0.05)
    
    assert isinstance(result, dict)
    assert "pruned network" in result
    assert "significant edges" in result
    assert isinstance(result["significant edges"], set)
    
    # Every edge is equal to or below the threshold
    expected_edges = set()

    result_edges = {(s, o, w) for s, o, w in result["significant edges"]}
    assert result_edges == expected_edges

def test_prune_edges_fix_student():
    # Test prune_edges with fixed degrees for student nodes
    B = create_test_bipartite()
    result = prune_edges(B, fix_deg='student', alpha=0.05)
    
    assert "pruned network" in result
    assert "significant edges" in result
    assert isinstance(result["significant edges"], set)
    
    # Each edge weight equals its degree-specific threshold
    expected_edges = set()

    result_edges = {(s, o, w) for s, o, w in result["significant edges"]}    
    assert len(result_edges) <= 4
    assert result_edges == expected_edges

def test_prune_edges_fix_object():
    # Test prune_edges with fixed degrees for object nodes
    B = create_test_bipartite()
    result = prune_edges(B, fix_deg='object1', alpha=0.05)
    
    assert "pruned network" in result
    assert "significant edges" in result
    
    # Every edge weight equals the object-specific threshold
    expected_edges = set()

    result_edges = {(s, o, w) for s, o, w in result["significant edges"]}
    assert result_edges == expected_edges

def test_prune_edges_stricter_alpha():
    # Test prune_edges with a stricter significance level
    B = create_test_bipartite()
    result = prune_edges(B, fix_deg='None', alpha=0.01)
    
    assert "pruned network" in result
    assert "significant edges" in result    
    assert len(result["significant edges"]) <= 4

def test_prune_edges_custom_weights():
    # Test prune_edges with custom edge weights
    df = pd.DataFrame({
        'student': ['Alice', 'Bob', 'Alice', 'Alice', 'Bob'],
        'object1': ['ask questions', 'answer questions', 'ask questions', 'evaluating', 'evaluating'],
        'group': ['A', 'B', 'A', 'A', 'B'],
        'attr': ['cognitive', 'cognitive', 'cognitive', 'metacognitive', 'metacognitive']
    })
    
    B = get_bipartite(
        df,
        student_col='student',
        object_col='object1',
        attr_col='attr',
        group_col='group'
    )
    
    result = prune_edges(B, fix_deg='None', alpha=0.05)
    
    assert "pruned network" in result
    assert "significant edges" in result
    
    # Its weight equals the threshold, so strict pruning excludes it
    assert ('Alice', 'ask questions', 2) not in result["significant edges"]

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
    
if __name__ == "__main__":
    pytest.main()
