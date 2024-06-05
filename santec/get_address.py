# -*- coding: utf-8 -*-

"""
Created on Fri Feb 28 11:24:04 2020

@author: chentir
@organization: santec holdings corp.
"""

# Basic imports
import time

# Importing pyvisa and nidaqmx -> to control TSL and MPM, and DAQ device
import pyvisa
import nidaqmx

# Initializing pyvisa resource manager class
resource_manager = pyvisa.ResourceManager()

# Getting a list of all detected instruments
resources = resource_manager.list_resources()

# Getting a list of all detected DAQ devices
system = nidaqmx.system.System.local()


class GetAddress:
    def __init__(self):
        """ Initializing TSL, MPM and DAQ objects """
        self.__cached_TSL_Address = None
        self.__cached_MPM_Address = None
        self.__cached_DAQ_Address = None

    @staticmethod
    def Connection_Info_Class():
        """
        Instruments attributes
        """
        GPIB_address: int
        IPAddress: str
        USB_Address: str
        Port: int

    def Get_Tsl_Address(self):
        """
        Initialized TSL instrument
        """
        if self.__cached_TSL_Address is None:
            self.Initialize_Device_Addresses()
        return self.__cached_TSL_Address

    def Get_Mpm_Address(self):
        """
        Initialized MPM instrument
        """
        if self.__cached_MPM_Address is None:
            self.Initialize_Device_Addresses()
        return self.__cached_MPM_Address

    def Get_Dev_Address(self):
        """
        Initialized DAQ device
        """
        if self.__cached_DAQ_Address is None:
            self.Initialize_Device_Addresses()
        return self.__cached_DAQ_Address

    def Initialize_Device_Addresses(self, mode: str = ""):
        """
        Each device needs to prompt for a different connection type
        Returns
        -------
        TSL : str
            DESCRIPTION.
        OPM : str
            DESCRIPTION.
        DAQ : str
            DESCRIPTION.

        """
        # Initializing an empty dictionary
        devices = {'Name': [], 'Resource': []}

        # Gets and sorts GPIB connections only
        resource_tools = [i for i in resources if 'GPIB' in i]

        # Open the resources from the resource tools list and filter out SANTEC instruments only
        # Append the resource and teh instrument idn to devices dictionary
        for resource in resource_tools:
            try:
                resource_idn = resource_manager.open_resource(resource).query("*IDN?")
                if 'SANTEC' in resource_idn:
                    devices['Name'].append(resource_idn)
                    devices['Resource'].append(resource)
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")

        # Zipping devices dictionary 'Name' and 'Resource' into a list
        devices_list = list(zip(devices['Name'], devices['Resource']))

        # Sorting the devices list in order from TSL to MPM instruments
        devices_list = sorted(devices_list, key=lambda x: x[0].startswith('SANTEC,MPM'))

        # Unzipping the sorted devices list and assigning key & values of devices dictionary
        devices['Name'], devices['Resource'] = zip(*devices_list)

        # Prints all the detected SANTEC GPIB instruments in order of TSL to MPM
        print("Present GPIB Instruments: ")
        for i in range(len(devices['Name'])):
            print(i + 1, ": ", devices['Name'][i])

        if mode == 'SME':
            # Prints all the detected DAQ devices
            print("Detected DAQ devices: ")
            for i in system.devices.device_names:
                print(system.devices.device_names.index(i) + 1 + len(devices['Name']), ": ", i)

        time.sleep(0.2)

        # User laser instrument selection
        selection = int(input("\nSelect Laser instrument: "))
        selected_resource = devices['Resource'][selection - 1]
        # connect GPIB into a buffer
        buffer = resource_manager.open_resource(selected_resource)
        # buffer.read_termination = "\r\n"
        # set the TSL to CRLF delimiter
        buffer.write('SYST:COMM:GPIB:DEL 2')
        TSL = buffer.resource_name

        # User power meter instrument selection
        selection = int(input("Select Power meter: "))
        selected_resource = devices['Resource'][selection - 1]
        # connect GPIB into a buffer
        buffer = resource_manager.open_resource(selected_resource)
        # buffer.read_termination = "\r\n"
        OPM = buffer.resource_name

        DAQ = None
        if mode == 'SME':
            # User daq device selection
            selection = input("Select DAQ board: ")
            DAQ = system.devices[int(selection) - 1 - len(devices['Name'])].name

        # Assigning all the user selected instruments
        self.__cached_TSL_Address = TSL
        self.__cached_MPM_Address = OPM

        if mode == 'SME':
            self.__cached_DAQ_Address = DAQ

        return None
