# -*- coding: utf-8 -*-

"""
Created on Thu Mar 24 20:04:16 2022

@author: chentir
@organization: santec holdings corp.
"""

# Basic imports
import os
import clr

# Importing instrument error strings
from santec.error_handing_class import instrument_error_strings

# Adding Instrument DLL to the reference
ROOT = str(os.path.dirname(__file__)) + '\\DLL\\'
# print(ROOT)    """ <-- uncomment in to check if the root was selected properly """

PATH1 = 'InstrumentDLL'
ans = clr.AddReference(ROOT + PATH1)  # Add in santec.Instrument.DLL
# print(ans) #<-- comment in to check if the DLL was added properly


# Importing SPU class from the DLL
from Santec import SPU


class SpuDevice:
    """ DAQ board device class """

    def __init__(self, device_name: str):
        self.__spu = SPU()
        self.__deviceName = device_name

    def ConnectSPU(self):
        """
        Connects the DAQ board (SPU Connect).

        Parameters
        ----------
        device_name : TYPE
            DESCRIPTION.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        self.__spu.DeviceName = str(self.__deviceName)

        errorcode, device_answer = self.__spu.Connect("")
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        return instrument_error_strings(errorcode)

    # SPU Set logging parameter
    def set_logging_parameters(self,
                               start_wavelength,
                               stop_wavelength,
                               sweep_speed,
                               tsl_actual_step):
        """
        Set SPU sampling parameters
        Args:
            start_wavelength (float): Input the start wavelength value.
            stop_wavelength (float): Input the stop wavelength value.
            sweep_speed (float): Input the sweep sweep_speed value.
            tsl_actual_step (float): Input the sweep sweep_step wavelength value.

        Raises:
            Exception
        """

        errorcode = self.__spu.Set_Sampling_Parameter(start_wavelength,
                                                      stop_wavelength,
                                                      sweep_speed,
                                                      tsl_actual_step)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        return instrument_error_strings(errorcode)

    def sampling_start(self):
        """ Starts the SPU sampling """
        errorcode = self.__spu.Sampling_Start()
        if errorcode != 0:
            raise RuntimeError(str(errorcode) + ": " + instrument_error_strings(errorcode))

    def sampling_wait(self):
        """ SPU wait for sampling """
        errorcode = self.__spu.Waiting_for_sampling()
        if errorcode != 0:
            raise RuntimeError(str(errorcode) + ": " + instrument_error_strings(errorcode))

    def get_sampling_raw(self):
        """
        SPU get raw data

        returns:
        A list of trigger and monitor data
        """
        errorcode, trigger, monitor = self.__spu.Get_Sampling_Rawdata(
            None, None)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return trigger, monitor

    def Disconnect(self):
        """
        Disconnects the spu device
        """
        self.__spu.DisConnect()
