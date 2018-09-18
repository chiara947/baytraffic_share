import boto3
import json
import sys
import haversine
import igraph

node_json = json.load(open('../data_repo/tagged_alloneway_nodes.json'))
print(len(node_json))
node_index = 0
node_data = []
for n, cor in node_json.items():
    node_element = {
    'node_osmid': n,
    'node_index': node_index,
    'n_x': cor[1],
    'n_y': cor[0]}
    node_data.append(node_element)
    node_index += 1

BUCKET_NAME = 'deckgltest'
FOLDER = 'Imputed_data'
FILE = 'False9'

s3 = boto3.client('s3')
s3_object = s3.get_object(
    Bucket=BUCKET_NAME,
    Key=FOLDER+'/'+FILE)
s3_data = json.load(s3_object['Body'])['features'] # a list of dictionaries
print(s3_data[0])

edge_index = 0
edge_data = []
nodes_in_edge_set = set()
for e in s3_data:
    e_p = e['properties']
    [[e_c_sx, e_c_sy], [e_c_ex, e_c_ey]] = e['geometry']['coordinates']
    e_length = haversine.haversine(e_c_sy, e_c_sx, e_c_ey, e_c_ex)
    edge_element = {
    'edge_osmid': e_p['link_id'],
    'edge_index': edge_index,
    'start_node': e_p['start_node'],
    'end_node': e_p['end_node'],
    'sec_speed': e_p['sec_speed'],
    'sec_length': e_length,
    'sec_duration': e_length/e_p['sec_speed']
    }
    nodes_in_edge_set.add(e_p['start_node'])
    nodes_in_edge_set.add(e_p['end_node'])
    edge_data.append(edge_element)
    edge_index += 1

### Check if all nodes in the edge dataset are contained in the provided nodes dataset
print(nodes_in_edge_set.issubset(set([*node_json])))

g = igraph.Graph.DictList(
    vertices=node_data,
    edges=edge_data, 
    vertex_name_attr='node_osmid',
    edge_foreign_keys=('start_node','end_node'),
    directed=True)
print(igraph.summary(g))
# print(g.vs[0])
# print(g.es.find(edge_osmid='101554764'))
# route_a = g.get_shortest_paths(
#     g.vs.find(node_osmid='1172644728'),
#     g.vs.find(node_osmid='1172712808'),output="epath")
# print(route_a)
g.write_graphmlz('{}_{}_0509.graphmlz'.format(FOLDER, FILE))
# g = igraph.load('Collected_data_False14.graphmlz')


