# -*- coding: utf-8 -*-

"""
Get Instrument Addresses.
Connection modes: GPIB, LAN or USB(only TSL).

@organization: Santec Holdings Corp.
"""

import pyvisa
import nidaqmx

# Import Santec communication class from Santec namespace
from Santec.Communication import MainCommunication

# Import program logger
from . import logger


class GetAddress:
    """
    A class to get the GPIB or USB addresses of TSL, MPM and DAQ instruments/devices.

    Attributes:
        _resource_manager (ResourceManager): pyvisa's ResourceManager class.
        _resources (tuple[str]): Gets the list of connected gpib resources.
        _system (Any): Gets the list of connected DAQ devices.
        __cached_tsl_address: Stores the TSL instrument address
        __cached_mpm_address: Stores the MPM instrument address
        __cached_daq_address: Stores the DAQ device address
        is_disposed (bool): Stores the state of instrument connections disposed.
    """
    _resource_manager = pyvisa.ResourceManager()    # Initializing pyvisa resource manager class
    _resources = _resource_manager.list_resources()     # Getting a list of all detected instruments
    _system = nidaqmx.system.System.local()     # Getting a list of all detected DAQ devices

    def __init__(self):
        self.__cached_tsl_address: str = ""
        self.__cached_mpm_address: str = ""
        self.__cached_daq_address: str = ""
        self.is_disposed: bool = False

    def initialize_instrument_addresses(self, mode: str = "SME") -> None:
        """
        Detects and displays all the Santec GPIB and USB instrument connections.
        Also, detects and displays the DAQ devices.

        Parameters:
            mode (str): Current STS operation mode.
                        Default vale: "SME".

        **Information**
            Upon detecting and displaying the instruments/devices,
            the user shall select their laser, power meter and daq device for operation.
            The selected instrument's addresses will be stored into the class attributes,
                __cached_tsl_address: TSL instrument address
                __cached_mpm_address: MPM instrument address
                __cached_daq_address: DAQ device address
            These addresses can be accessed by using the following methods:
                get_tsl_address: returns the selected TSL instrument address
                get_mpm_address: returns the selected MPM instrument address
                get_dev_address: returns the selected DAQ device address

        Raises:
            Exception: If opening a gpib resource fails.
            RuntimeError: If no TSL or MPM instruments are found,
                        or if no DAQ device is found.
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
                except RuntimeError as err:
                    logger.info(f"Error while opening resource: {resource}, {err}")
                    print(f"Unexpected error while opening resource: {resource}, {err=}, {type(err)=}")

        # USB instruments
        logger.info("Getting USB resources")
        main_communication = MainCommunication()
        usb_resources = list(main_communication.Get_USB_Resouce())
        logger.info(f"Available USB resources: {usb_resources}")
        if len(usb_resources) > 0:
            for i, value in enumerate(usb_resources):
                usb_id = f"USB{i}"
                devices['Name'].append(value)
                devices['Resource'].append(usb_id)
                devices['Interface'].append("USB ")

        # Zipping devices dictionary 'Name' and 'Resource' into a list
        devices_list = list(zip(devices['Name'], devices['Resource'], devices['Interface']))

        if not len(devices_list) > 0:
            logger.critical("No TSL or MPM instruments were found.")
            raise RuntimeError("No TSL or MPM instruments were found.")

        # Sorting the device list in order from TSL to MPM instruments
        devices_list = sorted(devices_list, key=lambda x: x[0].startswith('SANTEC,MPM'))

        # Unzipping the sorted devices list and assigning key & values of device dictionary
        devices['Name'], devices['Resource'], devices['Interface'] = zip(*devices_list)

        # Prints all the detected SANTEC instruments in order of TSL to MPM
        print("Present Instruments: ")
        for i in range(len(devices['Name'])):
            print(i + 1, ": ", devices['Interface'][i], " | ", devices['Name'][i])

        if "SME" in mode:
            # Prints all the detected DAQ devices
            logger.info("Getting DAQ devices.")
            daq_devices = self._system.devices.device_names
            logger.info(f"Current DAQ devices: {daq_devices}")
            if not len(daq_devices) > 0:
                logger.critical("No DAQ device was found.")
                raise RuntimeError("No DAQ device was found.")
            print("Detected DAQ devices: ")
            for i in daq_devices:
                logger.info(f"Detected DAQ device: {i}")
                print(self._system.devices.device_names.index(i) + 1 + len(devices['Name']), ": ", i)

        tsl_instrument_address = None
        mpm_instrument_address = None

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
            tsl_instrument_address = buffer.resource_name
            logger.info(f"Opened laser instrument: {tsl_instrument_address}")
        except RuntimeError as err:
            logger.info(f"Error while opening resource: {selected_resource}, {err}")
            print(f"Unexpected error while opening resource: {selected_resource}, {err=}, {type(err)=}")

        # User power meter instrument selection
        selection = int(input("Select Power meter: "))
        selected_resource = devices['Resource'][selection - 1]
        logger.info(f"Selected power meter instrument: {selected_resource}")
        # connect GPIB into a buffer
        logger.info(f"Opening power meter instrument resource: {selected_resource}")
        try:
            buffer = self._resource_manager.open_resource(selected_resource)
            # buffer.read_termination = "\r\n"
            mpm_instrument_address = buffer.resource_name
            logger.info(f"Opened power meter instrument: {mpm_instrument_address}")
        except RuntimeError as err:
            logger.info(f"Error while opening resource: {selected_resource}, {err}")
            print(f"Unexpected error while opening resource: {selected_resource}, {err=}, {type(err)=}")

        self.__cached_tsl_address = tsl_instrument_address
        self.__cached_mpm_address = mpm_instrument_address

        if mode == 'SME':
            # User daq device selection
            selection = input("Select DAQ board: ")
            daq_device_address = self._system.devices[int(selection) - 1 - len(devices['Name'])].name
            logger.info(f"Selected DAQ instrument: {daq_device_address}")
            self.__cached_daq_address = daq_device_address

    def get_tsl_address(self) -> str:
        """
        Returns:
            The user selected TSL instrument address.
            Returns empty string if initialize_instrument_addresses was not initialized.
        """
        if self.__cached_tsl_address is None:
            self.initialize_instrument_addresses()
        return self.__cached_tsl_address

    def get_mpm_address(self) -> str:
        """
        Returns:
            The user selected MPM instrument address.
            Returns empty string if initialize_instrument_addresses was not initialized.
        """
        if self.__cached_mpm_address is None:
            self.initialize_instrument_addresses()
        return self.__cached_mpm_address

    def get_dev_address(self) -> str:
        """
        Returns:
            The user selected DAQ device address.
            Returns empty string if initialize_instrument_addresses was not initialized.
        """
        if self.__cached_daq_address is None:
            self.initialize_instrument_addresses()
        return self.__cached_daq_address

    def dispose(self) -> None:
        """
        Disposes / clears all the instrument connection objects.

        Objects cleared are:
            _resource_manager
            _system
            __cached_tsl_address
            __cached_mpm_address
            __cached_daq_address
        """
        logger.info("Destroying instrument objects.")
        if not self.is_disposed:
            self._resource_manager.close()
            self._system = None
            self.__cached_tsl_address = None
            self.__cached_mpm_address = None
            self.__cached_daq_address = None
