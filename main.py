# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:17:26 2022

@author: chentir
"""
#import datetime
import os
from datetime import datetime
import json
from tkinter import N
#import csv
#import glob
#import pandas as pd
#from matplotlib.pyplot import plot
#from matplotlib.pyplot import show
from Get_address import Initialize_Device_Addresses, Get_Tsl_Address, Get_Mpm_Address, Get_Dev_Address
import sts_process as sts
from tsl_instr_class import TslDevice
from mpm_instr_class import MpmDevice
from dev_intr_class import SpuDevice


file_last_scan_params = "last_scan_params.json" 
file_last_scan_reference_json = "last_scan_reference_data.json" 
file_measurement_data_results = "data_measurement.csv" 
file_reference_data_results = "data_reference.csv" 

def setting_tsl_sweep_params(connected_tsl: TslDevice, previous_param_data):
    """
    Setting sweep parameters. Will ask for:

        startwave:  Starting wavelength (nm)
        stopwave:   Stopping wavelength (nm)
        step:       Sweep step (pm)
        speed:      Sweep speed (nm/sec).
                    In case of TSL-570, the code will prompt
                    invite to select a speed from a list.
        power:      Output power (dBm)

    These arguments will be passed to the connected_tsl object.

    Args:
        connected_tsl (TslDevice): Instanciated TSL class.

    Returns:
        None
    """

    if (previous_param_data is not None):
        startwave = float(previous_param_data["startwave"])
        stopwave = float(previous_param_data["stopwave"])
        step = float(previous_param_data["actual_step"]) #The saved "step" is in pm, but we need nm.
        speed = float(previous_param_data["speed"])
        power = float(previous_param_data["power"])

        print('Start Wavelength (nm): ' + str(startwave))
        print('Stop Wavelength (nm): ' + str(stopwave))
        print('Sweep Step (nm): ' + str(step)) #nm, not pm.
        print('Sweep Speed (nm): ' + str(speed))
        print('Output Power (nm): ' + str(power))

    else:
        print('Input Start Wavelength (nm):')
        startwave = float(input())
        print('Input Stop Wavelength (nm):')
        stopwave = float(input())
        print('Input Sweep Step (pm):')
        step = float(input())/1000

        if connected_tsl.get_550_flag() is True:
            print('Input Sweep Speed (nm/sec):')
            speed = float(input())
        else:
            print('Select sweep speed (nm/sec):')
            num = 1
            for i in connected_tsl.get_sweep_speed_table():
                print(str(num)+'- '+str(i))
                num += 1
            speed = connected_tsl.get_sweep_speed_table()[int(input())-1]

        print('Input Output Power (dBm):')
        power = float(input())
        while power > 10:
            print('Invalid value of Output Power (<=10 dBm)')
            print('Input Output Power (dBm):')
            power = float(input())

    #Now that we have our parameters, set them on the TSL.
    # TSL Power setting
    connected_tsl.set_power(power)

    connected_tsl.set_sweep_parameters(startwave, stopwave, step, speed)

    return None


def prompt_and_get_previous_param_data(file_last_scan_params):
    '''If a file for a previous scan exists, then ask the user if it should be used to load ranges, channels,  previous reference data etc.'''
    if (os.path.exists(file_last_scan_params) == False):
        return None
    
    print('Would you like to load the most recent parameter settings from {}? [y|n]'.format(file_last_scan_params))
    ans = input()
    if ans not in 'Yy':
        return None

    #load the json data.
    with open(file_last_scan_params) as json_file:
        previous_settings = json.load(json_file)

    return previous_settings


def sts_save_param_data(file_last_scan_params: str, tsl: TslDevice, ilsts: sts.StsProcess):
    sts_rename_old_file(file_last_scan_params)

    #create a psuedo object for our array of STSDataStruct (self.ref_data)
    jsondata = {
        "selected_chans" : ilsts.selected_chans,
        "selected_ranges" : ilsts.selected_ranges,
        "startwave" :tsl.startwave,
        "stopwave" :tsl.stopwave,
        "step" :tsl.step,
        "speed" :tsl.speed,
        "power" :tsl.power, #only really used on the TSL, and not on the mpm or spu.
        "actual_step" :tsl.actual_step,
    }

    if (ilsts is not None):
        jsondata['selected_chans'] = ilsts.selected_chans
        jsondata['selected_ranges'] = ilsts.selected_ranges

    #save several of our data structure properties. 
    with open(file_last_scan_params, 'w') as exportfile:
        json.dump(jsondata, exportfile) #an array
    
    return None

def sts_save_reference_json_data(file_last_scan_reference_json):
    sts_rename_old_file(file_last_scan_reference_json)

    with open(file_last_scan_reference_json, 'w') as exportfile:
        json.dump(ilsts._reference_data_array, exportfile) #an array
    
    return None


#def rename_previous_log_files():
#    filearray = [file_last_scan_params, file_last_scan_reference_json, file_measurement_data_results, file_reference_data_results ]
#    for thisfilename in filearray:
#        sts_rename_old_file(thisfilename)

def sts_rename_old_file(filename: str):
    if (os.path.exists(filename)):
        timenow = datetime.now()
        os.rename(filename, timenow.strftime("%Y%m%d_%H%M%S") + "_" + filename )
    
    return None



def prompt_and_get_previous_reference_data():
    '''Ask the user if they want to use the previous reference data (if it exists). If so, then load it. '''

    if (os.path.exists(file_last_scan_reference_json) == False):
        return None

    print("Would you like to use the most recent reference data from file '{}'? [y|n]".format(file_last_scan_reference_json))
    ans = input()
    if ans not in 'Yy':
        return None

        #load the json data.
    with open(file_last_scan_reference_json) as json_file:
        previous_reference = json.load(json_file)

    return previous_reference

def main():
    """
    tsl_address = Get_Tsl_Address()
    mpm_address = Get_Mpm_Address()
    dev_address = Get_Dev_Address()

    interface = 'GPIB'
    # only connect to the devices that the user wants to connect to
    if tsl_address != None:
        tsl = TslDevice(interface, tsl_address)
        tsl.connect_tsl()
    else:
        # Shouldn't this exception be in TSL class?
        raise Exception("There must be a TSL connected")

    if mpm_address != None:
        mpm = MpmDevice(interface, mpm_address)  # for now, just do one MPM only
        mpm.connect_mpm()

    if dev_address != None:
        dev = SpuDevice(dev_address)
        dev.connect_spu()

    """

    global tsl, mpm, dev, ilsts

    Initialize_Device_Addresses()
    tsl_address = Get_Tsl_Address()
    mpm_address = Get_Mpm_Address()
    dev_address = Get_Dev_Address()
    interface = 'GPIB'
    #only connect to the devices that the user wants to connect to
    if tsl_address != None:
        tsl = TslDevice(interface, tsl_address)
        tsl.connect_tsl()
    else:
        raise Exception ("There must be a TSL connected")

    if mpm_address != None:
        mpm = MpmDevice(interface, mpm_address)
        mpm.connect_mpm()

    if dev_address != None:
        dev = SpuDevice(dev_address)
        dev.connect_spu()

    # Set the TSL properties
    previous_param_data = prompt_and_get_previous_param_data(file_last_scan_params) #might be empty, if there is no data, or if the user chose to not load it.
    setting_tsl_sweep_params(tsl, previous_param_data) #previous_param_data might be none

    # If there is an MPM, then create instance of ILSTS
    if mpm.address != None:
        ilsts = sts.StsProcess(tsl,mpm,dev)

        ilsts.set_selected_channels(previous_param_data)
        ilsts.set_selected_ranges(previous_param_data)

        ilsts.set_data_struct() # will automatically use either newly-input data, or saved data from the previous_param_data.
        ilsts.set_parameters() # will automatically use either newly-input data, or saved data from the previous_param_data.

        #Determine if we should load reference data
        previous_ref_data_array = prompt_and_get_previous_reference_data() #trigger, monitor, and logdata. Might be null if the user said no, or the file didn't exist.
        if (previous_ref_data_array is not None):
            ilsts._reference_data_array = previous_ref_data_array #ensures that we always have an array, empty or otherwise.
        
        if (len(ilsts._reference_data_array) == 0):
            
            print('Connect for Reference measurement and press ENTER')
            print('Reference process:')
            ilsts.sts_reference()

        else:
            #Load the reference data from file. 
            print("Loading reference data...")
            ilsts.sts_reference_from_saved_file() #loads from the cached array reference_data_array which is a property of ilsts


        
        #Perform the sweeps
        ans = 'y'
        while ans in 'yY':
            print('DUT measurement:')
            print('Input repeat count:')
            reps = int(input())
            print('Connect DUT and press ENTER')
            input() 
            for _ in range(reps):
                ilsts.sts_measurement()
                #plot(ilsts.wavelengthtable,ilsts.il)
                #show()
            print ('Redo? (y/n)')
            ans = input()

        
        print ("Saving measurement data file '" + file_measurement_data_results + "'...")
        ilsts.sts_save_meas_data(file_measurement_data_results)

        print ("Saving reference json file '" + file_last_scan_reference_json + "'...")
        sts_save_reference_json_data(file_last_scan_reference_json)

        print ("Saving reference csv data file '" + file_reference_data_results + "'...")
        print ("(not implemented yet...")
        #ilsts.sts_save_meas_data(file_measurement_data_results)

    #Save the parameters, whether we have an MPM or not. But only if there is no save file, or the user just set new settings.
    if (previous_param_data is None):
        print ("Saving parameter file '" + file_last_scan_params + "'...")
        sts_save_param_data(file_last_scan_params, tsl, ilsts) #ilsts might be None

main()
