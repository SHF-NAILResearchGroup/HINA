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

if __name__ == "__main__":
	pytest.main()
