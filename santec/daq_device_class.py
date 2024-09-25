# -*- coding: utf-8 -*-

"""
DAQ Device Class.

@organization: Santec Holdings Corp.
"""

# Importing SPU class from the DLL
from Santec import SPU

# Importing instrument error strings
from santec.error_handing_class import instrument_error_strings

# Import program logger
from . import logger


class SpuDevice:
    def __init__(self,
                 device_name: str):
        logger.info("Initializing Spu Instrument class.")
        self.__spu = SPU()
        self._deviceName = device_name
        logger.info(f"Spu Device details, Device Name: {device_name}")

    def connect_spu(self):
        """
        Connects the DAQ board (SPU Connect).

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        logger.info("Connect Spu device")
        self.__spu.DeviceName = str(self._deviceName)

        errorcode, device_answer = self.__spu.Connect("")
        if errorcode != 0:
            logger.critical("Spu instrument connection error ",
                            str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"Connected to Spu device, error string: {instrument_error_strings(errorcode)}")
        return instrument_error_strings(errorcode)

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
        logger.info(f"Set SPU logging params: start_wavelength={start_wavelength}, stop_wavelength={stop_wavelength}, "
                    f"sweep_speed={sweep_speed}, tsl_actual_step={tsl_actual_step}")
        errorcode = self.__spu.Set_Sampling_Parameter(start_wavelength,
                                                      stop_wavelength,
                                                      sweep_speed,
                                                      tsl_actual_step)

        if errorcode != 0:
            logger.error("Error while setting SPU logging params, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"SPU logging params set. Error string:{instrument_error_strings(errorcode)}")
        return instrument_error_strings(errorcode)

    def sampling_start(self):
        """ Starts the SPU sampling """
        logger.info("SPU sampling start")
        errorcode = self.__spu.Sampling_Start()
        if errorcode != 0:
            logger.error("Error while SPU sampling start, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise RuntimeError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("SPU sampling started.")

    def sampling_wait(self):
        """ SPU wait for sampling """
        logger.info("SPU sampling wait")
        errorcode = self.__spu.Waiting_for_sampling()
        if errorcode != 0:
            logger.error("Error while SPU sampling wait, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise RuntimeError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("SPU sampling wait done.")

    def get_sampling_raw_data(self):
        """
        SPU get raw data

        returns:
        A list of trigger and monitor data
        """
        logger.info("SPU get sampling raw data")
        errorcode, trigger, monitor = self.__spu.Get_Sampling_Rawdata(
            None, None)
        if errorcode != 0:
            logger.error("Error while getting SPU sampling raw data, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"SPU sampling raw data acquired, data length: trigger={len(trigger)}, monitor={len(monitor)}")
        return trigger, monitor

    def disconnect(self):
        """
        Disconnects the SPU device
        """
        try:
            self.__spu.DisConnect()
            logger.info("SPU connection disconnected.")
        except Exception as e:
            logger.error(f"Error while disconnecting the SPU connection, {e}")
