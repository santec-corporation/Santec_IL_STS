# -*- coding: utf-8 -*-
from . import logger

"""
Get Instrument Addresses.
Connection modes: GPIB, LAN, USB(TSL).

@organization: Santec Holdings Corp.
"""

import os
import clr
import time
import pyvisa
import nidaqmx

# Import Santec communication class from Santec namespace
from Santec.Communication import MainCommunication


class GetAddress:
    _resource_manager = pyvisa.ResourceManager()    # Initializing pyvisa resource manager class
    _resources = _resource_manager.list_resources()     # Getting a list of all detected instruments
    _system = nidaqmx.system.System.local()     # Getting a list of all detected DAQ devices

    # Instrument attributes
    GPIB_address: int
    IPAddress: str
    USB_Address: str
    Port: int

    def __init__(self):
        """ Initializing TSL, MPM, and DAQ objects. """
        self.__cached_TSL_Address = None
        self.__cached_MPM_Address = None
        self.__cached_DAQ_Address = None
        self.is_disposed = False

    def get_tsl_address(self):
        """
        Initialized a TSL instrument
        """
        if self.__cached_TSL_Address is None:
            self.initialize_instrument_addresses()
        return self.__cached_TSL_Address

    def get_mpm_address(self):
        """
        Initialized MPM instrument
        """
        if self.__cached_MPM_Address is None:
            self.initialize_instrument_addresses()
        return self.__cached_MPM_Address

    def get_dev_address(self):
        """
        Initialized DAQ device
        """
        if self.__cached_DAQ_Address is None:
            self.initialize_instrument_addresses()
        return self.__cached_DAQ_Address

    def initialize_instrument_addresses(self,
                                        mode: str = ""):
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
        logger.info("Initializing Instrument Addresses")
        devices = {'Name': [], 'Resource': [], 'Interface': []}      # Initializing an empty dictionary of devices.

        logger.info("Getting GPIB resources")
        resource_tools = [i for i in self._resources if 'GPIB' in i]      # Gets and sorts GPIB connections only
        logger.info(f"Available GPIB resources: {resource_tools}")

        if len(resource_tools) > 0:
            # Open the resources from the resource tools list and filter out SANTEC instruments only
            # Append the resource and the instrument idn to devices dictionary
            for resource in resource_tools:
                try:
                    logger.info(f"Opening resource: {resource}")
                    resource_idn = self._resource_manager.open_resource(resource).query("*IDN?")
                    logger.info(f"Opened instrument: {resource_idn}")
                    if 'SANTEC' in resource_idn:
                        devices['Name'].append(resource_idn)
                        devices['Resource'].append(resource)
                        devices['Interface'].append("GPIB")
                except Exception as err:
                    logger.info(f"Error while opening resource: {resource}, {err}")
                    print(f"Unexpected error while opening resource: {err=}, {type(err)=}")

        # USB instruments
        logger.info("Getting USB resources")
        main_communication = MainCommunication()
        usb_resources = list(main_communication.Get_USB_Resouce())
        logger.info(f"Available USB resources: {usb_resources}")
        if len(usb_resources) > 0:
            for i in range(len(usb_resources)):
                usb_id = f"USB{i}"
                devices['Name'].append(usb_resources[i])
                devices['Resource'].append(usb_id)
                devices['Interface'].append("USB ")

        # Zipping devices dictionary 'Name' and 'Resource' into a list
        devices_list = list(zip(devices['Name'], devices['Resource'], devices['Interface']))

        if len(devices_list) > 0:
            # Sorting the device list in order from TSL to MPM instruments
            devices_list = sorted(devices_list, key=lambda x: x[0].startswith('SANTEC,MPM'))

            # Unzipping the sorted devices list and assigning key & values of device dictionary
            devices['Name'], devices['Resource'], devices['Interface'] = zip(*devices_list)

        # Prints all the detected SANTEC instruments in order of TSL to MPM
        print("Present Instruments: ")
        for i in range(len(devices['Name'])):
            print(i + 1, ": ", devices['Interface'][i], " | ", devices['Name'][i])

        if mode == 'SME':
            # Prints all the detected DAQ devices
            print("Detected DAQ devices: ")
            logger.info("Getting DAQ devices.")
            for i in self._system.devices.device_names:
                logger.info(f"Detected DAQ device: {i}")
                print(self._system.devices.device_names.index(i) + 1 + len(devices['Name']), ": ", i)

        if len(devices) == 0 and len(usb_devices) == 0:
            logger.critical("No TSL or MPM instruments connected!!")
            raise Exception("No TSL or MPM instruments connected!!")

        TSL = None
        OPM = None

        # User laser instrument selection
        selection = int(input("\nSelect Laser instrument: "))
        selected_resource = devices['Resource'][selection - 1]
        logger.info(f"Selected laser instrument: {selected_resource}")
        # Connect GPIB into a buffer
        logger.info(f"Opening laser instrument resource: {selected_resource}")
        try:
            buffer = self._resource_manager.open_resource(selected_resource)
            # buffer.read_termination = "\r\n"
            # set the TSL to CRLF delimiter
            buffer.write('SYST:COMM:GPIB:DEL 2')
            TSL = buffer.resource_name
            logger.info(f"Opened laser instrument: {TSL}")
        except Exception as err:
            logger.info(f"Error while opening resource: {selected_resource}, {err}")
            print(f"Unexpected error while opening resource: {err=}, {type(err)=}")

        # User power meter instrument selection
        selection = int(input("Select Power meter: "))
        selected_resource = devices['Resource'][selection - 1]
        logger.info(f"Selected power meter instrument: {selected_resource}")
        # connect GPIB into a buffer
        logger.info(f"Opening power meter instrument resource: {selected_resource}")
        try:
            buffer = self._resource_manager.open_resource(selected_resource)
            # buffer.read_termination = "\r\n"
            OPM = buffer.resource_name
            logger.info(f"Opened power meter instrument: {OPM}")
        except Exception as err:
            logger.info(f"Error while opening resource: {selected_resource}, {err}")
            print(f"Unexpected error while opening resource: {err=}, {type(err)=}")

        self.__cached_TSL_Address = TSL
        self.__cached_MPM_Address = OPM

        if mode == 'SME':
            # User daq device selection
            selection = input("Select DAQ board: ")
            DAQ = self._system.devices[int(selection) - 1 - len(devices['Name'])].name
            logger.info(f"Selected DAQ instrument: {DAQ}")
            self.__cached_DAQ_Address = DAQ

        return None

    def dispose(self) -> None:
        logger.info("Destroying instrument objects.")
        if not self.is_disposed:
            self._resource_manager.close()
            self._system = None
            self.__cached_TSL_Address = None
            self.__cached_MPM_Address = None
            self.__cached_DAQ_Address = None
