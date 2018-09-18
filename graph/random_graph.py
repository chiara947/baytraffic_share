import scipy.sparse
import numpy as np
import networkx as nx 
import sys

A = nx.to_scipy_sparse_matrix(nx.grid_2d_graph(10,10))
(A_row, A_col) = A.nonzero()
link_count = A.count_nonzero()
print(link_count)
#sys.exit(0)

OD_pairs = [(0,1), (10,20), (3,5), (40, 15), (8,12), (5,18)]
OD_found = {key:'' for key in OD_pairs}
for (O,D) in OD_pairs:
    #print('OD pair', O,D, A[O,D])
    if A[O,D] > 0:
        OD_found[(O,D)] += str(O)+'-'+str(D)+'-'+str(A[(O,D)])
        OD_pairs.remove((O,D))
print(OD_pairs)
print(OD_found)

B_path = A*A
print(B_path[(0,1)], B_path[0,2])