import os
import numpy as np
import pandas as pd
import sys
import warnings
import traceback

import googlemaps
from tqdm import tqdm


# some hardcoded stuff
filename = 'doctors.csv'
home_addr = 'Conestoga Mall, Waterloo, ON'
work_addr = 'Davis Centre, University of Waterloo, Waterloo, ON'

secret_api_key = os.environ.get('GMAPS_API_KEY', '')
gmaps = googlemaps.Client(key=secret_api_key)

spreadsheet = pd.read_csv(filename)

endpoint_addrs = [home_addr, work_addr]

def batch(size):
    """
    Decorator for functions of type list[n] -> list[n]

    Splits up the input into chunks of size <= `size`, calls the function separately, and stitches together the output.
    """

    def decorator(fxn):
        def decorated(arg):
            start_indices = list(range(0, len(arg), size))
            results = []
            for i in tqdm(start_indices):
                results.append(fxn(arg[i:i+size]))

            if type(results[0]) == list:
                return sum(results, [])
            elif type(results[0]) == np.ndarray:
                if len(results[0].shape) <= 1:
                    return np.hstack(results)
                else:
                    return np.vstack(results)

            return results
        
        return decorated
    
    return decorator

@batch(20)
def distance_between(midpoint_addrs):
    """
    Measure the distance between the fixed `endpoint_addrs` and specified `midpoint_addrs`.

    Returns a NumPy array with one row for each midpoint address, and one column for each endpoint address.
    """

    data = gmaps.distance_matrix(endpoint_addrs, midpoint_addrs)

    results = np.zeros((len(endpoint_addrs), len(midpoint_addrs)))
    results[:, :] = np.nan

    if 'status' not in data or data['status'] != 'OK':
        warnings.warn('API call failed.')
        return results

    for i, endpoint_addr in enumerate(endpoint_addrs):
        for j, midpoint_addr in enumerate(midpoint_addrs):
            try:
                results[i, j] = data['rows'][i]['elements'][j]['distance']['value']
            except (KeyError, TypeError) as exc:
                warnings.warn('Could not find distance between `{0}` and `{1}`.'.format(endpoint_addr, midpoint_addr))
                traceback.print_exc()

    return results.transpose()

# build a list of distance from home/work to each place
distances = distance_between(spreadsheet.address.values)

# copy the lists into table
spreadsheet['distance from home'] = distances[:, 0]
spreadsheet['distance from work'] = distances[:, 1]

# add a column for the combined distance
spreadsheet['combined distance'] = spreadsheet['distance from home'] + spreadsheet['distance from work']

# sort by lowest combined distance
spreadsheet = spreadsheet.sort_values('combined distance')

# save the result
out_filename = os.path.splitext(filename)[0] + '_sorted.csv'
spreadsheet.to_csv(out_filename, index=False)

print('Done! Please see', out_filename, 'for the results.')
