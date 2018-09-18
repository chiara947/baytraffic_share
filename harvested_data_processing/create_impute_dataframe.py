import pandas as pd 
import sys
import numpy as np
import json
import itertools
from time import gmtime, strftime

### impute data
# get OSM node information (node_id: coordinates)
node_list = json.load(open('../data_repo/nodes.json'))
# get OSM link information (link_id: list_of_sections)
link_list = json.load(open('../data_repo/tagged_alloneway_links.json'))
print('unique roads: ', len(link_list))
# each json link may contain more than one section
total_section_count = 0
for key, value in link_list.items():
    total_section_count += len(value['sections'])
print('unique sections: ', total_section_count)

query_weekend_list = [True, False]
query_hour_list = [hr for hr in range(8,18)]

def assemble_impute_dataframe(link_list):
    feature_list = []
    for key, value in link_list.items():
        link_id = key
        link_type = value['tag_type']
        for sect in value['sections']:
            [start_node, end_node] = sect
            for query_weekend, query_hour in itertools.product(query_weekend_list, query_hour_list):
                feature_list.append({'link_id': link_id, 'link_type': link_type, 'start_node': start_node, 'end_node': end_node,
                    'query_hour': query_hour, 'query_weekend': query_weekend,
                    'coordinates': (tuple(node_list[start_node][::-1]), tuple(node_list[end_node][::-1])),
                    'approx_coordinates': ((round(node_list[start_node][1],2), round(node_list[start_node][0],2)),(round(node_list[end_node][1],2), round(node_list[end_node][0],2)))})
    return pd.DataFrame(feature_list)
impute_df = assemble_impute_dataframe(link_list)
print('shape of the impute dataframe: ', impute_df.shape)
impute_df.to_pickle('impute_df_{}.pkl'.format(strftime("%Y-%m-%d-%H-%M"))