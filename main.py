# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:17:26 2022

@author: chentir
"""
# %% import packages
#import datetime
#import os
#import csv
#import glob
#import pandas as pd
#from matplotlib.pyplot import plot
from Get_address import Initialize_And_Get_Device, Get_Tsl_Address, Get_Mpm_Address, Get_Dev_Address
import sts_process as sts
from tsl_instr_class import TslDevice
from mpm_instr_class import MpmDevice
from dev_intr_class import SpuDevice


def setting_tsl_sweep_params(connected_tsl: TslDevice):
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

    # TSL Power setting
    connected_tsl.set_power(power)

    connected_tsl.set_sweep_parameters(startwave, stopwave, step, speed)

    return None

def main():
    # %% Initiallization
    # TODO: Rework to include GPIB, USB and LAN connection #WARNING: TSL-550/710 do not accept LAN and USB connection
    #Initialize_Device_Addresses()

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

    tsl = Initialize_And_Get_Device(str(TslDevice))
    tsl.connect_tsl()

    if tsl is None:
        return None #quit the app 
    

    #prompt if we need an MPM
    print("Would you like to connect an MPM? [Y]es [N]o")
    answer = input()
    if answer in "Yy":
        mpm = Initialize_And_Get_Device(str(MpmDevice))
        mpm.connect_mpm()

        dev = Initialize_And_Get_Device(str(SpuDevice))
        dev.connect_spu()

    # If there is a TSL an MPM, then the max power should be 10. Otherwise, no limit. #DONE @ Line 38

    # Set the TSL properties
    setting_tsl_sweep_params(tsl)


    # If there is an MPM, then ask for the ranges and channels
    if mpm_address != None:
        # prompt user for channels and ranges.THese two methods will be in sts_process.py
        ilsts = sts.StsProcess(tsl,mpm,dev)

        ilsts.set_selected_channels(mpm)
        ilsts.set_selected_ranges(mpm)

        ilsts.set_data_struct()
        ilsts.set_parameters()
        print('Reference process:')
        ilsts.sts_reference(mpm)
        print('DUT measurement:')
        ilsts.sts_measurement()
        ilsts.sts_save_meas_data('Z:\\Santec_IL_STS\\test.csv')


    # def PromptUserToTakeReferenceAndCreateDataStructure():
        # prompt user about how to get reference data.
        # 1. take new reference,
        # 2. load previous reference,
        # 3. prompt user to cancel
        # 3. take no reference? maybe ignore this entirely and force user to do 1 or 2
        # prompt user to get channels
        # prompt user to get ranges

        # create data structure
        # do ref scan


    # newDevice = TSL_Device()
    # newDevice.setWaveLength(1600)
    # newDevice._wavelength = 333 #cant do this
    # newVar = newDevice._wavelength


main()