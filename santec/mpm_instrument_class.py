# -*- coding: utf-8 -*-

"""
MPM Instrument Class.

@organization: Santec Holdings Corp.
"""

# Import numpy for array operations
from numpy import array

# Importing from Santec namespace
from Santec import MPM, CommunicationTerminator
from Santec.Communication import CommunicationMethod, GPIBConnectType  # Enumeration Class

# Importing instrument error strings
from .error_handling_class import InstrumentError, instrument_error_strings
from .get_address import Instrument

# Import program logger
from . import logger


class MpmData:
    """
    A class to represent the data for an MPM.

    Attributes:
        averaging_time (float): The averaging time of the MPM.
        range_data (list): The list of range count values of an MPM module.
        modules_and_channels (list): The list of module and channels count values of an MPM.
    """
    averaging_time: float = 0.0
    range_data: list = []
    modules_and_channels: list = []


class MpmInstrument(MpmData):
    """
    A class to represent the data for an MPM.

    Attributes:
        __mpm (MPM): The MPM class from the namespace Santec.
        interface (str): The MPM instrument interface or connection type.
                        Example: GPIB or LAN
        ip_address (str): The connection ip_address of the MPM.
        port (int): In case of LAN connection, the port number of the MPM.
        instrument (Instrument): The instrument object in case of GPIB or USB connection.
        gpib_connect_type (str): In case of GPIB connection, the connection type of the GPIB,
                                if National Instruments, gpib_connect_type="NI",
                                if Keysight Instruments, gpib_connect_type="Keysight".

    Parameters:
        interface (str): The TSL instrument interface or connection type.
                        Supported types: GPIB, LAN or USB
        ip_address (str): The ip_address for the instrument, which can be a GPIB ip_address (e.g., 'GPIB0::10::INSTR')
                    or a LAN ip_address (e.g., '192.168.1.100').
        port (int): In case of LAN connection, the port number of the TSL.
                    Default value = 5000.
        instrument (Instrument): The instrument object in case of GPIB or USB connection.
        gpib_connect_type (str | optional): In case of GPIB connection, the connection type of the GPIB,
                                if using National Instruments, gpib_connect_type="NI",
                                if using Keysight Instruments, gpib_connect_type="Keysight".
                                Default: "ni"

    Raises:
        Exception: If the provided interface is not GPIB or LAN.
    """
    def __init__(self,
                 interface: str,
                 ip_address: str = "",
                 port: int = 5000,
                 instrument: Instrument = None,
                 gpib_connect_type: str = "ni"):
        logger.info("Initializing Mpm Instrument class.")
        self.__mpm = MPM()
        self.interface = interface.lower()
        self.ip_address = ip_address
        self.port = port
        self.instrument = instrument
        self.gpib_connect_type = gpib_connect_type.lower()
        logger.info(f"Mpm Instrument details, Interface: {interface}, Address: {ip_address},"
                    f" Port: {port}, Instrument:{instrument}, Gpib connect type: {gpib_connect_type}")

        if interface not in ("GPIB", "LAN"):
            logger.warning(f"Invalid interface type, this interface {interface} is not supported.")
            raise Exception(f"This interface {interface} is not supported.")

    def __str__(self):
        return "MpmInstrument"

    def connect(self) -> None:
        """
        Method handling the connection protocol of the MPM.

        Raises:
            RuntimeError: In case failed to connect to the MPM.
        """
        communication_type = None
        logger.info("Connect Mpm instrument")
        if self.instrument is not None:
            instrument_resource = self.instrument.ResourceValue
            if "gpib" in self.interface:
                self.__mpm.Terminator = CommunicationTerminator.CrLf
                self.__mpm.GPIBBoard = int(instrument_resource.split('::')[0][-1])
                self.__mpm.GPIBAddress = int(instrument_resource.split('::')[1])
                if "ni" in self.gpib_connect_type:
                    self.__mpm.GPIBConnectType = GPIBConnectType.NI4882
                elif "keysight" in self.gpib_connect_type:
                    self.__mpm.GPIBConnectType = GPIBConnectType.KeysightIO
                communication_type = CommunicationMethod.GPIB

        elif "lan" in self.interface:
            self.__mpm.IPAddress = self.ip_address
            self.__mpm.Port = self.port     # Default Port = 5000.
            self.__mpm.TimeOut = 5000  # timeout value for MPM
            communication_type = CommunicationMethod.TCPIP

        if communication_type is None:
            logger.error("MPM instrument not initialized.")
            raise RuntimeError("MPM instrument not initialized.")

        try:
            errorcode = self.__mpm.Connect(communication_type)        # Establish the connection

            if errorcode != 0:
                self.__mpm.DisConnect()
                logger.critical("Mpm instrument connection error, ",
                                str(errorcode) + ": " + instrument_error_strings(errorcode))
                raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))

        except InstrumentError as e:
            raise RuntimeError(f"Error occurred: {e}")

        logger.info("Connected to Mpm instrument.")

    def query_mpm(self, command: str) -> tuple[int, str]:
        """
        Queries the MPM instrument with a command,
        and returns the read data from the instrument buffer.

        Parameters:
            command (str): The command to query to the MPM.

        Returns:
              tuple[int, str]:
                - int: status value of the query operation.
                - str: read value of the buffer.

        Raises:
             RuntimeError: If the query operation fails.
        """
        command = command.upper()
        logger.info(f"Querying MPM, command: {command}")
        try:
            status, response = self.__mpm.Echo(command, "")
            return status, response
        except Exception as e:
            logger.error(f"Failed to query MPM with command '{command}': {e}")
            raise RuntimeError(f"query_mpm failed: {e}")

    def write_mpm(self, command: str) -> int:
        """
        Writes a command to the MPM instrument.

        Parameters:
            command (str): The command to write to the MPM.

        Returns:
              int: status value of the write operation.

        Raises:
             RuntimeError: If the write operation fails.
        """
        command = command.upper()
        logger.info(f"Writing to MPM, command: {command}")
        try:
            status = self.__mpm.Write(command)
            return status
        except Exception as e:
            logger.error(f"Failed to write to MPM with command '{command}': {e}")
            raise RuntimeError(f"write_mpm failed: {e}")

    def read_mpm(self) -> tuple[int, str]:
        """
        Reads data from the MPM instrument buffer.

        Returns:
              tuple[int, str]:
                - int: status value of the read operation.
                - str: read value of the buffer.

        Raises:
             RuntimeError: If the read operation fails.
        """
        try:
            status, response = self.__mpm.Read("")
            return status, response
        except Exception as e:
            logger.error(f"Failed to read MPM, {e}")
            raise RuntimeError(f"read_mpm failed: {e}")

    def get_modules_and_channels(self) -> list:
        """
        Detects all the modules that are mounted on the MPM (looping on the five possible slots).
        If the detected module is an MPM-212, then the possible optical channels are numbered 1 and 2
        Else, then the possible optical channels are numbered from 1 to 4.
        If no module is detected, then the method returns an empty array.

        Raises:
            Exception: In case no modules were detected on the MPM.

        Returns:
            list: A list of the MPM modules and channels count.
            Example:
                [[1,2,3,4],[1,2], [], [], []]
                Where the item index is the slot number (in the example above slots 0 and 1 contain modules),
                and the items in these subarrays are channel numbers.
        """
        logger.info("Get MPM modules and channels")
        self.modules_and_channels = []
        for slot_count in range(5):
            if self.__mpm.Information.ModuleEnable[slot_count] is True:
                if self.check_mpm_212(slot_count) is True:
                    self.modules_and_channels.append([1, 2])
                else:
                    self.modules_and_channels.append([1, 2, 3, 4])
            else:
                self.modules_and_channels.append([])
        if len(self.modules_and_channels) == 0:
            logger.warning("No MPM modules / channels were detected.")
            raise Exception("No modules / channels were detected.")
        logger.info(f"Detected MPM modules and channels: {self.modules_and_channels}")
        return self.modules_and_channels

    def check_module_type(self) -> tuple[bool, bool]:
        """
        Checks the type of modules that are mounted to the MPM.
        This method calls check_mpm_215 and check_mpm_213 methods.

        Raises:
            Exception: MPM-215 can't be used with other MPM modules.

        Returns:
            tuple[bool, bool]: True, True if the MPM-215 and MPM-213 modules are detected.
        """
        logger.info("MPM check module type")
        flag_215 = False
        flag_213 = False
        slot = 0
        count_215 = 0

        for slot_count in range(5):
            if self.__mpm.Information.ModuleEnable[slot_count] is True:
                flag_215 = self.check_mpm_215(slot_count)
                flag_213 = self.check_mpm_213(slot_count)
                slot += 1
                if flag_215 is True:
                    count_215 += 1

        if flag_215 is True and count_215 != slot:
            logger.error("MPM-215 can't use with other modules.")
            raise Exception("MPM-215 can't use with other modules.")
        logger.info(f"MPM module type check: flag_215={flag_215}, flag_213={flag_213}")
        return flag_215, flag_213

    def check_mpm_215(self, slot_num: int) -> bool:
        """
        Checks if the mounted module at the given slot number is an MPM-215 module.

        Parameters:
            slot_num (int): The module number (0~4) of the MPM.

        Returns:
            bool: True if an MPM-215 is detected.
        """
        logger.info("MPM check if module 215")
        check = bool(self.__mpm.Information.ModuleType[slot_num] == "MPM-215")
        logger.info(f"MPM module 215: {check}")
        return check

    def check_mpm_213(self, slot_number: int) -> bool:
        """
        Checks if the mounted module at the given slot number is an MPM-213 module.

        Parameters:
            slot_number (int): The module number (0~4) of the MPM.

        Returns:
            bool: True if an MPM-213 is detected.
        """
        logger.info("MPM check if module 213")
        check = bool(self.__mpm.Information.ModuleType[slot_number] == "MPM-213")
        logger.info(f"MPM module 213: {check}")
        return check

    def check_mpm_212(self, slot_number: int) -> bool:
        """
        Checks if the mounted module at the given slot number is an MPM-212 module.

        Parameters:
            slot_number (int): The module number (0~4) of the MPM.

        Returns:
            bool: True if an MPM-212 is detected.
        """
        logger.info("MPM check if module 212")
        check = bool(self.__mpm.Information.ModuleType[slot_number] == "MPM-212")
        logger.info(f"MPM module 212: {check}")
        return check

    def get_range(self) -> None:
        """
        Gets the measurement dynamic range of the MPM module.
        Depending on the module type, the dynamic range varies.

        The method appends the range values to range_data attribute of the class.

        Example:
                list: if MPM-215: [1],
                    if module MPM-213: [1,2,3,4],
                    if other modules: [1,2,3,4,5]
        """
        logger.info("MPM get dynamic ranges of modules")
        self.range_data = []
        if self.check_mpm_215 is True:
            self.range_data = [1]
        elif self.check_mpm_213 is True:
            # 213 have 4 ranges
            self.range_data = [1, 2, 3, 4]
        else:
            self.range_data = [1, 2, 3, 4, 5]
        logger.info(f"MPM range data: {self.range_data}")

    def set_range(self, power_range: int) -> None:
        """
        Sets the dynamic range value of the MPM.

        Args:
            power_range (int): The dynamic range value to be set.

        **Information**
            Check get_range method for available dynamic ranges.

        Raises:
            InstrumentError: In case the MPM is busy,
                            or in case the wrong value for power_range is entered,
                            or if setting MPM range fails.
        """
        logger.info("MPM set range")
        errorcode = self.__mpm.Set_Range(power_range)

        if errorcode != 0:
            logger.error("Error while setting MPM range, ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("MPM range set.")

    def zeroing(self) -> str:
        """
        Performs a Zeroing on all the MPM modules and channels.

        **Note**
            All the channels must be closed with respective back caps before
            performing this operation.

        Raises:
            InstrumentError: In case the MPM is busy,
                        or in case wrong value for power_range is entered,
                        or in case the MPM returns an error,
                        or if performing MPM zeroing fails.

        Returns:
            str: Success.
        """
        logger.info("MPM perform zeroing")
        errorcode = self.__mpm.Zeroing()

        if errorcode != 0:
            logger.error("Error while performing MPM zeroing, ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM zeroing done.")
        return errorcode

    def get_averaging_time(self) -> float:
        """
        Gets the averaging time of the MPM.

        Raises:
            InstrumentError: In case the MPM is busy,
                        or if getting the averaging time fails.

        Returns:
            float: Averaging time of the MPM.
        """
        logger.info("MPM get averaging time")
        errorcode, self.averaging_time = self.__mpm.Get_Averaging_Time(0)

        if errorcode != 0:
            logger.error("Error while getting MPM averaging time, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM averaging time: {self.averaging_time}")
        return self.averaging_time

    def logging_start(self) -> None:
        """
        Starts MPM logging.

        Raises:
            InstrumentError: In case the MPM is busy,
                        or fails to start MPM logging.
        """
        logger.info("MPM start logging")
        errorcode = self.__mpm.Logging_Start()
        if errorcode != 0:
            logger.error("Error while MPM start logging, ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("MPM logging started.")

    def logging_stop(self, except_if_error: bool = True) -> None:
        """
        Stops the MPM logging.

        Parameters:
            except_if_error (bool | optional): Set True if raising exception is needed within this method.
            Else, i.e.,
            if this method is inserted within STS then set False
            so the exception will be raised from STS method.
            Default value: True.

        Raises:
            InstrumentError: In case of failure in stopping the MPM logging.
        """
        logger.info("MPM stop logging")
        errorcode = self.__mpm.Logging_Stop()
        if errorcode != 0 and except_if_error is True:
            logger.error("Error while MPM stop logging, ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("MPM logging stopped.")

    def get_each_channel_log_data(self,
                                  slot_number: int,
                                  channel_number: int) -> list:
        """
        Gets log data for specified slot and channel number.

        Parameters:
            slot_number (int): Module number (0~4) of the MPM.
            channel_number (int): Channel number (1~4) of the MPM module.

        Raises:
            InstrumentError: In case wrong arguments are passed,
                            or fails to get log data from the MPM.

        Returns:
            list: List of log data.
        """
        logger.info(f"MPM get each channel log data, slot_number={slot_number}, channel_number={channel_number}")
        errorcode, log_data = self.__mpm.Get_Each_Channel_Logdata(slot_number, channel_number, None)
        if errorcode != 0:
            logger.error("Error while getting channel log data, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM slot {slot_number} channel {channel_number}, log data length: {len(list(log_data))}")
        return list(log_data)

    def set_logging_parameters(self,
                               start_wavelength: float,
                               stop_wavelength: float,
                               sweep_step: float,
                               sweep_speed: float,
                               trigger_step: float = 0.0) -> None:
        """
        Sets the logging parameter of the MPM instrument.

        Parameters:
            start_wavelength (float): The starting wavelength for the sweep.
            stop_wavelength (float): The stopping wavelength for the sweep.
            sweep_step (float): The step wavelength of a sweep.
            sweep_speed (float): The speed of a sweep.
            trigger_step (float): (Not necessary value) The step size (nm) between two TSL triggers.
                                Default value: 0.0

        Raises:
            InstrumentError: If setting the logging parameters to the MPM fails.
        """
        logger.info(f"Set MPM logging params: start_wavelength={start_wavelength}, stop_wavelength={stop_wavelength}, "
                    f"sweep_step={sweep_step}, sweep_speed={sweep_speed}, trigger_step={trigger_step}")
        errorcode = self.__mpm.Set_Logging_Paremeter_for_STS(start_wavelength,
                                                             stop_wavelength,
                                                             sweep_step,
                                                             trigger_step,
                                                             sweep_speed,
                                                             self.__mpm.Measurement_Mode.Freerun)

        if errorcode != 0:
            logger.error("Error while setting MPM logging params",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM logging params set.")

    def wait_for_log_completion(self) -> None:
        """
        Waits for MPM log completion.

        Raises:
            RuntimeError: If the MPM Trigger received an error!
            Please check trigger cable connection.
            InstrumentError: If the wait for MPM log completion fails.
        """
        logger.info("MPM wait for log completion")
        errorcode = None
        status = 0  # MPM Logging status 0: During logging 1: Completed, -1:stopped, 10:stopped

        logging_point = None
        # Constantly get the status in a loop. Increase the MPM timeout for this process.
        while status == 0:
            errorcode, status, logging_point = self.__mpm.Get_Logging_Status(0, 0)  # Updates status, which should break us out of the loop.
            break

        if errorcode == -999:
            error_string = "MPM Trigger received an error! Please check trigger cable connection."
            logger.critical(error_string)
            raise RuntimeError(error_string)

        if errorcode != 0 and status != -1:    # It's a success if either the error code is 0,
            # or the status is -1, otherwise, throw.
            logger.error("Error while waiting for MPM log completion, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM logging completed. logging_point={logging_point}")

    def disconnect(self) -> None:
        """
        Disconnects the connection from the MPM instrument.

        Raises:
              RuntimeError: If disconnecting the MPM instrument fails.
        """
        try:
            self.__mpm.DisConnect()
            logger.info("MPM connection disconnected.")
        except RuntimeError as e:
            logger.error(f"Error while disconnecting the MPM connection, {e}")
