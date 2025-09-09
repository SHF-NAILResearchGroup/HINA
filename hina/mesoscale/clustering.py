import numpy as np
from scipy.special import loggamma
import heapq
import networkx as nx
from collections import Counter
from collections import defaultdict

def hina_communities(G,fix_B=None):
	"""
	Identifies bipartite communities in a graph by optimizing a Minimum Description Length (MDL) objective.

	This function partitions the nodes of a bipartite graph into communities by minimizing the MDL objective,
	which balances the complexity of the community structure with the accuracy of representing the graph.
	The function supports fixing the number of communities (`fix_B`) and can handle tripartite networks. 

	Parameters:
	-----------
	G : networkx.Graph
		A bipartite or tripartite graph with weighted edges. Nodes must have a 'bipartite' attribute
		indicating their partition (e.g., 'student', 'coded behaviors'). If the graph is tripartite, nodes should
		have a 'tripartite' attribute set to `True`.
	fix_B : int or str, optional
		If specified, fixes the number of communities to this value. If `None`, the function automatically
		determines the optimal number of communities. Default is `None`.

	Returns:
	--------
	dict
		A dictionary containing the following keys:
		- 'number of communities': The number of communities identified.
		- 'node communities': A dictionary mapping each node to its community label.
		- 'community quality (compression ratio)': A measure of how well the inferred communities compress
		  the network structure, calculated as the compression ratio (description length / naive description length).
		- 'updated graph object': The input graph with an added 'communities' attribute for each node.
		- 'sub graphs for each community': A dictionary where keys are community labels and values are subgraphs of nodes
		  belonging to that community.
		- 'object-object graphs for each community' (only for tripartite networks): A dictionary where keys
		  are community labels and values are projected graphs representing relationships between objects
		  within each community. 
	"""
	G_info = set([(i,j,w['weight'])for i,j,w in G.edges(data=True)])

	v = set()
	node_bipartite_list = [x for x in [data['bipartite'] for n, data in G.nodes(data=True)]\
					 if not (x in v or v.add(x))]
	# if fix_B == None:
	#     set1,set2 = set([e[0] for e in G_info]),set([e[1] for e in G_info])
	#     print('set1,set2',set1,set2)
	# elif fix_B == node_bipartite_list[0]:
	#     set1,set2 = set([e[0] for e in G_info]),set([e[1] for e in G_info])
	# elif fix_B == node_bipartite_list[1]:
	#     set2,set1 = set([e[0] for e in G_info]),set([e[1] for e in G_info])
	set1,set2 = set([e[0] for e in G_info]),set([e[1] for e in G_info])

	
	N1,N2 = len(set1),len(set2)
	W = sum([e[2] for e in G_info])

	cluster2nodes = {i:set([i]) for i in set1}
	node2cluster = {i:i for i in set1}
	cluster2weights = {}
	for e in G_info:
		i,j,w = e
		c = node2cluster[i]
		if not(c in cluster2weights): cluster2weights[c] = Counter({k:0 for k in set2})
		cluster2weights[c][j] += w
		# if fix_B != node_bipartite_list[1]:
		# 	c = node2cluster[i]
		# 	if not(c in cluster2weights): cluster2weights[c] = Counter({k:0 for k in set2})
		# 	cluster2weights[c][j] += w
		# else: 
		# 	c = node2cluster[j]
		# 	if not(c in cluster2weights): cluster2weights[c] = Counter({k:0 for k in set1})
		# 	cluster2weights[c][i] += w

	def logchoose(n,k):
		"""
		log binomial coefficient
		"""
		return loggamma(n+1) - loggamma(k+1) - loggamma(n-k+1)

	def logmultiset(n,k):
		"""
		log multiset coefficient
		"""
		return logchoose(n+k-1,k)

	def C(B):
		"""
		constants in the description length (only depend on size B of partition)
		"""
		return np.log(N1) + logchoose(N1-1,B-1) + loggamma(N1) + logmultiset(N2*B,W)

	def F(r):
		"""
		cluster-level term in the description length
		r is a cluster name
		"""
		nr = len(cluster2nodes[r])
		weights = cluster2weights[r]
		return -loggamma(nr) + sum(logmultiset(nr,w) for w in weights.values())

	def merge_dF(r,s):
		"""
		change in cluster-level terms from merging existing clusters r and s
		"""
		bef = F(r) + F(s)
		nrs = len(cluster2nodes[r]) + len(cluster2nodes[s])
		weights = cluster2weights[r] + cluster2weights[s]
		aft = -loggamma(nrs) + sum(logmultiset(nrs,w) for w in weights.values())
		return aft - bef

	past_merges = []
	for c1 in cluster2nodes:
		for c2 in cluster2nodes:
			if c1 != c2:
				dF = merge_dF(c1,c2)
				heapq.heappush(past_merges,(dF,(c1,c2)))

	HN1 = C(N1) + sum(F(r) for r in cluster2nodes)
	Hs,past_partitions = [],[]
	Hs.append(HN1)
	past_partitions.append(node2cluster.copy())

	B,H = N1,HN1
	while B > 1:

		dF,pair = heapq.heappop(past_merges)
		while not(pair[0] in cluster2nodes) or not(pair[1] in cluster2nodes):
			dF,pair = heapq.heappop(past_merges)

		c1,c2 = pair
		c12 = 'Merge_at_Beq_'+str(B)
		cluster2weights[c12] = cluster2weights[c1] + cluster2weights[c2]
		cluster2nodes[c12] = cluster2nodes[c1].union(cluster2nodes[c2])
		for i in cluster2nodes[c12]:
			node2cluster[i] = c12
		del cluster2weights[c1],cluster2weights[c2],cluster2nodes[c1],cluster2nodes[c2]
		past_partitions.append(node2cluster.copy())

		H += dF + C(B-1) - C(B)

		for c3 in cluster2nodes:
			if c3 != c12:
				dF = merge_dF(c3,c12)
				heapq.heappush(past_merges,(dF,(c3,c12)))

		Hs.append(H)
		B -= 1

	if fix_B is None:
		best_ind = np.argmin(Hs)
	else:
		best_ind = len(Hs)-fix_B

	H0 = Hs[-1]
	Hmdl = Hs[best_ind]
	community_labels = past_partitions[best_ind]
	old_labels = list(set(community_labels.values()))
	labelmap = dict(zip(old_labels,range(len(old_labels))))
	community_labels = {str(i[0]):labelmap[str(i[1])] for i in community_labels.items()}

	nx.set_node_attributes(G, community_labels, 'communities')

	grouped_nodes = defaultdict(list)
	for node, community in community_labels.items():
		grouped_nodes[community].append(node)

