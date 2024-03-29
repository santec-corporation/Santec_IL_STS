# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:17:26 2022

@author: chentir
"""
import os
import json
from matplotlib.pyplot import plot, show
from Get_address import Initialize_Device_Addresses, Get_Tsl_Address, Get_Mpm_Address, Get_Dev_Address
import sts_process as sts
import file_logging as file_logging
from tsl_instr_class import TslDevice
from mpm_instr_class import MpmDevice
from dev_intr_class import SpuDevice

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
        step = float(previous_param_data["step"]) #step is .001, but step is .1. we need the nm value.
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

def prompt_and_get_previous_reference_data():
    '''Ask the user if they want to use the previous reference data (if it exists). If so, then load it. '''

    if (os.path.exists(file_logging.file_last_scan_reference_json) == False):
        return None

    print("Would you like to use the most recent reference data from file '{}'? [y|n]".format(file_logging.file_last_scan_reference_json))
    ans = input()
    if ans not in 'Yy':
        return None

    #Get the file size. If its huge, then the load will freeze for a few seconds.
    intfilesize = int(os.path.getsize(file_logging.file_last_scan_reference_json))
    if intfilesize > 1000000:
        strfilesize = str(int(intfilesize / 1000 / 1000)) + " MB"
    else:
        strfilesize = str(int(intfilesize / 1000)) + " KB"

    print ("Opening " + strfilesize + " file '" + file_logging.file_last_scan_reference_json + "'...")
    #load the json data.
    with open(file_logging.file_last_scan_reference_json) as json_file:
        previous_reference = json.load(json_file)

    return previous_reference

def main():
    """Main method of this project"""

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
    previous_param_data = prompt_and_get_previous_param_data(file_logging.file_last_scan_params) #might be empty, if there is no data, or if the user chose to not load it.
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
            reps = ""

            while reps.isnumeric() == False:
                print('Input repeat count, and connect the DUT and press ENTER:')
                reps = input()
                if reps.isnumeric() == False:
                    print('Invalid repeat count, enter a number.')

            for _ in range(int(reps)):
                print("Scan {} of {}...".format(str(_ + 1), reps))
                ilsts.sts_measurement()
                plot(ilsts.wavelengthtable,ilsts.il)
                show()
            print ('Redo? (y/n)')
            ans = input()


        print ("Saving measurement data file '" + file_logging.file_measurement_data_results + "'...")
        file_logging.save_meas_data(ilsts, file_logging.file_measurement_data_results)

        print ("Saving reference csv data file '" + file_logging.file_reference_data_results + "'...")
        file_logging.save_reference_result_data(ilsts, file_logging.file_reference_data_results)

        print ("Saving reference json file '" + file_logging.file_last_scan_reference_json + "'...")
        file_logging.save_reference_json_data(ilsts, file_logging.file_last_scan_reference_json)

    #Save the parameters, whether we have an MPM or not. But only if there is no save file, or the user just set new settings.
    if (previous_param_data is None):
        print ("Saving parameter file '" + file_logging.file_last_scan_params + "'...")
        file_logging.sts_save_param_data(tsl, ilsts, file_logging.file_last_scan_params) #ilsts might be None

main()
