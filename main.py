# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:17:26 2022

@author: chentir
"""
#import datetime
#import os
#import csv
#import glob
#import pandas as pd
from matplotlib.pyplot import plot
from matplotlib.pyplot import show
from Get_address import Initialize_Device_Addresses, Get_Tsl_Address, Get_Mpm_Address, Get_Dev_Address
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
    setting_tsl_sweep_params(tsl)


    # If there is an MPM, then create instance of ILSTS
    if mpm.address != None:
        ilsts = sts.StsProcess(tsl,mpm,dev)

        ilsts.set_selected_channels(mpm)
        ilsts.set_selected_ranges(mpm)

        ilsts.set_data_struct()
        ilsts.set_parameters()
        print('Connect for Reference measurement and press ENTER')
        print('Reference process:')
        ilsts.sts_reference(mpm)
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

        ilsts.sts_save_meas_data('test.csv')

main()
