hina.dyad
+++++++++

Tutorial
========

The `dyad` module provides functions for the statistical analysis of interactions in heterogeneous networks at the dyad level. This module focuses on identifying statistically significant edges by comparing observed edge weights against a binomial-based null model. The null model may be configured to fix the weighted degrees for nodes in a specified set. This module provides dyad-level analyses for heterogeneous networks.


Currently, the module contains the `significant_edges.py` file, which includes:

- `prune_edges(B, fix_deg='None', alpha=0.05)`: Prunes edges in a bipartite graph by retaining only those that are statistically significant under a specified null model.


.. list-table:: Functions
   :header-rows: 1

   * - Function
     - Description
   * - `prune_edges(B, fix_deg='None', alpha=0.05) <#prune-edges>`_
     - Computes statistically significant edges using a binomial null model with optional fixed degrees.

Reference
---------

.. _prune-edges:

.. raw:: html

   <div id="prune-edges" class="function-header">
       <span class="class-name">function</span> <span class="function-name">prune_edges(B, fix_deg='None', alpha=0.05)</span>
       <a href="../Code/significant_edges.html#prune-edges" class="source-link">[source]</a>
   </div>

**Description**:
Prunes edges in a bipartite graph to retain only those that are statistically significant under a null model. The function uses a binomial significance test: an edge is retained when its weight strictly exceeds the (1-alpha) quantile of the null distribution of edge weights, derived from the overall edge weight distribution or, when specified, the degree-constrained distribution for nodes whose degrees are fixed, so that the null probability of a retained edge's weight is below alpha. This allows for flexible analysis of dyad-level interaction patterns.

**Parameters**:

.. raw:: html

   <div class="parameter-block">
       (B, fix_deg='None', alpha=0.05)
   </div>

   <ul class="parameter-list">
       <li>
           <span class="param-name">B</span>: A NetworkX graph representing a bipartite network with weighted edges.
           <ul>
               <li>Every node must have a <code>bipartite</code> attribute indicating its partition; the two node sets (and hence <code>N_1</code>, <code>N_2</code> in the null model) are determined from this attribute, not from the order in which nodes or edges were added.</li>
           </ul>
       </li>
       <li>
           <span class="param-name">alpha</span>: The significance level for retaining edges.
           <span class="default-value">Default: <code>0.05</code></span>.
       </li>
       <li>
           <span class="param-name">fix_deg</span>: Specifies the node set for which the weighted degrees are fixed in the null model.
           <ul>
               <li><code>'None'</code>: No degree constraints are applied.</li>
               <li>Any student or object column string (e.g., <code>'student'</code> or <code>'object1'</code>) will fix the weighted degrees for nodes whose <code>bipartite</code> attribute matches that string.</li>
           </ul>
           <span class="default-value">Default: <code>'None'</code></span>.
       </li>
   </ul>

**Returns**:
  - **dict**: A dictionary containing:

    - ``pruned network``: A NetworkX graph representing the pruned network with only statistically significant edges.
    - ``significant edges``: A set of tuples ``(i, j, w)``, where ``i`` and ``j`` are node labels and ``w`` is the weight of the edge.

Demo
====

Example Code
------------

This example demonstrates how to use the `prune_edges` function to filter significant edges in a bipartite network.

**Step 1: Import necessary libraries**

.. code-block:: python

    import pandas as pd
    from hina.construction import get_bipartite
    from hina.dyad import prune_edges

**Step 2: Define the dataset**

A dataset containing student-task interactions:

.. code-block:: python

    df = pd.DataFrame({
        'student': ['Alice', 'Bob', 'Alice', 'Charlie', 'Bob', 'Alice', 'Charlie', 'Alice', 'Bob', 'Charlie',
                    'Alice', 'Bob', 'Charlie', 'Bob', 'Alice', 'Alice', 'Bob', 'Charlie'],
        'object1': ['ask questions', 'answer questions', 'evaluating', 'monitoring', 'ask questions', 'evaluating', 
                    'monitoring', 'ask questions', 'answer questions', 'evaluating', 'ask questions', 'answer questions', 
                    'evaluating', 'monitoring', 'ask questions', 'ask questions', 'answer questions', 'evaluating'],
        'object2': ['tilt head', 'shake head', 'nod head', 'nod head', 'tilt head', 'shake head', 'nod head', 
                    'tilt head', 'shake head', 'nod head', 'shake head', 'nod head', 'tilt head', 'shake head', 
                    'tilt head', 'tilt head', 'shake head', 'nod head'],
        'group': ['A', 'B', 'A', 'B', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A', 'A', 'A', 'B', 'B'],
        'attr': ['cognitive', 'cognitive', 'metacognitive', 'cognitive', 'metacognitive', 
                'cognitive', 'cognitive', 'metacognitive', 'cognitive', 'cognitive', 'metacognitive', 
                'metacognitive', 'cognitive', 'cognitive', 'cognitive', 'cognitive', 'metacognitive', 'metacognitive']
    })

**Step 3: Construct the bipartite network representation**

We create a bipartite network representation of the interactions between students and objects in the 'object1' category, adding the additional attribute 'attr' storing object codes.

.. code-block:: python

    B = get_bipartite(df,student_col='student', object_col='object1', attr_col='attr', group_col='group')

**Step 4: Compute significant edges without fixing degrees**

.. code-block:: python

    alpha = 0.05  # Significance level
    result_none = prune_edges(B, fix_deg='None', alpha=alpha)
    print("Significant Edges (No Degree Fixing):", result_none['significant edges'])

**Step 5: Compute significant edges with fixed degrees for Student nodes**

.. code-block:: python

    result_student= prune_edges(B, alpha=alpha, fix_deg='student')
    print("Significant Edges (Fixing Degree for Student):", result_student['significant edges'])

**Step 6: Compute significant edges with fixed degrees for Object1 nodes**

.. code-block:: python

    result_object = prune_edges(B, alpha=alpha, fix_deg='object1')
    print("Significant Edges (Fixing Degree for Object1):", result_object['significant edges'])

Example Output
--------------

.. code-block:: console

    Significant Edges (No Degree Fixing): 
    {('Alice', 'ask questions', 5)}

    Significant Edges (Fixing Degree for Student): 
    {('Bob', 'answer questions', 4), ('Alice', 'ask questions', 5)}
    
    Significant Edges (Fixing Degree for Object1): 
    {('Bob', 'answer questions', 4), ('Alice', 'ask questions', 5)}

Paper Source
============

If you use this function in your work, please cite:

Feng, S., Gibson, D., & Gasevic, D. (2025). Analyzing students' emerging roles based on quantity and heterogeneity of individual contributions in small group online collaborative learning using bipartite network analysis. Journal of Learning Analytics, 12(1), 253–270.
