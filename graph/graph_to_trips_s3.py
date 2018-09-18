import boto3
import json
import sys
import haversine
import igraph
import random
import warnings
import time

def geojson2s3(geojson_dict, out_bucket, out_key):
    s3client = boto3.client('s3')
    s3client.put_object(
        Body=json.dumps(geojson_dict, indent=2), 
        Bucket=out_bucket, 
        Key=out_key, 
        #ContentType='application/json',
        ACL='private')#'public-read'

g = igraph.load('Imputed_data_False9_0509.graphmlz')
print(g.summary())

node_json = json.load(open('../data_repo/tagged_alloneway_nodes.json'))
node_osmid_list = [*node_json]
print('number of nodes in nodes.json: ', len(node_osmid_list))
print('osmid of first node in nodes.json: ', node_osmid_list[0])

t0 = time.time()
trip_no = 500
OD_node_list = random.sample(node_osmid_list, 2*trip_no)
O_node_list = OD_node_list[0:trip_no]
D_node_list = OD_node_list[trip_no:]
# O_node_list.append('1172644728')
# D_node_list.append('1172712808')
# O_node_list.append('1172712808')
# D_node_list.append('1172644728')
print(len(O_node_list), len(D_node_list))

trip_list = []
for trip_id in range(len(O_node_list)):
    # print(trip_id, g.vs.find(node_osmid=origin_node_list[trip_id]), g.vs.find(node_osmid=destination_node_list[trip_id]))
    trip_path = g.get_shortest_paths(
        g.vs.find(node_osmid=O_node_list[trip_id]),
        g.vs.find(node_osmid=D_node_list[trip_id]),
        output="vpath")
    if len(trip_path[0])==0:
        #print('no route found')
        continue
    else:
        #print(trip_path)
        path_node = trip_path[0]
        timestamp = random.randint(0,3600)
        timestamp = 0
        # first time step
        segments = [[g.vs[path_node[0]]['n_x'], g.vs[path_node[0]]['n_y'], timestamp]]
        # second till the last time step
        for (sec_node_start, sec_node_end) in zip(path_node, path_node[1:]):
            sec_duration = g.es[g.get_eid(sec_node_start, sec_node_end)]['sec_duration']
            timestamp += sec_duration
            segment = [g.vs[sec_node_end]['n_x'], g.vs[sec_node_end]['n_y'], timestamp]
            segments.append(segment)
        #print(segments)

    trip_list.append({'trip_id': trip_id, 'segments': segments})

print('number of trips: ', len(trip_list))
t1 = time.time()
print('time to run {} OD shortest path queries is {} sec'.format(trip_no, t1-t0))
### 500 queries in 20 seconds

# S3_BUCKET = 'deckgltest'
# S3_FOLDER = 'Trip_vis/'
# KEY = S3_FOLDER+'trip_test_500_timestamp.json'
# geojson2s3(trip_list, S3_BUCKET, KEY)

print('end of graph_to_trips_s3.py')