# Create subgraphs for each community
	sub_Gs = {}
	for community, u_nodes in grouped_nodes.items():
		G_sub = nx.Graph()
		for u_node in u_nodes:
			G_sub.add_node(u_node, **G.nodes[u_node])
		v_nodes = set()
		for u_node in u_nodes:
			for v_node in G.neighbors(u_node):
				v_nodes.add(v_node)
				G_sub.add_node(v_node, **G.nodes[v_node])
		for u_node in u_nodes:
			for v_node in G.neighbors(u_node):
				if G.has_edge(u_node, v_node):
					G_sub.add_edge(u_node, v_node, **G.edges[u_node, v_node])
		sub_Gs[community] = G_sub

# Create the projected subgraphs for each community for tripartite network
	
	if any(j.get('tripartite') == True for i, j in G.nodes(data=True)):
		sub_Gs_object = {}
		for i, g in sub_Gs.items():
			objects_objects = [[j,w['weight']] for i,j,w in g.edges(data=True)]
			bipartite_attrs = list(set([j['bipartite'] for i, j in g.nodes(data=True)]))
			combined_attr = None
			student_attr = None
			attr1, attr2 = "object1", "object2"
			for attr in bipartite_attrs:
				if isinstance(attr, str) and '(' in attr and ')' in attr and ',' in attr:
					combined_attr = attr
				else:
					student_attr = attr
			try:
				attr1, attr2 = combined_attr.strip("()").split(",")
				attr1 = attr1.strip()
				attr2 = attr2.strip()
				pair_count = defaultdict(int)
				for n in objects_objects:
					if '**' in n[0]:
						parts = n[0].split('**')
						if len(parts) == 2:
							pair = (parts[0].strip(), parts[1].strip())
							pair_count[pair] += n[1]
				w_edges = [(object1, object2, {'weight': count}) 
						  for (object1, object2), count in pair_count.items() 
						  if object1 != 'NA' and object2 != 'NA']
				G_ = nx.Graph()
				G_.add_edges_from(w_edges)
				for node in G_.nodes():
					if node in [edge[0] for edge in w_edges]:
						G_.nodes[node]['bipartite'] = attr1
					else:
						G_.nodes[node]['bipartite'] = attr2
						
				sub_Gs_object[i] = G_
			except Exception as e:
				print(f"Error processing community {i}: {str(e)}")
				sub_Gs_object[i] = nx.Graph()
		
	if any(j.get('tripartite') == True for i, j in G.nodes(data=True)):
			results = {'number of communities': len(set(community_labels.values())), \
			   "node communities": community_labels, "community quality (compression ratio)":Hmdl/H0,\
			   'updated graph object':G, 'sub graphs for each community':sub_Gs, 'object-object graphs for each community': sub_Gs_object}
	else:
		results = {'number of communities': len(set(community_labels.values())), \
			   "node communities": community_labels, "community quality (compression ratio)":Hmdl/H0,\
			   'updated graph object':G, 'sub graphs for each community':sub_Gs}
	
	return results
