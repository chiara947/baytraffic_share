#!python3
#Or change the SHEBANG line to point to the python3 executable, returned by sys.executable
import boto3
import pprint
import json
import os
import google_res
import haversine
from time import gmtime, strftime
import sys
import random

NUMBER_OF_LINKS = 5
S3_BUCKET = 'baytraffic'
S3_FOLDER = 'bz247_test'

# Load data
absolute_path = os.path.dirname(os.path.abspath(__file__))
nodes_dict = json.load(open(absolute_path+'/data_repo/nodes.json'))
links_dict = json.load(open(absolute_path+'/data_repo/tagged_alloneway_links.json'))
query_osm_id_list = random.sample([*links_dict], NUMBER_OF_LINKS)#'8915500'
#print(len(query_osm_id_list))

# Request traffic time from google
res_collection = [] # list of response, one element for one request
time_collection = [] # list of leg wise travel time
for query_osm_id in query_osm_id_list:
	query_osm_link = links_dict[query_osm_id]
	current_time = strftime("%Y-%m-%d %H:%M")
	res, section_duration = google_res.google_res(query_osm_link, nodes_dict)
	if res is not None:
		res['osm_link_id'] = query_osm_id
		res_collection.append(res)
		time_collection.append({'time': current_time, 'link_id': query_osm_id, 'duration': section_duration})
#pprint.pprint(time_collection)

s3client = boto3.client('s3')
save_time = strftime("%Y-%m-%d %H:%M")
s3client.put_object(Body=json.dumps(time_collection, indent=2), Bucket=S3_BUCKET, Key='{}/time_{}_cron.txt'.format(S3_FOLDER, save_time))
s3client.put_object(Body=json.dumps(res_collection, indent=2), Bucket=S3_BUCKET, Key='{}/res_{}_cron.txt'.format(S3_FOLDER, save_time))

'''
Get the major roads from OSM;
For each way, get the start and end coordinates;
Query for the travel time on that way;
May need to get rid of the first and last few steps due to the difference
of Google and OSM coordinates;
Now have the travel time at that specific hour for the way!
'''

