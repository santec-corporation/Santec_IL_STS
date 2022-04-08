# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:17:26 2022

@author: chentir
"""
#%% import packages
import datetime
import os
import csv
import glob
import pandas as pd
from matplotlib.pyplot import plot
from Get_address import Initialize_Device_Addresses, Get_Tsl_Address, Get_Mpm_Address, Get_Dev_Address
import sts_process as sts
from tsl_instr_class import TslDevice
from mpm_instr_class import MpmDevice
from dev_intr_class import SpuDevice

def setting_tsl_sweep_params(connected_tsl: TslDevice):
    print('Input Start Wavelength (nm):')
    startwave = float(input())
    print('Input Stop Wavelength (nm):')
    stopwave = float(input())
    print('Input Sweep Step (pm):')
    step = float(input())/1000
    if tsl.get_550_flag() is True:
        print('Input Sweep Speed (nm/sec):')
        speed = float(input())
    else :
        print('Select sweep speed (nm/sec):')
        num = 1
        for i in tsl.get_sweep_speed_table():
            print(str(num)+'- '+str(i))
            num +=1
        speed = tsl.get_sweep_speed_table()[int(input())-1]

    print('Input Output Power (dBm):')
    power = float(input())
    while power>10:
        print('Invalid value of Output Power (<=10 dBm)')
        print('Input Output Power (dBm):')
        power = float(input())

    #TSL Power setting
    errorstr = tsl.set_power(power)
    
    errorstr = tsl.set_sweep_parameters(startwave, stopwave, step, speed)

#%% Initiallization
#TODO: put this in a try/catch
Initialize_Device_Addresses()
tsl_address = Get_Tsl_Address() #this prompts the user for interface and other stuff
opm_address = Get_Mpm_Address()
dev_address = Get_Dev_Address()

#only connect to the devices that the user wants to connect to
if tsl_address != None:
    tsl = TslDevice(interface, tsl_address)
    tsl.connect_tsl()
else:
    raise Exception ("There must be a TSL connected") #Shouldn't this exception be in TSL class?

if opm_address != None:
    opm = MpmDevice(interface, opm_address) #for now, just do one MPM only
    opm.connect_opm()

if dev_address != None:
    dev = SpuDevice(dev_address)
    dev.connect_dev()

#If there is a TSL an MPM, then the max power should be 10. Otherwise, no limit. #DONE @ Line 38

#Set the TSL properties
setting_tsl_sweep_params(tsl)


#If there is an MPM, then ask for the ranges and channels
if opm_address != None:
    #prompt user for channels and ranges.THese two methods will be in sts_process.py
    ilsts = sts.StsProcess()

    selected_channels = ilsts.channel_select(opm)
    selected_ranges = ilsts.selected_ranges(opm)
    ilsts.set_data_struct(selected_channels,selected_ranges)
    
    #The sts datastruct is then initialized in the sts_process.py file
    #prompt user to take a reference from the sts_process.py

    PromptUserToTakeReferenceAndCreateDataStructure





def PromptUserToTakeReferenceAndCreateDataStructure():
    #prompt user about how to get reference data.
        #1. take new reference,
        #2. load previous reference,
        #3. prompt user to cancel
        #3. take no reference? maybe ignore this entirely and force user to do 1 or 2
    #prompt user to get channels
    #prompt user to get ranges

    #create data structure
    #do ref scan



newDevice = TSL_Device()
newDevice.setWaveLength(1600)
newDevice._wavelength = 333 #cant do this
newVar = newDevice._wavelength
