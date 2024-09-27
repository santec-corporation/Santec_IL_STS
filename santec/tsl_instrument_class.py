# -*- coding: utf-8 -*-

"""
TSL Instrument Class.

@organization: Santec Holdings Corp.
"""

# Importing from Santec namespace
from Santec import TSL, ExceptionCode, CommunicationTerminator
from Santec.Communication import CommunicationMethod, GPIBConnectType

# Importing instrument error strings
from .error_handing_class import InstrumentError, instrument_error_strings

# Import program logger
from . import logger


class TslData:
    """
    A class to represent the data for a TSL.

    Attributes:
        max_power (float): The maximum power output of the TSL.
        spec_max_wav (float): The maximum wavelength of the spectral range of the TSL.
        spec_min_wav (float): The minimum wavelength of the spectral range of the TSL.
        power (float): The power setting of the TSL.
        actual_step (float): The step wavelength value of the TSL.
        start_wavelength (float): The starting wavelength for the sweep.
        stop_wavelength (float): The stopping wavelength for the sweep.
        sweep_step (float): The step wavelength of a sweep.
        sweep_speed (float): The speed of a sweep.
        sweep_speed_table (list): A table of TSL sweep speeds.
    """
    max_power: float = 0.0
    spec_max_wav: float = 0.0
    spec_min_wav: float = 0.0
    power: float = 0.0
    actual_step: float = 0.0
    start_wavelength: float = 0.0
    stop_wavelength: float = 0.0
    sweep_step: float = 0.0
    sweep_speed: float = 0.0
    sweep_speed_table: list = []


