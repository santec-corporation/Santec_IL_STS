# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 11:24:04 2020

@author: chentir
"""
from mpm_instr_class import MpmDevice
import pyvisa
import nidaqmx
from tsl_instr_class import TslDevice
from dev_intr_class import SpuDevice

rm=pyvisa.ResourceManager()
listing=rm.list_resources() #creat a list of all detected connections
system=nidaqmx.system.System.local()

_cached_Tsl_Address = None
_cached_MPM_Address = None
_cached_Dev_Address = None

class DeviceObject(object):
    pass

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

def get_interface_devices(interface_type: str, device_type: str):
    #Get all found devices on this interface. If LAN, then ask for the IP address.
    #[1]. USB, [2]. GPIB, [3]. LAN")

    list_of_found_devices = []

    if (interface_type == '1'):
        #scan all USB ports and get all devices
        raise Exception ("Not Implemented Exception")
    elif (interface_type == '2'):
        #scan all GPIB ports and get all devices
        list_of_found_devices = get_interface_devices_gpib(interface_type, device_type)
    elif (interface_type == '3'):
        #Prompt the user for their desired IP address. And then return a single array with a single object
        raise Exception ("Not Implemented Exception")
    else:
        raise Exception ("Bad interface number " + interface_type)

    return list_of_found_devices

def get_interface_devices_gpib(interface_type: int, device_type: str):
    
    print("###################################################################")
    print("Present GPIB instruments: ")

    list_of_found_devices = []
 
    #list all GPIB devices found, including TSL, MPM, or others
    tools=[i for i in listing if 'GPIB' in i] #select only GPIB connections
    for i in range(len(tools)):
        #connect GPIB into a buffer
        buffer=rm.open_resource(tools[i], read_termination='\r\n')
        print(i+1,": ",buffer.query('*IDN?'))
        thisObj = DeviceObject()
        thisObj.index = i
        thisObj.interface = "GPIB"
        thisObj.fulladdress = tools[i]
        thisObj.address = tools[i].split('::')[1]
        thisObj.port = 5000
        list_of_found_devices.append(thisObj)

    return list_of_found_devices
    


#def Initialize_Device_Addresses() :
def Initialize_And_Get_Device(device_type:str) : 
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

    print("Select the interface for this device: [1]. USB, [2]. GPIB, [3]. LAN")
    interface = input()
    while interface != '1' and interface != '2' and  interface != '3' :
        print('Incorrect interface selection. Only enter a number')
        print("Select the interface for this device: 1. USB, 2. GPIB, 3. LAN")
        interface = input()

    list_of_found_devices = get_interface_devices(interface, device_type)


    #Each device has:
    #   a) an interface type that is either LAN, USB, or GPIB (not an int)
    #   b) an address
    #   c) a port
    #In the case of LAN, this is a single object within an array, that has an IP and a port.
    selected_device_index = 0
    if(len(list_of_found_devices) > 1): #if LAN, there would only be one device. So no need to ask again.
        #TODO: loop through list_of_found_devices and if there is more than 1 in the array, then ask the user
        # which one that they want to use
        print('select your favorite device from the list of list_of_found_devices')
        selected_device_index = input()
        raise Exception ("not implemented")
    

    #get the string interface and the address from the selected device
    interface = list_of_found_devices[selected_device_index].interface
    address = list_of_found_devices[selected_device_index].address
    port = list_of_found_devices[selected_device_index].port

    print('Using device ' + selected_device_index + address )

    returnObj = None

    if (device_type == str(TslDevice)):
        returnObj = TslDevice(interface, address, port)
    if (device_type == str(MpmDevice)):
        returnObj = MpmDevice(interface, address, port)
    if (device_type == str(SpuDevice)):
        returnObj = SpuDevice(address) #this is actually the name

    if (returnObj is None):
        raise Exception ("cannot return a None object...fix me")
        #if we ask to rescan and reselect again, re-call this same method

    return returnObj



""" I might need to be deleted...

#def Initialize_Device_Addresses() :
def Initialize_And_Get_Device(device_type:str) : 
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

    #select the interface for the light source
    
    print("Select light source")
    print("Select the interface for this device: [1]. USB, [2]. GPIB, [3]. LAN")
    interface = input()
    while interface != '1' and  interface != '2' and  interface != '3' :
        print('Incorrect interface selection. Only enter a number')
        print("Select the interface for this device: 1. USB, 2. GPIB, 3. LAN")
        interface = input()

    list_of_found_devices = get_interface_devices(interface)

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
"""