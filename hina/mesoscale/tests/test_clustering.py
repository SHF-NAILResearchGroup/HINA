import pytest
import networkx as nx
import pandas as pd
from hina.mesoscale import hina_communities
from hina.construction import get_bipartite, get_tripartite

def create_test_graph():
	# Create a test graph directly with NetworkX
	B = nx.Graph()
	B.add_nodes_from(['Alice', 'Bob', 'Charlie'], bipartite='student', group=['A', 'B', 'B'])
	B.add_nodes_from(['ask questions', 'answer questions', 'evaluating', 'monitoring'], bipartite='object', attr=['cognitive', 'cognitive', 'metacognitive', 'metacognitive']) 
	B.add_weighted_edges_from([
		('Alice', 'ask questions', 2),
		('Alice', 'evaluating', 1),
		('Bob', 'answer questions', 3),
		('Charlie', 'monitoring', 1)
	])
	return B

def create_test_graph_from_df():
	# Create a test graph from DataFrame using get_bipartite 
	df = pd.DataFrame({
		'student': ['Alice', 'Bob', 'Alice', 'Charlie'],
		'object1': ['ask questions', 'answer questions', 'evaluating', 'monitoring'],
		'object2': ['tilt head', 'shake head', 'nod head', 'nod head'],
		'group': ['A', 'B', 'A', 'B'],
		'attr': ['cognitive', 'cognitive', 'metacognitive', 'metacognitive']
	})
	
	B = get_bipartite(
		df,
		student_col='student', 
		object_col='object1', 
		attr_col='attr', 
		group_col='group'
	)
	return B

def test_hina_communities():
	# Test the hina_communities function without fixing the number of communities
	G = create_test_graph()
	results = hina_communities(G)

	assert isinstance(results, dict)
	assert 'number of communities' in results
	assert 'node communities' in results
	assert 'community quality (compression ratio)' in results
	assert 'updated graph object' in results
	assert 'sub graphs for each community' in results
	
	# Validate the types of returned values
	assert isinstance(results['number of communities'], int)
	assert isinstance(results['node communities'], dict)
	assert isinstance(results['community quality (compression ratio)'], float)
	assert isinstance(results['updated graph object'], nx.Graph)
	
	# Ensure sub graphs exist for each community
	communities = set(results['node communities'].values())
	for community in communities:
		assert community in results['sub graphs for each community']

def test_hina_communities_from_df():
	# Test hina_communities using a graph created from get_bipartite
	B = create_test_graph_from_df()
	results = hina_communities(B)
	
	# Verify structure of results
	assert isinstance(results, dict)
	assert 'number of communities' in results
	assert 'node communities' in results
	assert 'community quality (compression ratio)' in results
	assert 'updated graph object' in results
	assert 'sub graphs for each community' in results
	
	# Ensure all students are assigned to communities
	students = ['Alice', 'Bob', 'Charlie']
	for student in students:
		assert student in results['node communities']    
	assert results['number of communities'] > 0

def test_hina_communities_fixed():
	# Test hina_communities with a fixed number of communities.
	B = create_test_graph_from_df()
	results = hina_communities(B, fix_B=2)
	
	# Verify the basic structure
	assert isinstance(results, dict)
	assert 'number of communities' in results
	assert 'node communities' in results
	assert 'community quality (compression ratio)' in results
	assert 'updated graph object' in results
	assert 'sub graphs for each community' in results
	
	# With fix_B=2, we should have exactly 2 communities
	assert results['number of communities'] == 2
	
	# Exactly 2 sub-graphs should be created
	assert len(results['sub graphs for each community']) == 2
	
	# Only 2 unique community IDs should exist
	community_ids = set(results['node communities'].values())
	assert len(community_ids) == 2
	
	students = ['Alice', 'Bob', 'Charlie']
	bob_community = results['node communities']['Bob']
	charlie_community = results['node communities']['Charlie']
	alice_community = results['node communities']['Alice']
	
	# Bob and Charlie should be in the same community, Alice in a different one
	assert bob_community == charlie_community
	assert alice_community != bob_community

def test_compression_ratio():
	# Test that the compression ratio increases with fewer communities
	B = create_test_graph_from_df()
	
	# Run with optimal number of communities
	results_no_fix = hina_communities(B)
	optimal_quality = results_no_fix['community quality (compression ratio)']
	
	# Run with a forced smaller number of communities
	results_fix = hina_communities(B, fix_B=2)
	fixed_quality = results_fix['community quality (compression ratio)']
	
	# When forcing fewer communities than optimal, MDL objective should increase as a worse compression
	assert fixed_quality >= optimal_quality


def test_hina_communities_tripartite():
	# Test hina_communities with a tripartite network 
	# Create a test tripartite DataFrame
	data = {
		'student': ['Alice', 'Bob', 'Alice', 'Charlie'],
		'object1': ['ask questions', 'answer questions', 'evaluating', 'monitoring'],
		'object2': ['tilt head', 'shake head', 'nod head', 'nod head'],
		'group': ['A', 'B', 'A', 'B']
	}
	df = pd.DataFrame(data)

	# Generate the tripartite graph
	T = get_tripartite(df, student_col='student', object1_col='object1', object2_col='object2', group_col='group')
	
	# Test hina_communities with the tripartite network
	results = hina_communities(T, fix_B=2)
	
	# Test the community structure 
	bob_community = results['node communities']['Bob']
	charlie_community = results['node communities']['Charlie']
	alice_community = results['node communities']['Alice']
	
	assert bob_community == charlie_community  
	assert alice_community != bob_community    

