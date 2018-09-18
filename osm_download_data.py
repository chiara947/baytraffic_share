#!python3
import overpy
import numpy as np
import sys
import itertools
import requests

#api = overpy.Overpass()
overpass_url = "http://overpass-api.de/api/interpreter?"

(bay_bottom, bay_left, bay_top, bay_right) = (36.8931, -123.5337, 38.8643, -121.2082)
bay_x = np.linspace(bay_left, bay_right, 12)
bay_y = np.linspace(bay_bottom, bay_top, 12)
#print(bay_x)
#print(bay_y)
bbox_no = 0
for (bbox_l, bbox_r) in zip(bay_x, bay_x[1:]):
    for (bbox_b, bbox_t) in zip(bay_y, bay_y[1:]):
        query_url = overpass_url+"data=[out:json][bbox:{},{},{},{}];way[highway];(._;>;);out;".format(bbox_b, bbox_l, bbox_t, bbox_r)
        r = requests.get(query_url)
        if len(r.content)<300:
            continue
        with open('data_repo/bay/bay_area_{}.osm'.format(bbox_no), 'wb') as f:
            f.write(r.content)
        bbox_no += 1
        print('save bay_area_{}.osm'.format(bbox_no))

print('end of osm_download_data.py')
