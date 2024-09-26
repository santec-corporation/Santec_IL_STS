# -*- coding: utf-8 -*-

"""
TSL Instrument Class.

@organization: Santec Holdings Corp.
"""

# Importing from Santec namespace
from Santec import TSL, ExceptionCode, CommunicationTerminator
from Santec.Communication import CommunicationMethod, GPIBConnectType

# Importing instrument error strings
from santec.error_handing_class import instrument_error_strings

# Import program logger
from . import logger


class TslData:
    max_power = None
    spec_max_wav = None
    spec_min_wav = None
    power = None
    actual_step = None
    start_wavelength = None
    stop_wavelength = None
    sweep_step = None
    sweep_speed = None
    return_table = None


class TslInstrument(TslData):
    def __init__(self,
                 interface: str,
                 address: str,
                 port: int = 5000,
                 gpib_connect_type="NI"):
        logger.info("Initializing Tsl Instrument class.")
        self.__tsl = TSL()
        self.interface = interface.lower()
        self.address = address
        self.port = port
        self.gpib_connect_type = gpib_connect_type.lower()
        logger.info(f"Tsl Instrument details, Interface: {self.interface}, Address: {self.address},"
                    f" Port: {self.port}, Gpib connect type: {self.gpib_connect_type}")

        if interface not in ("GPIB", "LAN", "USB"):
            logger.warning(f"Invalid interface type, this interface {interface} is not supported")
            raise Exception(f"This interface {interface} is not supported")

    def __str__(self):
        return "TslInstrument"

    def connect(self):
        """
        Method handling the connection protocol of the TSL.
        It also gets TSL specs: Min and Max wavelength and Max output power.

        Raises:
            Exception: In case failed to connect to the TSL.

          ---Property setting before "Connect"------------

        GPIB Terminate can be set by TSL Front panel.
        In this code, GPIB terminator must match TSL's GPIB terminator.
        When LAN/USB Communication, terminator becomes "CR" at TSL.
        """
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
            errorcode = self.__tsl.Connect(CommunicationMethod.GPIB)

        elif "lan" in self.interface:
            logger.info("Connect Tsl instrument, type LAN")
            self.__tsl.Terminator = CommunicationTerminator.Cr
            self.__tsl.IPAddress = self.address
            self.__tsl.Port = self.port
            errorcode = self.__tsl.Connect(CommunicationMethod.TCPIP)

        elif "usb" in self.interface:
            logger.info("Connect Tsl instrument, type USB")
            self.__tsl.DeviceID = int(self.address[-1])
            self.__tsl.Terminator = CommunicationTerminator.Cr
            errorcode = self.__tsl.Connect(CommunicationMethod.USB)

        else:
            errorcode = -1
            logger.info("There was NO interface specified!!!")
            raise Exception("There was NO interface specified!!!")

        if errorcode != 0:
            self.__tsl.DisConnect()
            logger.critical("Tsl instrument connection error ", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        logger.info("Connected to Tsl instrument.")

        self.get_spec_wavelength()  # Gets TSL spec wavelength(nm)
        if not self.get_550_flag():
            self.get_max_power()
        return None

    def query_tsl(self, command: str):
        """ Queries a command to the instrument and returns a string """
        command = command.upper()
        logger.info(f"Querying TSL, command: {command}")
        try:
            status, response = self.__tsl.Echo(command, "")
            return status, response
        except Exception as e:
            logger.error(f"Failed to query TSL with command '{command}': {e}")
            raise RuntimeError(f"query_tsl failed: {e}")

    def write_tsl(self, command: str):
        """ Writes a command to the instrument """
        command = command.upper()
        logger.info(f"Writing to TSL, command: {command}")
        try:
            status = self.__tsl.Write(command)
            return status
        except Exception as e:
            logger.error(f"Failed to write to TSL with command '{command}': {e}")
            raise RuntimeError(f"write_tsl failed: {e}")

    def read_tsl(self):
        """ Reads from the instrument """
        try:
            status, response = self.__tsl.Read("")
            return status, response
        except Exception as e:
            logger.error(f"Failed to read TSL, {e}")
            raise RuntimeError(f"read_tsl failed: {e}")

    def get_550_flag(self):
        """
        Checks if the connected TSL is TSL-550/TSL-710

        Returns:
            bool: True if TSL-550/TSL-710; else False.
        """
        logger.info("Get TSL name")
        tsl_name = self.__tsl.Information.ProductName
        logger.info(f"TSL name: {tsl_name}")
        return tsl_name in ("TSL-550", "TSL-710")

    def get_spec_wavelength(self):
        """
        Gets Min and Max wavelengths supported by the connected TSL.

        Raises:
            Exception: In case couldn't get spec min and max wavelengths from the TSL.
        """
        logger.info("Get TSL spec wavelength")
        errorcode, self.spec_min_wav, self.spec_max_wav = self.__tsl.Get_Spec_Wavelength(0, 0)

        logger.info(f"TSL spec wavelength: min_wav={self.spec_min_wav}, max_wav={self.spec_max_wav}")
        if errorcode != 0:
            logger.warning("Error while getting TSL spec wavelength", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None

    def get_sweep_speed_table(self) -> list:
        """
        Returns sweep sweep_speed table of TSL-570:
        [1,2,5,10,20,50,100,200] (nm/sec)

        Raises:
            Exception: "DeviceError" when other TSL is connected.

        Returns:
            array: Sweep speeds allowed by the TSL-570.
        """
        logger.info("Get TSL speed table")
        errorcode, table = self.__tsl.Get_Sweep_Speed_table(None)
        self.return_table = []

        # This function only supports "TSL-570"
        # When other TSL connected, errorcode return "DeviceError"
        if errorcode == ExceptionCode.DeviceError:
            errorcode = 0
        else:
            for item in table:
                self.return_table.append(item)

        if errorcode != 0:
            logger.error("Error while getting TSL speed table",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL speed table received.")
        return self.return_table

    def get_max_power(self):
        """
        This method is used when TSL-570 is connected.
        Returns the max output power that can be delivered by the connected
        TSL.
        The method will call TSL object properties:min and max wavelength
        (spec_min_wav; spec_max_wav resp.)

        Otherwise, DeviceError errorcode is returned.

        Raises:
            Exception: In case TSL doesn't return the value.
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
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None

    def set_power(self, power):
        """
        Sets the output power of the TSL.

        Args:
            power (float): Setting output power.

        Raises:
            Exception: In case setting the output power is failed.
            Exception: In case TSL is busy.
        """
        logger.info(f"Set TSL power: {power}")
        self.power = power
        errorcode = self.__tsl.Set_APC_Power_dBm(self.power)

        if errorcode != 0:
            logger.error(f"Error while setting TSL power", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        errorcode = self.__tsl.TSL_Busy_Check(3000)

        if errorcode != 0:
            logger.error(f"Error while setting TSL power", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None

    def set_wavelength(self, wavelength):
        """
        Sets the TSL at a specific wavelength.

        Args:
            wavelength (float): setting wavelength.

        Raises:
            Exception: In case setting the wavelength is failed.
            Exception: In case TS is busy.
        """
        logger.info(f"Set TSL wavelength: {wavelength}")
        errorcode = self.__tsl.Set_Wavelength(wavelength)

        if errorcode != 0:
            logger.error(f"Error while setting TSL wavelength", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        errorcode = self.__tsl.TSL_Busy_Check(3000)

        if errorcode != 0:
            logger.error(f"Error while setting TSL wavelength", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None


    def set_sweep_parameters(self, start_wavelength, stop_wavelength, sweep_step, sweep_speed):
        """
        Setting the sweep parameters and pass them in the TSL object.

        Args:
            start_wavelength (float): Input the start wavelength value.
            stop_wavelength (float): Input the stop wavelength value.
            sweep_step (float): Input the sweep sweep_step wavelength value.
            sweep_speed (float): Input the sweep sweep_speed value.

        Raises:
            Exception: In case the pass method fails
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
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        logger.info(f"TSL sweep params set, actual_step={self.actual_step}")
        self.tsl_busy_check()
        return None

    def soft_trigger(self):
        """
        Issues a soft trigger to start TSL sweep.

        Raises:
            RuntimeError: In case TSL is not in Standby mode, or if TSL cannot start the sweep.
        """
        logger.info("Issue soft trigger")
        errorcode = self.__tsl.Set_Software_Trigger()

        if errorcode != 0:
            logger.error("Error while setting TSL soft trigger", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise RuntimeError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("Issue soft trigger done.")
        return None

    def start_sweep(self):
        """
        Runs the wavelength sweep. Method to be used when TSL is not connected
        to STS.

        Raises:
            Exception: In case TSL doesn't start the sweep.
        """
        logger.info("TSL start sweep")
        errorcode = self.__tsl.Sweep_Start()

        if errorcode != 0:
            logger.error("Error while starting TSL sweep", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL start sweep done.")
        return None

    def stop_sweep(self, except_if_error=True):
        """
        Stops the sweep.

        Args:
            except_if_error (bool, optional): Set True if raising exception is
            needed within this method.
            Else, i.e., if this method is inserted within STS
            then set False so the exception will be raised from STS method.
            Defaults to True.

        Raises:
            Exception: In case failure in stopping the TSL.
        """
        logger.info("TSL stop sweep")
        errorcode = self.__tsl.Sweep_Stop()

        if errorcode != 0 and except_if_error is True:
            logger.error("Error while stopping TSL sweep", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL stop sweep done.")
        return None

    def tsl_busy_check(self):
        """
        Checks if the TSL is busy with other tasks.
        Default timeout = 3000 ms

        Raises:
            Exception: In case, no response from TSL after timeout.
        """
        logger.info("TSL busy check")
        errorcode = self.__tsl.TSL_Busy_Check(3000)

        if errorcode != 0:
            logger.error("Error while TSL busy check", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL busy check done.")
        return None

    def wait_for_sweep_status(self, waiting_time: int, sweep_status: int):
        """
        Wait until the TSL is set to a specified status prior the sweeping process.


        Args:
            waiting_time (int): Waiting time (milliseconds)
            sweep_status (int): Key value (1~5) of the _status dictionary.
                                1: Standby
                                2: Running
                                3: Pause
                                4: Waiting for trigger
                                5:  Return

        Raises:
            Exception: In case TSL is not set to the specified status after timeout.
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
            logger.error("Error while TSL wait for sweep status", str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("TSL wait for sweep status done.")

    def disconnect(self):
        """
        Disconnects the TSL connection.
        """
        try:
            self.__tsl.DisConnect()
            logger.info("TSL connection disconnected.")
        except Exception as e:
            logger.error(f"Error while disconnecting the TSL connection, {e}")
