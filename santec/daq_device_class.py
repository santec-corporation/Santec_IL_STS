# -*- coding: utf-8 -*-

"""
DAQ Device Class.

@organization: Santec Holdings Corp.
"""

# Importing SPU class from the DLL
from Santec import SPU

# Importing instrument error strings
from .error_handling_class import InstrumentError, instrument_error_strings

# Import program logger
from . import logger


class SpuDevice:
    """
    SPU device class to control and command the DAQ device.

    Attributes:
        __spu (SPU): The SPU class from the namespace Santec.
        _device_name (str): The name of the DAQ device.

    Parameters:
        device_name (str): The name of the DAQ device.

    Raises:
        None
    """
    def __init__(self,
                 device_name: str):
        logger.info("Initializing Spu Instrument class.")
        self.__spu = SPU()
        self._device_name = device_name
        logger.info(f"Spu Device details, Device Name: {device_name}")

    def connect(self) -> None:
        """
        Establishes connection with a DAQ board.

        Raises:
            InstrumentError: If the connection fails with an error code.
        """
        logger.info("Connect Spu device")
        self.__spu.DeviceName = str(self._device_name)
        device_answer = None
        try:
            errorcode, device_answer = self.__spu.Connect("")
            if errorcode != 0:
                logger.critical("Spu instrument connection error ",
                                str(errorcode) + ": " + instrument_error_strings(errorcode))
                raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        except InstrumentError as e:
            print(f"Error occurred: {e}")
        logger.info(f"Connected to Spu device. device_answer: {device_answer}")

    def set_logging_parameters(self,
                               start_wavelength: float,
                               stop_wavelength: float,
                               sweep_speed: float,
                               tsl_actual_step: float) -> None:
        """
        Set SPU logging parameters for DAQ sampling.

        Parameters:
            start_wavelength (float): Start wavelength value of the sweep.
            stop_wavelength (float): Stop wavelength value of the sweep.
            sweep_speed (float): Speed value of the sweep.
            tsl_actual_step (float): Step wavelength value of the sweep.

        Raises:
            InstrumentError: If setting the logging parameters to the DAQ device fails.
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
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"SPU logging params set.")

    def sampling_start(self) -> None:
        """ Starts the SPU sampling """
        logger.info("SPU sampling start")
        errorcode = self.__spu.Sampling_Start()
        if errorcode != 0:
            logger.error("Error while SPU sampling start, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("SPU sampling started.")

    def sampling_wait(self) -> None:
        """ SPU wait for sampling """
        logger.info("SPU sampling wait")
        errorcode = self.__spu.Waiting_for_sampling()
        if errorcode != 0:
            logger.error("Error while SPU sampling wait, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("SPU sampling wait done.")

    def get_sampling_raw_data(self) -> tuple[list[float], list[float]]:
        """
        Gets the raw sampling data from the DAQ device.

        Raises:
            InstrumentError: If getting the raw sampling data from the DAQ device fails.

        Returns:
            tuple[list[float], list[float]]: A tuple containing two lists:
                - The first list contains the TSL trigger data of a float type.
                - The second list contains the power monitor data of a float type.
        """
        logger.info("SPU get sampling raw data")
        errorcode, trigger, monitor = self.__spu.Get_Sampling_Rawdata(
            None, None)
        if errorcode != 0:
            logger.error("Error while getting SPU sampling raw data, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"SPU sampling raw data acquired, data length: trigger={len(trigger)}, monitor={len(monitor)}")
        return trigger, monitor

    def disconnect(self) -> None:
        """
        Disconnects the connection from the DAQ device.

        Raises:
              RuntimeError: If disconnecting the DAQ device fails.
        """
        try:
            self.__spu.DisConnect()
            logger.info("SPU connection disconnected.")
        except RuntimeError as e:
            logger.error(f"Error while disconnecting the SPU connection, {e}")
