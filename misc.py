import os
from datetime import datetime
import json

file_last_scan_params = "last_scan_params.json" 
file_measurement_data_results = "test.csv" 

def check_and_load_previous_param_data(self, file_last_scan_params):
    '''If a file for a previous scan exists, then ask the user if it should be used to load ranges, channels,  previous reference data etc.'''
    if (os.path.exists(file_last_scan_params) == False):
        return 
    
    print('Would you like to load the most recent settings and reference data from {}? [y|n]'.format(file_last_scan_params))
    ans = input()
    if ans not in 'Yy':
        return

    #load the json data.
    with open(file_last_scan_params) as json_file:
        previous_settings = json.load(json_file)

    return previous_settings


check_and_load_previous_param_data(None, file_last_scan_params)