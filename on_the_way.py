import os
import numpy as np
import pandas as pd
import sys
import warnings
import traceback

import googlemaps
import tqdm


# some hardcoded stuff
filename = 'doctors.csv'
home_addr = 'Conestoga Mall, Waterloo, ON'
work_addr = 'Davis Centre, University of Waterloo, Waterloo, ON'
max_rows = 20 # limit requests while testing


secret_api_key = os.environ.get('GMAPS_API_KEY', '')
gmaps = googlemaps.Client(key=secret_api_key)

spreadsheet = pd.read_csv(filename)

# TODO: batch API calls
def distance_between(endpoint_addrs, midpoint_addrs):
    data = gmaps.distance_matrix(endpoint_addrs, midpoint_addrs)

    results = np.zeros((len(endpoint_addrs), len(midpoint_addrs)))
    results[:, :] = np.nan

    if 'status' not in data or data['status'] != 'OK':
        warnings.warn('API call failed.')
        return results

    for i, endpoint_addr in enumerate(endpoint_addrs):
        for j, midpoint_addr in enumerate(midpoint_addrs):
            try:
                if np.random.random() < 0.05:
                    continue
                results[i, j] = data['rows'][i]['elements'][j]['distance']['value']
            except (KeyError, TypeError) as exc:
                warnings.warn('Could not find distance between `{0}` and `{1}`.'.format(endpoint_addr, midpoint_addr))
                traceback.print_exc()

    return results.transpose()

# build a list of distance from home/work to each place
distances = distance_between([home_addr, work_addr], spreadsheet.address.values[:max_rows])

# copy the lists into table
spreadsheet['distance from home'] = np.nan
spreadsheet['distance from work'] = np.nan
spreadsheet['distance from home'].iloc[:max_rows] = distances[:, 0]
spreadsheet['distance from work'].iloc[:max_rows] = distances[:, 1]

# add a column for the combined distance
spreadsheet['combined distance'] = spreadsheet['distance from home'] + spreadsheet['distance from work']

# sort by lowest combined distance
spreadsheet = spreadsheet.sort_values('combined distance')

# save the result
out_filename = os.path.splitext(filename)[0] + '_sorted.csv'
spreadsheet.to_csv(out_filename, index=False)

print('Done! Please see', out_filename, 'for the results.')