def _description_length(G, labels, focal_attr):
	# Reference implementation of the description length (Eq. for L(G,b) in the HINA paper), in nats:
	# log N1 + log C(N1-1,B-1) + log[N1!/prod_r n_r!] + log multiset(B*N2, W) + sum_{r,j} log multiset(n_r, w_rj)
	from scipy.special import loggamma
	from collections import Counter
	import numpy as np
	def logchoose(n, k): return loggamma(n + 1) - loggamma(k + 1) - loggamma(n - k + 1)
	def logmultiset(n, k): return logchoose(n + k - 1, k)
	focal = [n for n, d in G.nodes(data=True) if d['bipartite'] == focal_attr]
	targets = [n for n in G.nodes() if n not in focal]
	N1, N2 = len(focal), len(targets)
	W = sum(d['weight'] for _, _, d in G.edges(data=True))
	groups = sorted(set(labels[n] for n in focal))
	B = len(groups)
	sizes = Counter(labels[n] for n in focal)
	L = np.log(N1) + logchoose(N1 - 1, B - 1) + loggamma(N1 + 1) - sum(loggamma(sizes[g] + 1) for g in groups)
	L += logmultiset(B * N2, W)
	for g in groups:
		for j in targets:
			w = sum(G.edges[i, j]['weight'] for i in focal if labels[i] == g and G.has_edge(i, j))
			L += logmultiset(sizes[g], w)
	return L

def test_compression_ratio_matches_description_length_formula():
	# Regression test for the factorial terms of the description length: the code previously used
	# loggamma(n) (= log (n-1)!) where the objective needs log n! = loggamma(n+1) in the multinomial term.
	G = create_test_graph()
	results = hina_communities(G)
	labels = results['node communities']
	trivial = {n: 0 for n in labels}
	expected = _description_length(G, labels, 'student') / _description_length(G, trivial, 'student')
	assert abs(results['community quality (compression ratio)'] - expected) < 1e-9

def test_hina_communities_independent_of_node_insertion_order():
	# The clustered node set must be identified from the 'bipartite' attribute, not from the order in
	# which nodes/edges were inserted (previously a graph with object nodes inserted first raised KeyError
	# or clustered the wrong node set). For plain bipartite graphs the set to cluster is the first-inserted
	# one by default and can be chosen explicitly with `focal`.
	G = create_test_graph()
	G_rev = nx.Graph()
	objects = [n for n, d in G.nodes(data=True) if d['bipartite'] == 'object']
	students = [n for n, d in G.nodes(data=True) if d['bipartite'] == 'student']
	G_rev.add_nodes_from(objects, bipartite='object')
	G_rev.add_nodes_from(students, bipartite='student')
	G_rev.add_weighted_edges_from([(v, u, d['weight']) for u, v, d in G.edges(data=True)])
	r1, r2 = hina_communities(G), hina_communities(G_rev, focal='student')
	assert set(r1['node communities']) == set(students)
	assert r1['node communities'] == r2['node communities']
	assert abs(r1['community quality (compression ratio)'] - r2['community quality (compression ratio)']) < 1e-12

def test_tripartite_projection_pruning_uses_code_and_target_sets():
	# The per-community code-target projections must be pruned with N1 = number of codes, N2 = number of targets.
	from hina.dyad import prune_edges
	import scipy.stats as stats
	df = pd.DataFrame({
		'student': ['S1'] * 6 + ['S2'] * 6 + ['S3'] * 3,
		'code': ['ask', 'ask', 'ask', 'plan', 'ask', 'agree', 'ask', 'ask', 'ask', 'ask', 'plan', 'agree', 'greet', 'greet', 'plan'],
		'target': ['AI', 'AI', 'AI', 'Peer', 'AI', 'Peer', 'AI', 'AI', 'AI', 'AI', 'Peer', 'Peer', 'Peer', 'Peer', 'AI'],
	})
	T = get_tripartite(df, student_col='student', object1_col='code', object2_col='target')
	results = hina_communities(T, fix_B=1)
	P = results['object-object graphs for each community'][0]
	n_code = sum(1 for _, d in P.nodes(data=True) if d['bipartite'] == 'code')
	n_target = sum(1 for _, d in P.nodes(data=True) if d['bipartite'] == 'target')
	assert (n_code, n_target) == (4, 2)
	W = sum(d['weight'] for _, _, d in P.edges(data=True))
	threshold = stats.binom.ppf(0.95, W, 1.0 / (n_code * n_target))
	expected = {(u, v, d['weight']) for u, v, d in P.edges(data=True) if d['weight'] >= threshold}
	assert prune_edges(P)['significant edges'] == expected

if __name__ == "__main__":
	pytest.main()
