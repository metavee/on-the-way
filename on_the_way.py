import os
import pandas as pd
import sys

import googlemaps
import tqdm


# some hardcoded stuff
filename = 'doctors.csv'
home_addr = 'Conestoga Mall, Waterloo, ON'
work_addr = 'Davis Centre, University of Waterloo, Waterloo, ON'


secret_api_key = os.environ.get('GMAPS_API_KEY', '')
gmaps = googlemaps.Client(key=secret_api_key)

spreadsheet = pd.read_csv(filename)

# TODO: batch API calls
def distance_between(from_addr, to_addr):
    data = gmaps.distance_matrix([from_addr], [to_addr])
    dist = data['rows'][0]['elements'][0]['distance']['value']

    return dist

# build a list of distance from home/work to each place
distances_from_home = []
distances_from_work = []

for addr in tqdm.tqdm(spreadsheet['address'].values):
    distances_from_home.append(distance_between(home_addr, addr))
    distances_from_work.append(distance_between(work_addr, addr))

# copy the lists into table
spreadsheet['distance from home'] = distances_from_home
spreadsheet['distance from work'] = distances_from_work

# add a column for the combined distance
spreadsheet['combined distance'] = spreadsheet['distance from home'] + spreadsheet['distance from work']

# sort by lowest combined distance
spreadsheet = spreadsheet.sort_values('combined distance')

# save the result
out_filename = os.path.splitext(filename)[0] + '_sorted.csv'
spreadsheet.to_csv(out_filename, index=False)

print('Done! Please see', out_filename, 'for the results.')
