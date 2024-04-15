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
listing = resource_manager.list_resources()

# Getting a list of all detected DAQ devices
system = nidaqmx.system.System.local()


class GetAddress:
    def __init__(self):
        """Initializing TSL, MPM and DAQ objects"""
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

    def Initialize_Device_Addresses(self):
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
        tools = [i for i in listing if 'GPIB' in i]  # Gets and sorts GPIB connections only

        print("Present GPIB Instruments: ")
        for i in range(len(tools)):
            # Connect GPIB into a buffer
            try:
                buffer = resource_manager.open_resource(tools[i])
                # buffer.read_termination = "\r\n"
                print(i + 1, ": ", buffer.query('*IDN?'))

            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")

        print("Detected DAQ devices: ")
        for i in system.devices.device_names:
            print(system.devices.device_names.index(i) + 1 + len(tools), ": ", i)

        time.sleep(0.5)

        selection = input("\nSelect Laser instrument: ")

        # connect GPIB into a buffer
        buffer = resource_manager.open_resource(tools[int(selection) - 1])
        # buffer.read_termination = "\r\n"

        # set the TSL to CRLF delimiter
        buffer.write('SYST:COMM:GPIB:DEL 2')
        TSL = buffer.resource_name

        selection = input("Select Power meter: ")
        # connect GPIB into a buffer
        buffer = resource_manager.open_resource(tools[int(selection) - 1])

        # buffer.read_termination = "\r\n"
        OPM = buffer.resource_name

        selection = input("Select DAQ board: ")
        DAQ = system.devices[int(selection) - 1 - len(tools)].name

        self.__cached_TSL_Address = TSL
        self.__cached_MPM_Address = OPM
        self.__cached_DAQ_Address = DAQ

        return None