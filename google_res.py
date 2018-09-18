#!python3
import requests
import os
import numpy as np
from google_key import GOOGLE_MAPS_API_KEY
import calendar
import time
import sys

GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/directions/json'
GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_API_KEY

def google_res(link, nodes_dict):
    params = {
        'origin': str(nodes_dict[link['start']][0])+','+str(nodes_dict[link['start']][1]),#'37.6761780,-122.4576602',
        'destination': str(nodes_dict[link['end']][0])+','+str(nodes_dict[link['end']][1]),#'37.67670,-122.4582',
        'departure_time': 'now',#str(calendar.timegm(time.gmtime())+60),
        'mode': 'driving',
        'key': GOOGLE_MAPS_API_KEY
    }

    req = requests.get(GOOGLE_MAPS_API_URL, params=params)
    res = req.json()

    if len(res['routes'])==0:
        return(None, None)

    # Total distance of the journey, used to calculate fractional distance for each leg
    useful_res = {'google_total_length': sum(leg['distance']['value'] for leg in res['routes'][0]['legs'])}
    if abs(useful_res['google_total_length'] - link['total_length']) > 0.1 * link['total_length']:
        #print('distance not match')
        return(None, None)

    # Leg wise distance
    useful_res['xp_0'] = [leg['distance']['value'] for leg in res['routes'][0]['legs']]
    # Leg wise travel time
    try:
        useful_res['fp_0'] = [leg['duration_in_traffic']['value'] for leg in res['routes'][0]['legs']]
    except KeyError:
        #print('no real time traffic information')
        useful_res['fp_0'] = [leg['duration']['value'] for leg in res['routes'][0]['legs']]
    # Cummulative leg wise distance
    useful_res['xp'] = np.cumsum(useful_res['xp_0'])
    # Cummulative leg wise distance in fraction
    useful_res['xp'] = [0] + [xp/useful_res['google_total_length'] for xp in useful_res['xp']]
    # Cummulative leg wise travel time
    useful_res['fp'] = [0] + np.cumsum(useful_res['fp_0']).tolist()

    # The above gives us a series of travel times to reach each "Google nodes" along the route
    # Now linear interpolate the travel times to get to the "OSM nodes" along the route.
    link_cum_time = np.interp(link['cum_frac_length'], useful_res['xp'], useful_res['fp'])
    link_section_time = [link_cum_time[0]] + np.diff(link_cum_time).tolist()
    #print('successful query')
    return(res, link_section_time)

'''
4104469914,
  "lat": 37.6761780,
  "lon": -122.4576602
1655404391,
  "lat": 37.6764189,
  "lon": -122.4579374
65402567
  "lat": 37.6767005,
  "lon": -122.4582452,
'''
