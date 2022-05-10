# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 11:24:04 2020

@author: chentir
"""
import pyvisa
import nidaqmx

rm=pyvisa.ResourceManager()
listing=rm.list_resources() #creat a list of all detected connections
system=nidaqmx.system.System.local()

_cached_Tsl_Address = None
_cached_MPM_Address = None
_cached_Dev_Address = None

def Connection_Info_Class():
    GPIB_address: int
    IPAddress: str
    USB_Address: str
    Port: int


def Get_Tsl_Address():
    if _cached_Tsl_Address == None :
        Initialize_Device_Addresses()
    return _cached_Tsl_Address


def Get_Mpm_Address():
    if _cached_MPM_Address == None :
        Initialize_Device_Addresses()
    return _cached_MPM_Address


def Get_Dev_Address():
    if _cached_Dev_Address == None :
        Initialize_Device_Addresses()
    return _cached_Dev_Address

def Initialize_Device_Addresses():
    """_summary_

    Returns:
        _type_: _description_
    """
    '''

    #each device needs to prompt for a different connection type
    Returns
    -------
    TSL : str
        DESCRIPTION.
    OPM : str
        DESCRIPTION.
    Dev : str
        DESCRIPTION.

    '''
    global _cached_Tsl_Address, _cached_MPM_Address, _cached_Dev_Address
    print("###################################################################")
    print("Present GPIB instruments: ")
    tools=[i for i in listing if 'GPIB' in i] #select only GPIB connections
    for i in range(len(tools)):
        #connect GPIB into a buffer
        buffer=rm.open_resource(tools[i], read_termination='\r\n')
        print(i+1,": ",buffer.query('*IDN?'))
    print('')
    print("Detected DAQ boards: ")
    for i in system.devices.device_names:
        print (system.devices.device_names.index(i)+1+len(tools),": ",i)
    print("###################################################################")
    print("")
    print("Select light source")
    selection=input()
    #connect GPIB into a buffer
    buffer=rm.open_resource(tools[int(selection)-1], read_termination='\r\n')
    #set the TSL to CRLF delimiter
    buffer.write('SYST:COMM:GPIB:DEL 2')
    TSL=buffer.resource_name
    print("Select power meter")
    selection=input()
    #connect GPIB into a buffer
    buffer=rm.open_resource(tools[int(selection)-1], read_termination='\r\n')
    OPM=buffer.resource_name
    print("Select DAQ board")
    selection=input()
    Dev=system.devices[int(selection)-1-len(tools)].name

    _cached_Tsl_Address = TSL
    _cached_MPM_Address = OPM
    _cached_Dev_Address = Dev

    return None
    