import pytest
from hina.utils import save_network
import os

def test_save_network_gml(tmp_path):
    G = [(1, 2, 0.5), (2, 3, 0.75)]
    filename = tmp_path / "test_network"
    save_network(G, str(filename), format='gml')
    assert os.path.exists(str(filename) + '.gml')

def test_save_network_gexf(tmp_path):
    G = [(1, 2, 0.5), (2, 3, 0.75)]
    filename = tmp_path / "test_network"
    save_network(G, str(filename), format='gexf')
    assert os.path.exists(str(filename) + '.gexf')

def test_save_network_graphml(tmp_path):
    G = [(1, 2, 0.5), (2, 3, 0.75)]
    filename = tmp_path / "test_network"
    save_network(G, str(filename), format='graphml')
    assert os.path.exists(str(filename) + '.graphml')

def test_save_network_unsupported_format(tmp_path):
    G = [(1, 2, 0.5), (2, 3, 0.75)]
    filename = tmp_path / "test_network"
    with pytest.raises(ValueError, match="Unsupported format: unsupported"):
        save_network(G, str(filename), format='unsupported')

if __name__ == "__main__":
    pytest.main()


def test_split_node_sets():
    import networkx as nx
    import pytest
    from hina.utils import split_node_sets
    G = nx.Graph()
    G.add_weighted_edges_from([("o1", "s1", 1), ("s2", "o1", 2), ("o2", "s2", 1)])  # interleaved insertion
    for n in G.nodes():
        G.nodes[n]["bipartite"] = "student" if n.startswith("s") else "object"
    set1, set2 = split_node_sets(G)
    assert {set1 == {"o1", "o2"}, set2 == {"s1", "s2"}} == {True}      # first-inserted type is focal
    set1, set2 = split_node_sets(G, focal="student")
    assert (set1, set2) == ({"s1", "s2"}, {"o1", "o2"})
    G.nodes["o1"]["tripartite"] = True
    G.nodes["o2"]["tripartite"] = True
    set1, _ = split_node_sets(G)                                        # tripartite objects are never focal
    assert set1 == {"s1", "s2"}
    with pytest.raises(ValueError):
        split_node_sets(G, focal="nope")
    del G.nodes["s1"]["bipartite"]
    with pytest.raises(ValueError):
        split_node_sets(G)
