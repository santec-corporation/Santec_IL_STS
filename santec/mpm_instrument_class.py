# -*- coding: utf-8 -*-

"""
MPM Instrument Class.

@organization: Santec Holdings Corp.
"""

import os
import clr
import time
from . import logger
from numpy import array

# Importing instrument error strings
from santec.error_handing_class import instrument_error_strings


# Importing from Santec namespace
from Santec import MPM  # Importing MPM class
from Santec.Communication import CommunicationMethod  # Enumeration Class
from Santec.Communication import GPIBConnectType  # Enumeration Class


class MpmData:
    averaging_time = None
    range_data = None
    mods_and_chans = None


class MpmInstrument(MpmData):
    def __init__(self,
                 interface: str,
                 address: str,
                 port: int = 5000,
                 gpib_connect_type="NI"):
        logger.info("Initializing Mpm Instrument class.")
        self.__mpm = MPM()
        self.interface = interface.lower()
        self.address = address
        self.port = port
        self.gpib_connect_type = gpib_connect_type.lower()
        logger.info(f"Mpm Instrument details, Interface: {self.interface}, Address: {self.address},"
                    f" Port: {self.port}, Gpib connect type: {self.gpib_connect_type}")

        if interface not in ("GPIB", "LAN", "USB"):
            logger.warning(f"Invalid interface type, this interface {interface} is not supported.")
            raise Exception(f"This interface {interface} is not supported.")

    def __str__(self):
        return "MpmInstrument"

    def connect(self):
        """
        Method handling the connection protocol of the MPM.

        Raises:
            Exception: In case failed to connect to the MPM.
        """
        logger.info("Connect Mpm instrument")
        logger.info(f"Connect Mpm instrument, type {self.interface}")
        if "gpib" in self.interface:
            self.__mpm.GPIBAddress = int(self.address.split('::')[1])
            self.__mpm.BordNumber = int(self.address.split('::')[0][-1])
            if "ni" in self.gpib_connect_type:
                self.__mpm.GPIBConnectType = GPIBConnectType.NI4882
            elif "keysight" in self.gpib_connect_type:
                self.__mpm.GPIBConnectType = GPIBConnectType.KeysightIO
            mpm_communication_method = CommunicationMethod.GPIB

        elif "lan" in self.interface:
            self.__mpm.IPAddress = self.address
            self.__mpm.port = self.port     # Default Port = 5000.
            mpm_communication_method = CommunicationMethod.TCPIP

        else:
            errorcode = -1
            logger.error("There was NO interface specified!!!")
            raise Exception("There was NO interface specified!!!")

        self.__mpm.TimeOut = 5000  # timeout value for MPM
        errorcode = self.__mpm.Connect(mpm_communication_method)        # Establish the connection

        if errorcode != 0:
            self.__mpm.DisConnect()
            logger.critical("Mpm instrument connection error, ",
                            str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        logger.info("Connected to Mpm instrument.")
        return None

    def query_mpm(self, command: str):
        """ Queries a command to the instrument and returns a string """
        command = command.upper()
        logger.info(f"Querying MPM, command: {command}")
        try:
            status, response = self.__mpm.Echo(command, "")
            return status, response
        except Exception as e:
            logger.error(f"Failed to query MPM with command '{command}': {e}")
            raise RuntimeError(f"query_mpm failed: {e}")

    def write_mpm(self, command: str):
        """ Writes a command to the instrument """
        command = command.upper()
        logger.info(f"Writing to MPM, command: {command}")
        try:
            status = self.__mpm.Write(command)
            return status
        except Exception as e:
            logger.error(f"Failed to write to MPM with command '{command}': {e}")
            raise RuntimeError(f"write_mpm failed: {e}")

    def read_mpm(self):
        """ Reads from the instrument """
        try:
            status, response = self.__mpm.Read("")
            return status, response
        except Exception as e:
            logger.error(f"Failed to read MPM, {e}")
            raise RuntimeError(f"read_mpm failed: {e}")

    def get_modules_and_channels(self):
        """
        Detects all the modules that are mounted on the MPM (looping on the five possible slots).
        If the detected module is an MPM-212, then the possible optical channels are numbered 1 and 2
        Else, then the possible optical channels are numbered from 1 to 4.
        If no module is detected, then the method returns an empty array.

        Raises:
            Exception: In case no modules were detected on the MPM.

        Returns:
            array: array of arrays (example: [[1,2,3,4],[1,2], [], [], []])
            Where the item index is the slot number (in the example above slots 0 and 1 contain modules),
            and the items in these subarrays are channel numbers.
        """
        logger.info("Get MPM modules and channels")
        self.mods_and_chans = []
        for slot_count in range(5):
            if self.__mpm.Information.ModuleEnable[slot_count] is True:
                if self.check_mpm_212(slot_count) is True:
                    self.mods_and_chans.append([1, 2])
                else:
                    self.mods_and_chans.append([1, 2, 3, 4])
            else:
                self.mods_and_chans.append([])
        if len(self.mods_and_chans) == 0:
            logger.warning("No MPM modules / channels were detected.")
            raise Exception("No modules / channels were detected.")
        logger.info(f"Detected MPM modules and channels: {self.mods_and_chans}")
        return self.mods_and_chans

    def check_module_type(self):
        """
        Checks the type of modules that are mounted on the MPM.
        This method calls check_mpm_215 and check_mpm_213 methods.

        Raises:
            Exception: MPM-215 can't be used with other MPM modules.

        Returns:
            bool: flag_215, flag_213 True if these modules are detected.
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
        Checks if the mounted module at slot number slot_num is an MPM-215.

        Args:
            slot_num (int): The module number (0~4).

        Returns:
            bool: True if an MPM-215 is detected.
        """
        logger.info("MPM check if module 215")
        check = bool(self.__mpm.Information.ModuleType[slot_num] == "MPM-215")
        logger.info(f"MPM module 215: {check}")
        return check

    def check_mpm_213(self, slot_num: int) -> bool:
        """
        Checks if the mounted module at slot number slot_num is an MPM-213.

        Args:
            slot_num (int): The module number (0~4).

        Returns:
            bool: True if an MPM-213 is detected.
        """
        logger.info("MPM check if module 213")
        check = bool(self.__mpm.Information.ModuleType[slot_num] == "MPM-213")
        logger.info(f"MPM module 213: {check}")
        return check

    def check_mpm_212(self, slot_num: int) -> bool:
        """
        Checks if the mounted module at slot number slot_num is an MPM-212.

        Args:
            slot_num (int): The module number (0~4).

        Returns:
            bool: True if an MPM-212 is detected.
        """
        logger.info("MPM check if module 212")
        check = bool(self.__mpm.Information.ModuleType[slot_num] == "MPM-212")
        logger.info(f"MPM module 212: {check}")
        return check

    def get_range(self) -> array:
        """
        Gets the measurement dynamic range of the MPM module.
        Depending on the module type, the dynamic range varies.
        This method calls check_mpm_215 and check_mpm_213 methods.

        Returns:
            array: MPM-215: [1]
                    MPM-213: [1,2,3,4]
                    Others: [1,2,3,4,5]
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
        return None

    def set_range(self, power_range):
        """
        Sets the dynamic range of the MPM.

        Args:
            power_range (int): check get_range method for
            available dynamic ranges.

        Raises:
            Exception: In case the MPM is busy.
                        In case the wrong value for power_range is entered
        """
        logger.info("MPM set range")
        errorcode = self.__mpm.Set_Range(power_range)

        if errorcode != 0:
            logger.error("Error while setting MPM range, ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("MPM range set.")
        return None

    def zeroing(self):
        """
        Performs a Zeroing on all MPM channels.
        All the channels must be closed with respective back caps before
        performing this operation.

        Raises:
            Exception: In case the MPM is busy;
                        In case wrong value for power_range is entered;
                        In case the MPM returns an error.

        Returns:
            str: Success.
        """
        logger.info("MPM perform zeroing")
        errorcode = self.__mpm.Zeroing()

        if errorcode != 0:
            logger.error("Error while performing MPM zeroing, ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM zeroing done, error string: {instrument_error_strings(errorcode)}")
        return instrument_error_strings(errorcode)

    def get_averaging_time(self):
        """
        Gets the averaging time of the MPM.

        Raises:
            Exception: In case the MPM is busy;
                        In case of communication failure.

        Returns:
            float: averaging time
        """
        logger.info("MPM get averaging time")
        errorcode, self.averaging_time = self.__mpm.Get_Averaging_Time(0)

        if errorcode != 0:
            logger.error("Error while getting MPM averaging time, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM averaging time: {self.averaging_time}")
        return self.averaging_time

    def logging_start(self):
        """
        MPM starts logging.

        Raises:
            Exception: In case the MPM is busy.
        """
        logger.info("MPM start logging")
        errorcode = self.__mpm.Logging_Start()
        if errorcode != 0:
            logger.error("Error while MPM start logging, ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("MPM logging started.")

    def logging_stop(self, except_if_error=True):
        """
        MPM stops logging.

        Args:
            except_if_error (bool, optional): Set True if raising exception is
            needed within this method.
            Else, i.e., if this method is inserted within STS
            then set False so the exception will be raised from STS method.
            Defaults to True.

        Raises:
            Exception: In case the MPM is busy.
        """
        logger.info("MPM stop logging")
        errorcode = self.__mpm.Logging_Stop()
        if errorcode != 0 and except_if_error is True:
            logger.error("Error while MPM stop logging, ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("MPM logging stopped.")

    def get_each_channel_log_data(self, slot_num: int, chan_num: int) -> array:
        """
        Gets log data for specified slot and channel.

        Args:
            slot_num (int): Module number (0~4).
            chan_num (int): Channel number (1~4).

        Raises:
            Exception: In case wrong arguments are passed.

        Returns:
            array: array of logged data.
        """
        logger.info(f"MPM get each channel log data, slot_num={slot_num}, chan_num={chan_num}")
        errorcode, log_data = self.__mpm.Get_Each_Channel_Logdata(slot_num, chan_num, None)
        if errorcode != 0:
            logger.error("Error while getting channel log data, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM slot {slot_num} channel {chan_num}, log data length: {len(list(log_data))}")
        return list(log_data)

    def set_logging_parameters(self, start_wavelength, stop_wavelength, sweep_step, sweep_speed, trigger_step=0.0):
        """
        Sets the logging parameter for MPM integrated in STS

        Args:
            start_wavelength (float): Input the start wavelength value.
            stop_wavelength (float): Input the stop wavelength value.
            sweep_step (float): Input the sweep sweep_step wavelength value.
            sweep_speed (float): Input the sweep sweep_speed value.
            trigger_step (float): The step size (nm) between two TSL triggers.

        Raises:
            RuntimeError: When trigger signal is not detected
            RuntimeError: if the MPM didn't record data
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
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"MPM set logging params, error string: {instrument_error_strings(errorcode)}")
        return instrument_error_strings(errorcode)

    def wait_for_log_completion(self, sweep_count: int):
        """ Waits for log completion """
        logger.info("MPM wait for log completion")
        errorcode = None
        status = 0  # MPM Logging status 0: During logging 1: Completed, -1:stopped, 10:stopped
        logging_point = 0

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
            raise RuntimeError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("MPM logging completed.")
        return None

    def disconnect(self):
        """ Disconnects MPM instrument """
        try:
            self.__mpm.DisConnect()
            logger.info("MPM connection disconnected.")
        except Exception as e:
            logger.error(f"Error while disconnecting the MPM connection, {e}")
        return None
