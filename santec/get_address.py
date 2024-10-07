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


class Instrument:
    Idn: str = ""
    VendorName: str = ""
    ProductName: str = ""
    SerialNumber: int = 12345678
    VersionNumber: str = ""
    Interface: str = ""
    ResourceValue: str = ""


class GetAddress:
    """
    A class to get the GPIB or USB addresses of TSL, MPM and DAQ instruments/devices.

    Attributes:
        _resource_manager (ResourceManager): pyvisa's ResourceManager class.
        _resources (tuple[str]): Gets the list of connected gpib resources.
        _system (Any): Gets the list of connected DAQ devices.
        __cached_tsl_address: Stores the TSL instrument ip_address
        __cached_mpm_address: Stores the MPM instrument ip_address
        __cached_daq_address: Stores the DAQ device ip_address
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
        instruments = self.detect_instruments()

        if not instruments:
            logger.critical("No TSL or MPM instruments were found.")
            raise RuntimeError("No TSL or MPM instruments were found.")

        self.select_instruments(instruments)

        if mode == 'SME':
            self.select_daq_device(instruments)

    def detect_instruments(self) -> list:
        """
        Detects GPIB and USB instruments and returns a list of Instrument objects.

        Returns:
            list: A list of detected Instrument objects.
        """
        instruments = []
        self.detect_gpib_resources(instruments)
        self.detect_usb_resources(instruments)

        logger.info(f"Current instruments: {instruments}")
        if len(instruments) < 2:
            logger.critical(f"TSL or MPM instruments not connected.")
            raise Exception("TSL or MPM instruments not connected!!!")

        self.sort_devices(instruments)

        return instruments

    def detect_gpib_resources(self, instruments: list) -> None:
        """
        Detects GPIB resources and appends them to the provided instruments list.

        Parameters:
            instruments (list): The list where detected GPIB resources will be stored.
        """
        logger.info("Getting GPIB resources")
        resource_tools = [i for i in self._resources if 'GPIB' in i]
        logger.info(f"Available GPIB resources: {resource_tools}")

        for resource in resource_tools:
            self.check_gpib_resource(resource, instruments)

    def check_gpib_resource(self, resource: str, instruments: list) -> None:
        """
        Opens a GPIB resource and appends it to the instrument list if it
        is identified as a SANTEC instrument.

        Parameters:
            resource (str): The resource string to be opened.
            instruments (list): The list where the found SANTEC instrument will be stored.

        Raises:
            RuntimeError: If there is an error while opening the resource.
        """
        try:
            logger.info(f"Opening resource: {resource}")
            instrument = self._resource_manager.open_resource(resource)
            resource_idn = instrument.query("*IDN?")
            logger.info(f"Opened instrument: {resource_idn}")

            if 'SANTEC' in resource_idn:
                instr = Instrument()
                idn = resource_idn.split(',')
                instr.Idn = resource_idn
                instr.VendorName = idn[0]
                instr.ProductName = idn[1]
                instr.SerialNumber = int(idn[2])
                instr.VersionNumber = idn[3]
                instr.ResourceValue = resource
                instr.Interface = "GPIB"
                instruments.append(instr)
            instrument.close()
        except RuntimeError as err:
            logger.info(f"Error while opening resource: {resource}, {err}")

    @staticmethod
    def detect_usb_resources(instruments: list) -> None:
        """
        Detects USB resources and appends them to the provided instruments list.

        Parameters:
            instruments (list): The list where detected USB resources will be stored.
        """
        logger.info("Getting USB resources")
        main_communication = MainCommunication()
        usb_resources = list(main_communication.Get_USB_Resouce())
        logger.info(f"Available USB resources: {usb_resources}")

        for i, value in enumerate(usb_resources):
            usb_id = f"USB{i}"
            instr = Instrument()
            idn = value.strip("'").split('_')
            instr.Idn = value
            instr.VendorName = "SANTEC"
            instr.ProductName = idn[0]
            instr.SerialNumber = int(idn[1])
            instr.VersionNumber = "NA"
            instr.ResourceValue = usb_id
            instr.Interface = "USB"
            instruments.append(instr)

    @staticmethod
    def sort_devices(instruments: list) -> None:
        """
        Sorts the instrument list by the type of instrument (TSL vs. MPM)
        and prints the sorted list of detected instruments.

        Parameters:
            instruments (list): The list containing detected instruments.
        """
        instruments.sort(key=lambda x: x.Idn.startswith('SANTEC,MPM'))

        print("Present Instruments: ")
        for i, instr in enumerate(instruments):
            print(i + 1, ": ", instr.Interface, " | ", instr.Idn)

    def select_instruments(self, instruments: list) -> None:
        """
        Prompts the user to select TSL and MPM instruments and stores their addresses
        in the class attributes.

        Parameters:
            instruments (list): The list containing information about the detected instruments.
        """
        self.__cached_tsl_address = self.user_select_instrument(instruments, "Laser instrument")
        self.__cached_mpm_address = self.user_select_instrument(instruments, "Power meter instrument")

    @staticmethod
    def user_select_instrument(instruments: list, instrument: str) -> str:
        """
        Prompts the user to select an instrument from the provided instruments list
        and returns the selected instrument's ip_address.

        Parameters:
            instruments (list): The list containing detected instruments.
            instrument (str): The current instrument.

        Returns:
            str: The resource name of the selected instrument.
        """
        selection = int(input(f"Select {instrument}: "))
        selected_instrument = instruments[selection - 1]
        logger.info(f"Selected {instrument}: {selected_instrument.ResourceValue}")

        return selected_instrument

    def select_daq_device(self, instruments: list) -> None:
        """
        Prompts the user to select a DAQ device from the available devices
        and stores its ip_address.

        Parameters:
            instruments (list): The list containing information about the detected instruments.

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
            print((i + 1) + len(instruments), ": ", value)

        selection = input("Select DAQ board: ")
        daq_device_address = self._system.devices[int(selection) - 1 - len(instruments)].name
        logger.info(f"Selected DAQ instrument: {daq_device_address}")
        self.__cached_daq_address = daq_device_address

    def get_tsl_address(self) -> str:
        """
        Returns:
            The user selected TSL instrument ip_address.
            Returns empty string if initialize_instrument_addresses was not initialized.
        """
        if self.__cached_tsl_address is None:
            self.initialize_instrument_addresses()
        return self.__cached_tsl_address

    def get_mpm_address(self) -> str:
        """
        Returns:
            The user selected MPM instrument ip_address.
            Returns empty string if initialize_instrument_addresses was not initialized.
        """
        if self.__cached_mpm_address is None:
            self.initialize_instrument_addresses()
        return self.__cached_mpm_address

    def get_dev_address(self) -> str:
        """
        Returns:
            The user selected DAQ device ip_address.
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
