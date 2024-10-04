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
        Detects and displays all the Santec GPIB and USB instrument connections,
        as well as the DAQ devices.

        Parameters:
            mode (str): Current STS operation mode.
            Default value: "SME".

        Raises:
            RuntimeError: If no TSL or MPM instruments are found.
        """
        logger.info("Initializing Instrument Addresses")
        devices = self.detect_instruments()

        if not devices['Name']:
            logger.critical("No TSL or MPM instruments were found.")
            raise RuntimeError("No TSL or MPM instruments were found.")

        self.select_instruments(devices)

        if mode == 'SME':
            self.select_daq_device(devices)

    def detect_instruments(self) -> dict:
        """
        Detects GPIB and USB instruments and returns a dictionary containing
        the names, resources, and interfaces of the found devices.

        Returns:
            dict: A dictionary with keys 'Name', 'Resource', and 'Interface',
                  each containing a list of detected devices.
        """
        devices = {'Name': [], 'Resource': [], 'Interface': []}
        self.detect_gpib_resources(devices)
        self.detect_usb_resources(devices)
        logger.info(f"Current devices: {devices['Name']}, {devices['Resource']}, {devices['Interface']}")
        if len(devices['Resource']) < 2:
            logger.critical(f"TSL or MPM instruments not connected.")
            raise Exception("TSL or MPM instruments not connected!!!")
        self.sort_devices(devices)

        return devices

    def detect_gpib_resources(self, devices: dict) -> None:
        """
        Detects GPIB resources and appends them to the provided devices' dictionary.

        Parameters:
            devices (dict): The dictionary where detected GPIB resources will be stored.
        """
        logger.info("Getting GPIB resources")
        resource_tools = [i for i in self._resources if 'GPIB' in i]
        logger.info(f"Available GPIB resources: {resource_tools}")

        for resource in resource_tools:
            self.check_gpib_resource(resource, devices)

    def check_gpib_resource(self, resource: str, devices: dict) -> None:
        """
        Opens a GPIB resource and appends it to the device dictionary if it
        is identified as a SANTEC instrument.

        Parameters:
            resource (str): The resource string to be opened.
            devices (dict): The dictionary where the found SANTEC instrument
                            will be stored.

        Raises:
            RuntimeError: If there is an error while opening the resource.
        """
        try:
            logger.info(f"Opening resource: {resource}")
            instrument = (self._resource_manager.open_resource(resource))
            resource_idn = instrument.query("*IDN?")
            logger.info(f"Opened instrument: {resource_idn}")
            if 'SANTEC' in resource_idn:
                devices['Name'].append(resource_idn)
                devices['Resource'].append(resource)
                devices['Interface'].append("GPIB")
            instrument.close()
        except RuntimeError as err:
            logger.info(f"Error while opening resource: {resource}, {err}")

    @staticmethod
    def detect_usb_resources(devices: dict) -> None:
        """
        Detects USB resources and appends them to the provided devices' dictionary.

        Parameters:
            devices (dict): The dictionary where detected USB resources will be stored.
        """
        logger.info("Getting USB resources")
        main_communication = MainCommunication()
        usb_resources = list(main_communication.Get_USB_Resouce())
        logger.info(f"Available USB resources: {usb_resources}")

        for i, value in enumerate(usb_resources):
            usb_id = f"USB{i}"
            devices['Name'].append(value)
            devices['Resource'].append(usb_id)
            devices['Interface'].append("USB")

    @staticmethod
    def sort_devices(devices: dict) -> None:
        """
        Sorts the device dictionary by the type of instrument (TSL vs. MPM)
        and prints the sorted list of detected instruments.

        Parameters:
            devices (dict): The dictionary containing detected devices.
        """
        devices_list = list(zip(devices['Name'], devices['Resource'], devices['Interface']))
        devices_list.sort(key=lambda x: x[0].startswith('SANTEC,MPM'))
        devices['Name'], devices['Resource'], devices['Interface'] = zip(*devices_list)

        print("Present Instruments: ")
        for i in range(len(devices['Name'])):
            print(i + 1, ": ", devices['Interface'][i], " | ", devices['Name'][i])

    def select_instruments(self, devices: dict) -> None:
        """
        Prompts the user to select TSL and MPM instruments and stores their addresses
        in the class attributes.

        Parameters:
            devices (dict): The dictionary containing information about the detected instruments.
        """
        self.__cached_tsl_address = self.user_select_instrument(devices, "Laser instrument")
        self.__cached_mpm_address = self.user_select_instrument(devices, "Power meter instrument")

    @staticmethod
    def user_select_instrument(devices: dict, instrument: str) -> str:
        """
        Prompts the user to select an instrument from the provided devices dictionary
        and returns the selected instrument's address.

        Parameters:
            devices (dict): The dictionary containing detected instruments.
            instrument (str): The current instrument.

        Returns:
            str: The resource name of the selected instrument.

        Raises:
            RuntimeError: If there is an error while opening the selected resource.
        """
        selection = int(input(f"Select {instrument}: "))
        selected_resource = devices['Resource'][selection - 1]
        logger.info(f"Selected {instrument}: {selected_resource}")

        return selected_resource

        # try:
        #     buffer = self._resource_manager.open_resource(selected_resource)
        #     idn = buffer.query('*IDN?')
        #     if 'TSL' in idn:
        #         buffer.write('SYST:COMM:GPIB:DEL 2')  # Set the TSL to CRLF delimiter
        #     instrument_address = buffer.resource_name
        #     logger.info(f"Opened {instrument_address} instrument: {idn}")
        #     return instrument_address
        # except RuntimeError as err:
        #     logger.info(f"Error while opening resource: {selected_resource}, {err}")
        #     print(f"Unexpected error while opening resource: {selected_resource}, {err=}, {type(err)=}")

    def select_daq_device(self, devices: dict) -> None:
        """
        Prompts the user to select a DAQ device from the available devices
        and stores its address.

        Parameters:
            devices (dict): The dictionary containing information about the detected instruments.

        Raises:
            RuntimeError: If no DAQ device is found.
        """
        logger.info("Getting DAQ devices.")
        daq_devices = self._system.devices.device_names
        logger.info(f"Current DAQ devices: {daq_devices}")

        if not daq_devices:
            logger.critical("No DAQ device was found.")
            raise RuntimeError("No DAQ device was found.")

        print("\nDetected DAQ devices: ")
        for i, value in enumerate(daq_devices):
            logger.info(f"Detected DAQ device: {value}")
            print((i + 1) + len(devices['Name']), ": ", value)

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
