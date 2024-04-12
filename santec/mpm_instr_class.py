# -*- coding: utf-8 -*-

"""
Created on Thu Mar 17 19:48:11 2022

@author: chentir
@organization: santec holdings corp.
"""

import os
import clr  # python for .net
import time
from numpy import array

from santec.error_handing_class import instrument_error_strings

ROOT = str(os.path.dirname(__file__)) + '\\DLL\\'
# print(ROOT) #<-- comment in to check if the root was selected properly

PATH1 = 'InstrumentDLL'
# Add in santec.Instrument.DLL
ans = clr.AddReference(ROOT + PATH1)

# print(ans) #<-- comment in to check if the DLL was added properly

from Santec import MPM  # namespace of instrument DLL
from Santec.Communication import CommunicationMethod  # Enumeration Class
from Santec.Communication import GPIBConnectType  # Enumeration Class


class MpmDevice:
    """MPM device class"""

    def __init__(self, interface: str, address: str, port: int = None):
        self._mpm = MPM()
        self.interface = interface
        self.address = address.split('::')[1]
        self.port = port

    def connect_mpm(self):
        """
        Method handling the connection protocol of the MPM.

        Raises:
            Exception: In case failed to connect to the MPM.
        """
        if self.interface == "GPIB":
            mpm_commincation_method = CommunicationMethod.GPIB
            self._mpm.GPIBAddress = int(self.address)
            self._mpm.Bordnumber = 0
            self._mpm.GPIBConnectType = GPIBConnectType.NI4882
        else:
            mpm_commincation_method = CommunicationMethod.TCPIP
            self._mpm.IPAddress = self.address
            self._mpm.port = self.port  # port = 5000

        self._mpm.TimeOut = 5000  # timeout value for MPM

        errorcode = self._mpm.Connect(mpm_commincation_method)
        if errorcode != 0:
            self._mpm.DisConnect()
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        return None

    def get_mods_chans(self):
        """
        Detects all the modules that are mounted on the MPM (looping on the 5 possible slots).
        If the detected module is an MPM-212, then the possible optical channels are numbered 1 and 2
        Else, then the possible optical channels are numbered from 1 to 4.
        If no module is detected then the method returns an empty array.

        Raises:
            Exception: In case no modules were detected on the MPM.

        Returns:
            array: array of arrays (example: [[1,2,3,4],[1,2],[],[],[]])
            Where the item index is the slot number (in the example above slots 0 and 1 contain modules),
            and the items in these sub-arrays are channel numbers.
        """
        self.mods_and_chans = []
        for slotcount in range(5):
            if self._mpm.Information.ModuleEnable[slotcount] is True:
                if self.check_mpm_212(slotcount) is True:
                    self.mods_and_chans.append([1, 2])
                else:
                    self.mods_and_chans.append([1, 2, 3, 4])
            else:
                self.mods_and_chans.append([])
        if len(self.mods_and_chans) == 0:
            raise Exception('No modules/channels were detected')
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
        flag_215 = False
        flag_213 = False
        slot = 0
        count_215 = 0

        for slotcount in range(5):
            if self._mpm.Information.ModuleEnable[slotcount] is True:
                flag_215 = self.check_mpm_215(slotcount)
                flag_213 = self.check_mpm_213(slotcount)
                slot += 1
                if flag_215 is True:
                    count_215 += 1

        if flag_215 is True and count_215 != slot:
            raise Exception("MPM-215 can't use with other modules")

        return flag_215, flag_213

    def check_mpm_215(self, slotnum: int) -> bool:
        """
        Checks if the mounted module at slot number slotnum is an MPM-215.

        Args:
            slotnum (int): The module number (0~4).

        Returns:
            bool: True if a MPM-215 is detected.
        """
        return bool(self._mpm.Information.ModuleType[slotnum] == "MPM-215")

    def check_mpm_213(self, slotnum: int) -> bool:
        """
        Checks if the mounted module at slot number slotnum is an MPM-213.

        Args:
            slotnum (int): The module number (0~4).

        Returns:
            bool: True if an MPM-213 is detected.
        """
        return bool(self._mpm.Information.ModuleType[slotnum] == "MPM-213")

    def check_mpm_212(self, slotnum: int) -> bool:
        """
        Checks if the mounted module at slot number slotnum is an MPM-212.

        Args:
            slotnum (int): The module number (0~4).

        Returns:
            bool: True if an MPM-212 is detected.
        """
        return bool(self._mpm.Information.ModuleType[slotnum] == "MPM-212")

    def get_range(self) -> array:
        """
        Gets the measurement dynamic range of the MPM module.
        Depending on the module type, the dynamic range varies.
        This method calls check_mpm_215 and check_mpm_213 methods.

        Returns:
            array:  MPM-215: [1]
                    MPM-213: [1,2,3,4]
                    Others:  [1,2,3,4,5]
        """
        self.rangedata = []
        if self.check_mpm_215 is True:
            self.rangedata = [1]
        elif self.check_mpm_213 is True:
            # 213 have 4 ranges
            self.rangedata = [1, 2, 3, 4]
        else:
            self.rangedata = [1, 2, 3, 4, 5]
        return None

    def set_range(self, powerrange):
        """
        Sets the dynamic range of the MPM.

        Args:
            powerrange (int): check get_range method for
            available dynamic ranges.

        Raises:
            Exception:  In case the MPM is busy.
                        In case wrong value for powerrange is entered
        """
        errorcode = self._mpm.Set_Range(powerrange)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        return None

    def zeroing(self):
        """
        Performs a Zeroing on all MPM channels.
        All the channels must be closed with respective back caps before
        performing this operation.

        Raises:
            Exception:  In case the MPM is busy;
                        In case wrong value for powerrange is entered;
                        In case the MPM  returns an error.


        Returns:
            str: Success.
        """
        errorcode = self._mpm.Zeroing()

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        return instrument_error_strings(errorcode)

    def get_averaging_time(self):
        """
        Gets the averaging time of the MPM.

        Raises:
            Exception:  In case the MPM is busy;
                        In case of communication failure.

        Returns:
            float: averaging time
        """
        errorcode, self.averaging_time = self._mpm.Get_Averaging_Time(0)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        return self.averaging_time

    def logging_start(self):
        """
        MPM starts logging.

        Raises:
            Exception:  In case the MPM is busy.
        """
        errorcode = self._mpm.Logging_Start()
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

    def logging_stop(self, except_if_error=True):
        """
        MPM stops logging.

        Args:
            except_if_error (bool, optional): Set True if raising exception is
            needed within this method. Else, i.e. if this method is inserted within STS
            then set False so the exception  will be raised from STS method.
            Defaults to True.

        Raises:
            Exception: In case the MPM is busy.
        """
        errorcode = self._mpm.Logging_Stop()
        if errorcode != 0 and except_if_error is True:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

    def get_each_chan_logdata(self, slot_num: int, chan_num: int) -> array:
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
        errorcode, logdata = self._mpm.Get_Each_Channel_Logdata(slot_num, chan_num, None)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return logdata

    def set_logging_parameters(self, startwave, stopwave, step, speed):
        """
        Sets the logging parameter for MPM integrated in STS

        Args:
            startwave (float): Input the start wavelength value.
            stopwave (float): Input the stop wavelength value.
            step (float): Input the sweep sweep_step wavelength value.
            speed (float): Input the sweep sweep_speed value.

        Raises:
            RuntimeError: When trigger signal is not detected
            RuntimeError: if the MPM didn't record data
        """
        errorcode = self._mpm.Set_Logging_Paremeter_for_STS(startwave,
                                                            stopwave,
                                                            step,
                                                            speed,
                                                            self._mpm.Measurement_Mode.Freerun)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        return instrument_error_strings(errorcode)

    def disconnect(self):
        self._mpm.DisConnect()

    def wait_log_completion(self, sweepcount: int):

        # Check MPM Loging stopped
        status = 0  # MPM Logging status  0: During logging 1: Completed, -1:stopped, 10:stopped
        logging_point = 0

        # constantly get the status in a loop. Increase the MPM timeout for this process,

        while status == 0:
            errorcode, status, logging_point = self._mpm.Get_Logging_Status(0,
                                                                            0)  # Updates status, which should break us out of the loop.
            break

        if errorcode == -999:
            errorstr = "MPM Trigger received an error! Please check trigger cable connection."
            raise RuntimeError(errorstr)

        if (
                errorcode != 0 and status != -1):  # it's a success if either the error code is 0, or the status is -1. Otherwise, throw.
            raise RuntimeError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None
