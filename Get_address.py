# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 11:24:04 2020

@author: chentir
"""
#from readline import append_history_file
#import this

#from platformdirs import user_log_path
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


def get_interface_devices(interface_type: str, device_type: str):
    #Get all found devices on this interface. If LAN, then ask for the IP address.
    #[1]. GPIB, [2]. LAN, [3]. USB")

    list_of_found_devices = []

    if device_type == str(SpuDevice):
        #We dont care about the interface type, just get the list of items from NIMax
       list_of_found_devices = get_interface_devices_daq_spu()
    elif (interface_type == '1'):
        #scan all GPIB ports and get all devices
        list_of_found_devices = get_interface_devices_gpib()
    elif (interface_type == '2'):
        #Prompt the user for their desired IP address. And then return a single array with a single object
        list_of_found_devices = get_single_ethernet_device_array(device_type) #it's one single device in an array
    elif (interface_type == '3'):
        #scan all USB ports and get all devices
        raise Exception ("Not Implemented Exception")
        #The InstrumentDLL method Get_USB_Resouce() within MainCommunication will return a string array of devices
    else:
        raise Exception ("Bad interface number " + interface_type)

    return list_of_found_devices

def get_interface_devices_gpib():
    
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
    
def get_single_ethernet_device_array(device_type: str):
    
    print("###################################################################")
    print("Present GPIB instruments: ")

    list_of_found_devices = []
 
    print("Enter the IP address")
    user_ip = input()

    if (device_type == str(MpmDevice)):
        int_user_port = 5000
    else:
        int_user_port = 0
        str_port_prompt = "Enter the port number between 1 and 65536, or press enter to use the default port number of 5000"
        print(str_port_prompt)
        str_user_port = input()
        if str_user_port == "" or None:
            int_user_port = 5000

        while int_user_port <= 0 or int_user_port > 65536:
            print ("Invalid port number")
            print (str_port_prompt)
            str_user_port = input()
            if str_user_port == "" or None:
                str_user_port = "5000"

            try:
                int_user_port = int(str_user_port)
            except:
                pass
                #do nothing.

    thisObj = DeviceObject()
    thisObj.index = 0
    thisObj.interface = "LAN"
    thisObj.fulladdress = user_ip
    thisObj.address = user_ip
    thisObj.port = int_user_port
    list_of_found_devices.append(thisObj)

    return list_of_found_devices #just one device in the array
    
def get_interface_devices_daq_spu():
    list_of_found_devices = []
    #for i in system.devices.device_names:
    for i in range(len(system.devices.device_names)):
        thisObj = DeviceObject()
        thisObj.index = i
        thisObj.address = system.devices.device_names[i] #the device name is the same as the address
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
    interface = None

    #Get the interfact (USB, GPIB) if its a TSL or MPM. We ignore DAQ boards here.
    if device_type != str(SpuDevice):
        interface = get_selected_interface(device_type)

    #they selected the interface, like USB or something. So get all of the connected devices.
    #unless its a DAQ board, which will ignore the null interface and just get a list of DAQ boards
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
        
        prompt_list_of_devices = 'Select the index of the device that you would like to use' + "\r\n"
        for found_device in list_of_found_devices:
            prompt_list_of_devices += "[" + str(found_device.index) + "] " + found_device.fulladdress  + "\r\n"
        
        print(prompt_list_of_devices)

        selected_device_index = input()
        
        #make sure that the user selected one of the item indexes in our list
        while selected_device_index not in [str(x.index) for x in list_of_found_devices]:
            print("'" + selected_device_index + "' was not a valid selection.")
            print(prompt_list_of_devices)
            selected_device_index = input()

    #get the string interface and the address from the selected device
    address = list_of_found_devices[selected_device_index].address
    if device_type != str(SpuDevice):
        interface = list_of_found_devices[selected_device_index].interface
        port = list_of_found_devices[selected_device_index].port

    print('Using device {} - {}.'.format(selected_device_index,address))
    print("Enter [Y]es to proceed, or [N]o to cancel")
    proceedyesno = input()
    if proceedyesno not in "Yy":
        return None
        
    returnObj = None

    if (device_type == str(TslDevice)):
        returnObj = TslDevice(interface, address, port)
    if (device_type == str(MpmDevice)):
        returnObj = MpmDevice(interface, address, port)
    if (device_type == str(SpuDevice)):
        returnObj = SpuDevice(address) #this is actually the name

    if (returnObj is None):
        raise Exception ("Failed to create a TSL, MPM, or SPU device")
        #TODO: if we ask to rescan and reselect again, re-call this same method. Low priority since this should be rare

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

def get_dict_of_interfaces_for_this_device(device_type:str):

    #{1:"GPIB", 2:"LAN", 3:"USB"}
    if (device_type == str(TslDevice)):
        return {"1":"GPIB", "2":"LAN", "3":"USB"}
    if (device_type == str(MpmDevice)):
        return {"1":"GPIB", "2":"LAN"}
    
    return None #For daq boards, this is empty

def get_selected_interface(device_type:str):
    #prompt the user to select an interface.
    dict_of_interfaces:dict = get_dict_of_interfaces_for_this_device(device_type)

    if (dict_of_interfaces is None):
        raise Exception("daq board, not implemented")

    prompt_string = "Select the interface for this device: "
    for this_key_index in dict_of_interfaces:
        prompt_string += "[" + str(this_key_index) + "]. " + dict_of_interfaces[this_key_index]

    print(prompt_string)
    interface = input()
    while interface not in dict_of_interfaces.keys():
        print('Incorrect interface selection. Only enter a number')
        prompt_string
        interface = input()

    return interface