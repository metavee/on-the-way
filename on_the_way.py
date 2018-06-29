"""
Sort a CSV of addresses by the amount of detour they would add to an existing route.
"""


import argparse
import os
import sys
import warnings
import traceback

import googlemaps
import numpy as np
import pandas as pd
from tqdm import tqdm


secret_api_key = os.environ.get('GMAPS_API_KEY', '')
if not secret_api_key:
    print('Please set an API key for the Google Maps Distance Matrix APi in the environment variable `GMAPS_API_KEY`.')


gmaps = googlemaps.Client(key=secret_api_key)


def main(start_addr, end_addr, filename):

    spreadsheet = pd.read_csv(filename)
    if 'address' not in spreadsheet.columns:
        raise ValueError('CSV file must have an `address` column.')

    endpoint_addrs = [start_addr, end_addr]

    # build a list of distance from start/end to each place
    distances = distance_between(spreadsheet.address.values, endpoint_addrs)

    # copy the lists into table
    spreadsheet['distance from start'] = distances[:, 0]
    spreadsheet['distance from end'] = distances[:, 1]

    # add a column for the combined distance
    spreadsheet['combined distance'] = spreadsheet['distance from start'] + spreadsheet['distance from end']

    # sort by lowest combined distance
    spreadsheet = spreadsheet.sort_values('combined distance')

    # save the result
    out_filename = os.path.splitext(filename)[0] + '_sorted.csv'
    spreadsheet.to_csv(out_filename, index=False)

    print('Done! Please see', out_filename, 'for the results.')


def batch(size):
    """
    Decorator for functions of type list[n] -> list[n]

    Splits up the input into chunks of size <= `size`, calls the function separately, and stitches together the output.
    """

    def decorator(fxn):
        def decorated(arg, *args, **kwargs):
            start_indices = list(range(0, len(arg), size))
            results = []
            for i in tqdm(start_indices):
                results.append(fxn(arg[i:i+size], *args, **kwargs))

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
def distance_between(midpoint_addrs, endpoint_addrs):
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('START_ADDRESS', type=str, help='Start address on the fixed route.')
    parser.add_argument('END_ADDRESS', type=str, help='End address on the fixed route.')
    parser.add_argument('CSV_FILE', type=str, help='Path to CSV file with address column.')

    args = parser.parse_args()
    main(args.START_ADDRESS, args.END_ADDRESS, args.CSV_FILE)
