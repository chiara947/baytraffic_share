#!python3
import boto3
import botocore
import pprint
import json
import os
from time import gmtime, strftime
import sys
import random
import pandas as pd
from datetime import datetime
import numpy as np

def assemble_geojson(query_res, link_list, node_list):
    # Assemble geojson
    feature_list = []
    for link_res in query_res:
        link_id = link_res['link_id']
        query_time = link_res['time']
        for sect_count in range(len(link_res['duration'])):
            [start_node, end_node] = link_list[link_id]['sections'][sect_count]
            sec_length = link_list[link_id]['length'][sect_count]
            sec_duration = link_res['duration'][sect_count]
            if sec_duration == 0:
                print('zero_duration')
                continue
            sec_prop = {
                'link_id': link_id,
                'query_time': query_time,
                'start_node': start_node,
                'end_node': end_node,
                'sec_speed': sec_length/sec_duration
                }
            sec_geom = {
                'type': 'LineString',
                'coordinates': [node_list[start_node][::-1], node_list[end_node][::-1]]
                }
            feature_list.append({'type': 'Feature', 'geometry': sec_geom, 'properties': sec_prop})

    geojson_dict = {'type': 'FeatureCollection', 'features': feature_list}
    return geojson_dict

def assemble_dataframe(query_res, link_list, node_list):
    # Assemble geojson
    feature_list = []
    zero_duration = 0
    for link_res in query_res:
        link_id = link_res['link_id']
        link_type = link_list[link_id]['tag_type']
        query_time = link_res['time']
        for sect_count in range(len(link_res['duration'])):
            [start_node, end_node] = link_list[link_id]['sections'][sect_count]
            sec_length = link_list[link_id]['length'][sect_count]
            sec_duration = link_res['duration'][sect_count]
            if sec_duration == 0:
                zero_duration += 1
                #print('zero_duration')
                continue
            sect = {
                'link_id': link_id,
                'link_type': link_type,
                'query_hour': datetime.strptime(query_time, '%Y-%m-%d %H:%M').hour,
                'query_weekday': datetime.strptime(query_time, '%Y-%m-%d %H:%M').weekday(),
                'start_node': start_node,
                'end_node': end_node,
                'sec_speed': sec_length/sec_duration,
                #'type': 'LineString',
                'coordinates': (tuple(node_list[start_node][::-1]), tuple(node_list[end_node][::-1]))
                }
            feature_list.append(sect)

    print('number of zero-duration sections: ', zero_duration)
    return pd.DataFrame(feature_list)

def geojson2s3(geojson_dict, out_bucket, out_key):
    s3client = boto3.client('s3')
    s3client.put_object(
        Body=json.dumps(geojson_dict, indent=2), 
        Bucket=out_bucket, 
        Key=out_key, 
        ContentType='application/json',
        ACL='private')#'public-read'

# get OSM node information (node_id: coordinates)
node_list = json.load(open('../data_repo/nodes.json'))

# get OSM link information (link_id: list_of_sections)
link_list = json.load(open('../data_repo/tagged_alloneway_links.json'))
print('no. of road links: ', len(link_list))

# each json link may contain more than one section
total_section_count = 0
for key, value in link_list.items():
    total_section_count += len(value['sections'])
print('no. of road sections: ', total_section_count)

# get google data (link level duration at particular query times)
BUCKET_NAME = 'CHANGE'
#KEY = 'time_2018-03-16 11:39.txt'
OPERATION = 'all_files' # all_files or single_file
PREFIXES = ['CHANGE'] # Change to ['time', 'user/time'], or something similar

s3 = boto3.resource('s3')
key_time = []
for prefix in PREFIXES:
    key_time_prefix = [obj.key for obj in s3.Bucket(BUCKET_NAME).objects.filter(Prefix=prefix)]
    key_time.extend(key_time_prefix)
    print('Number of time result files with prefix {} is: '.format(prefix), len(key_time_prefix))
print('Total number of time result files: ', len(key_time))

if OPERATION == 'single_file':
    for KEY in key_time:
        s3_object = s3.Object(BUCKET_NAME, KEY)
        file_content = s3_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        query_res = json_content
        print('numbers of query results loaded: {}'.format(len(query_res)))
        geojson_dict = assemble_geojson(query_res, link_list, node_list)
        geojson2s3(geojson_dict, 'deckgltest', KEY)

if OPERATION == 'all_files':
    query_res = []
    for KEY in key_time:
        s3_object = s3.Object(BUCKET_NAME, KEY)
        file_content = s3_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        query_res.extend(json_content)
    print('no. of query results: {}'.format(len(query_res)))
    res_df = assemble_dataframe(query_res, link_list, node_list)
    print('unique query hours: ', np.sort(res_df.query_hour.unique()))
    print(res_df.head())
    res_df.to_pickle('query_results_df_{}.pkl'.format(strftime("%Y-%m-%d-%H-%M")))