class TslInstrument(TslData):
    """
    Class to control and command the TSL instrument.

    Attributes:
        __tsl (TSL): The TSL class from the namespace Santec.
        interface (str): The TSL instrument interface or connection type.
                        Example: GPIB, LAN or USB
        address (str): The connection address of the TSL.
        port (int): In case of LAN connection, the port number of the TSL.
        gpib_connect_type (str): In case of GPIB connection, the connection type of the GPIB,
                                if National Instruments, gpib_connect_type="NI",
                                if Keysight Instruments, gpib_connect_type="Keysight".

    Parameters:
        interface (str): The TSL instrument interface or connection type.
                        Example: GPIB, LAN or USB
        address (str): The connection address of the TSL.
        port (int): In case of LAN connection, the port number of the TSL.
                    Default value = 5000.
        gpib_connect_type (str): In case of GPIB connection, the connection type of the GPIB,
                                if National Instruments, gpib_connect_type="NI",
                                if Keysight Instruments, gpib_connect_type="Keysight".
                                Default: "NI"

    Raises:
        Exception: If the provided interface is not GPIB, LAN or USB.
    """
    def __init__(self,
                 interface: str,
                 address: str,
                 port: int = 5000,
                 gpib_connect_type: str = "NI"):
        logger.info("Initializing Tsl Instrument class.")
        self.__tsl = TSL()
        self.interface = interface.lower()
        self.address = address
        self.port = port
        self.gpib_connect_type = gpib_connect_type.lower()
        logger.info(f"Tsl Instrument details, Interface: {self.interface}, Address: {self.address},"
                    f" Port: {self.port}, Gpib connect type: {self.gpib_connect_type}")

        if interface not in ("GPIB", "LAN", "USB"):
            logger.warning(f"Invalid interface type, this interface {interface} is not supported.")
            raise Exception(f"This interface {interface} is not supported")

    def __str__(self):
        return "TslInstrument"

    def connect(self) -> None:
        """
        Establishes connection with the TSL instrument.

        Raises:
            InstrumentError: If establishing connection fails.
        """
        communication_type = None
        logger.info("Connect Tsl instrument")
        if "gpib" in self.interface:
            logger.info("Connect Tsl instrument, type GPIB")
            self.__tsl.Terminator = CommunicationTerminator.CrLf
            self.__tsl.GPIBAddress = int(self.address.split('::')[1])
            self.__tsl.GPIBBoard = int(self.address.split('::')[0][-1])
            if "ni" in self.gpib_connect_type:
                self.__tsl.GPIBConnectType = GPIBConnectType.NI4882
            elif "keysight" in self.gpib_connect_type:
                self.__tsl.GPIBConnectType = GPIBConnectType.KeysightIO
            communication_type = CommunicationMethod.GPIB

        elif "lan" in self.interface:
            logger.info("Connect Tsl instrument, type LAN")
            self.__tsl.Terminator = CommunicationTerminator.Cr
            self.__tsl.IPAddress = self.address
            self.__tsl.Port = self.port
            communication_type = CommunicationMethod.TCPIP

        elif "usb" in self.interface:
            logger.info("Connect Tsl instrument, type USB")
            self.__tsl.DeviceID = int(self.address[-1])
            self.__tsl.Terminator = CommunicationTerminator.Cr
            communication_type = CommunicationMethod.USB

        try:
            errorcode = self.__tsl.Connect(communication_type)
            if errorcode != 0:
                self.__tsl.DisConnect()
                logger.critical("Tsl instrument connection error ", str(errorcode) + ": " + instrument_error_strings(errorcode))
                raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))

        except InstrumentError as e:
            print(f"Error occurred: {e}")

        logger.info("Connected to Tsl instrument.")
        self.get_spec_wavelength()  # Gets TSL spec wavelength(nm)

        if not self.get_550_flag():
            self.get_max_power()

    def query_tsl(self, command: str) -> tuple[int, str]:
        """
        Queries the TSL instrument with a command,
        and returns the read data from the instrument buffer.

        Parameters:
            command (str): The command to query to the TSL.

        Returns:
              tuple[int, str]:
                - int: status value of the query operation.
                - str: read value of the buffer.

        Raises:
             RuntimeError: If the query operation fails.
        """
        command = command.upper()
        logger.info(f"Querying TSL, command: {command}")
        try:
            status, response = self.__tsl.Echo(command, "")
            return status, response
        except Exception as e:
            logger.error(f"Failed to query TSL with command '{command}': {e}")
            raise RuntimeError(f"query_tsl failed: {e}")

    def write_tsl(self, command: str) -> int:
        """
        Writes a command to the TSL instrument.

        Parameters:
            command (str): The command to write to the TSL.

        Returns:
              int: status value of the write operation.

        Raises:
             RuntimeError: If the write operation fails.
        """
        command = command.upper()
        logger.info(f"Writing to TSL, command: {command}")
        try:
            status = self.__tsl.Write(command)
            return status
        except Exception as e:
            logger.error(f"Failed to write to TSL with command '{command}': {e}")
            raise RuntimeError(f"write_tsl failed: {e}")

    def read_tsl(self) -> tuple[int, str]:
        """
        Reads data from the TSL instrument buffer.

        Returns:
              tuple[int, str]:
                - int: status value of the read operation.
                - str: read value of the buffer.

        Raises:
             RuntimeError: If the read operation fails.
        """
        try:
            status, response = self.__tsl.Read("")
            return status, response
        except Exception as e:
            logger.error(f"Failed to read TSL, {e}")
            raise RuntimeError(f"read_tsl failed: {e}")

    def get_550_flag(self) -> bool:
        """
        Checks if the connected TSL is a TSL-550 or TSL-710.

        Returns:
            bool: True if TSL-550 or TSL-710,
                  else False.
        """
        logger.info("Get TSL name")
        tsl_name = self.__tsl.Information.ProductName
        logger.info(f"TSL name: {tsl_name}")
        return tsl_name in ("TSL-550", "TSL-710")

    def get_spec_wavelength(self) -> None:
        """
        Gets minimum and maximum wavelengths supported by the connected TSL.

        Raises:
            InstrumentError: In case, could not get the spec min and max wavelengths from the TSL.
        """
        logger.info("Get TSL spec wavelength")
        errorcode, self.spec_min_wav, self.spec_max_wav = self.__tsl.Get_Spec_Wavelength(0, 0)

        logger.info(f"TSL spec wavelength: min_wav={self.spec_min_wav}, max_wav={self.spec_max_wav}")
        if errorcode != 0:
            logger.warning("Error while getting TSL spec wavelength", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))

    def get_sweep_speed_table(self) -> list[float]:
        """
        **Note**
            This method works only with a "TSL-570" instrument.

        Returns sweep sweep_speed table of TSL-570:
        Example: [1,2,5,10,20,50,100,200]
                 All values in nm/sec units.

        Raises:
            InstrumentError: "DeviceError" when other TSL is connected.

        Returns:
            list[float]: Table of sweep speeds allowed by the TSL-570.
        """
        logger.info("Get TSL speed table")
        errorcode, table = self.__tsl.Get_Sweep_Speed_table(None)
        self.sweep_speed_table = []

        # This function only supports "TSL-570"
        # When other TSL connected, errorcode return "DeviceError"
        if errorcode == ExceptionCode.DeviceError:
            errorcode = 0
        else:
            for item in table:
                self.sweep_speed_table.append(item)

        if errorcode != 0:
            logger.error("Error while getting TSL speed table",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL speed table received.")
        return self.sweep_speed_table

    def get_max_power(self) -> None:
        """
        **Note**
            This method works only with a "TSL-570" instrument.

        Returns the maximum output power that can be delivered by the connected TSL.

        Raises:
            InstrumentError: In case TSL doesn't return a value.
        """
        logger.info("Get TSL max power.")
        errorcode, self.max_power = self.__tsl.Get_APC_Limit_for_Sweep(self.spec_min_wav,
                                                                       self.spec_max_wav,
                                                                       0.0)
        if errorcode == ExceptionCode.DeviceError:
            self.max_power = 999
            errorcode = 0
        logger.info(f"TSL max power: {self.max_power}")

        if errorcode != 0:
            logger.error("Error while getting TSL max power", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))

    def set_power(self, power: float) -> None:
        """
        Sets the output power of the TSL.

        Parameters:
            power (float): The power value for the TSL to be set at.

        Raises:
            InstrumentError: If setting the output power is fails.
            InstrumentError: If the TSL is busy.
        """
        logger.info(f"Set TSL power: {power}")
        self.power = power
        errorcode = self.__tsl.Set_APC_Power_dBm(self.power)

        if errorcode != 0:
            logger.error(f"Error while setting TSL power", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))

        errorcode = self.__tsl.TSL_Busy_Check(3000)

        if errorcode != 0:
            logger.error(f"Error while setting TSL power", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))

    def set_wavelength(self, wavelength: float) -> None:
        """
        Sets the TSL at a specific wavelength.

        Parameters:
            wavelength (float): The wavelength value for the TSL to be set at.

        Raises:
            InstrumentError: If setting the wavelength is fails.
            InstrumentError: If the TSL is busy.
        """
        logger.info(f"Set TSL wavelength: {wavelength}")
        errorcode = self.__tsl.Set_Wavelength(wavelength)

        if errorcode != 0:
            logger.error(f"Error while setting TSL wavelength", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))

        errorcode = self.__tsl.TSL_Busy_Check(3000)

        if errorcode != 0:
            logger.error(f"Error while setting TSL wavelength", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))


    def set_sweep_parameters(self,
                             start_wavelength: float,
                             stop_wavelength: float,
                             sweep_step: float,
                             sweep_speed: float) -> None:
        """
        Sets the TSL sweep parameters.

        Parameters:
            start_wavelength (float): The starting wavelength for the sweep.
            stop_wavelength (float): The stopping wavelength for the sweep.
            sweep_step (float): The step wavelength of a sweep.
            sweep_speed (float): The speed of a sweep.

        Raises:
            InstrumentError: If setting the TSL sweep parameters fails.
        """
        logger.info(f"Set TSL sweep params: start_wavelength={start_wavelength}, "
                    f"stop_wavelength={stop_wavelength}, sweep_step={sweep_step}, sweep_speed={sweep_speed}")
        self.start_wavelength = start_wavelength
        self.stop_wavelength = stop_wavelength
        self.sweep_step = sweep_step
        self.sweep_speed = sweep_speed
        self.tsl_busy_check()

        errorcode, self.actual_step = self.__tsl.Set_Sweep_Parameter_for_STS(self.start_wavelength,
                                                                             self.stop_wavelength,
                                                                             self.sweep_speed,
                                                                             self.sweep_step,
                                                                             0)

        if errorcode != 0:
            logger.error("Error while setting TSL sweep params", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))

        logger.info(f"TSL sweep params set, actual_step={self.actual_step}")
        self.tsl_busy_check()

    def soft_trigger(self) -> None:
        """
        Issues a soft trigger to start the TSL sweep.

        Raises:
            InstrumentError: In case TSL is not in Standby mode, or if TSL cannot start the sweep.
        """
        logger.info("Issue soft trigger")
        errorcode = self.__tsl.Set_Software_Trigger()

        if errorcode != 0:
            logger.error("Error while setting TSL soft trigger",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("Issue soft trigger done.")

    def start_sweep(self) -> None:
        """
        Starts the TSL sweep.
        Method to be used when TSL is not connected to STS.

        Raises:
            InstrumentError: In case TSL doesn't start the sweep.
        """
        logger.info("TSL start sweep")
        errorcode = self.__tsl.Sweep_Start()

        if errorcode != 0:
            logger.error("Error while starting TSL sweep",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL start sweep done.")

    def stop_sweep(self, except_if_error: bool = True):
        """
        Stops the TSL sweep.

        Parameters:
            except_if_error (bool | optional): Set True if raising exception is needed within this method.
            Else, i.e.,
            if this method is inserted within STS then set False
            so the exception will be raised from STS method.
            Default value: True.

        Raises:
            InstrumentError: In case of failure in stopping the TSL sweep.
        """
        logger.info("TSL stop sweep")
        errorcode = self.__tsl.Sweep_Stop()

        if errorcode != 0 and except_if_error is True:
            logger.error("Error while stopping TSL sweep",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL stop sweep done.")

    def tsl_busy_check(self) -> None:
        """
        Checks if the TSL is busy performing other operations.
        Default timeout = 3000 ms

        Raises:
            InstrumentError: In case, no response from TSL after timeout.
        """
        logger.info("TSL busy check")
        errorcode = self.__tsl.TSL_Busy_Check(3000)

        if errorcode != 0:
            logger.error("Error while TSL busy check",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL busy check done.")

    def wait_for_sweep_status(self,
                              waiting_time: int,
                              sweep_status: int) -> None:
        """
        Wait until the TSL is set to a specified status prior the sweeping process.


        Parameters:
            waiting_time (int): Waiting time (milliseconds) before setting a sweep status.
            sweep_status (int): Set the sweep status of the TSL.
                                Sweep status values:
                                1: Standby
                                2: Running
                                3: Pause
                                4: Waiting for trigger
                                5: Return

        Raises:
            InstrumentError: In case TSL is not set to the specified sweep status after timeout.
        """
        logger.info("TSL wait for sweep status")
        _status = {
            1: self.__tsl.Sweep_Status.Standby,
            2: self.__tsl.Sweep_Status.Running,
            3: self.__tsl.Sweep_Status.Pausing,
            4: self.__tsl.Sweep_Status.WaitingforTrigger,
            5: self.__tsl.Sweep_Status.Returning
        }
        errorcode = self.__tsl.Waiting_For_Sweep_Status(waiting_time, _status[sweep_status])

        if errorcode != 0:
            logger.error("Error while TSL wait for sweep status",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL wait for sweep status done.")

    def disconnect(self) -> None:
        """
        Disconnects the connection from the TSL instrument.

        Raises:
              RuntimeError: If disconnecting the TSL instrument fails.
        """
        try:
            self.__tsl.DisConnect()
            logger.info("TSL connection disconnected.")
        except RuntimeError as e:
            logger.error(f"Error while disconnecting the TSL connection, {e}")
