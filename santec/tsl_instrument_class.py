# -*- coding: utf-8 -*-

"""
Created on Thu Mar 17 11:33:52 2022

@author: chentir
@organization: santec holdings corp.
"""

# Basic imports
import os
import numpy
import clr

# Importing instrument error strings
from santec.error_handing_class import instrument_error_strings

# Adding Instrument DLL to the reference
ROOT = str(os.path.dirname(__file__)) + '\\DLL\\'
# print(ROOT)    """ <-- uncomment in to check if the root was selected properly """

PATH1 = 'InstrumentDLL'
ans = clr.AddReference(ROOT + PATH1)  # Add in santec.Instrument.DLL
# print(ans) #<-- comment in to check if the DLL was added properly

# Importing from Santec namespace
from Santec import TSL, ExceptionCode, CommunicationTerminator
from Santec.Communication import CommunicationMethod, GPIBConnectType


class TslDevice:
    """ TSL device class """

    def __init__(self, interface: str, address: str, port: int = 5000):
        self.__tsl = TSL()
        self.interface = interface
        self.address = address
        self.port = port

        self.max_power = None

        self.spec_max_wav = None
        self.spec_min_wav = None

        self.power = None
        self.actual_step = None
        self.start_wavelength = None
        self.stop_wavelength = None
        self.sweep_step = None
        self.sweep_speed = None

        self.return_table = None


        if interface not in ("GPIB", "LAN", "USB"):
            raise Exception('This interface is not supported')

    def __str__(self):
        return "TslDevice"

    # TSL Connect
    def ConnectTSL(self):
        """
        Method handling the connection protocol of the TSL.
        It also gets TSL specs: Min and Max wavelength and Max output power.

        Raises:
            Exception: In case failed to connect to the TSL.


          ---Property setting before "Connect"------------

        GPIB Terminate can set by TSL Front panel.
        In this code, GPIB terminator must match TSL's GPIB terminator.
        When LAN/USB Communication, terminator becomes "CR"  at TSL.
        """

        errorcode = 0

        # When GPIB communication
        if self.interface == "GPIB":
            self.__tsl.Terminator = CommunicationTerminator.CrLf
            self.__tsl.GPIBAddress = int(self.address.split('::')[1])
            self.__tsl.GPIBBoard = int(self.address.split('::')[0][-1])
            self.__tsl.GPIBConnectType = GPIBConnectType.NI4882  # For Keysight cable use: GPIBConnectType.KeysightIO
            errorcode = self.__tsl.Connect(CommunicationMethod.GPIB)

        # When LAN Communication
        elif self.interface == "LAN":
            self.__tsl.Terminator = CommunicationTerminator.Cr
            self.__tsl.IPAddress = self.address
            self.__tsl.Port = self.port  # port =5000
            errorcode = self.__tsl.Connect(CommunicationMethod.TCPIP)

        # When USB communication
        elif self.interface == "USB":
            # USB DeviceID is defined uint32, So must be change variable type to unit32
            # this code type change with numpy array
            ar_address = numpy.array([self.address], dtype="uint32")
            self.__tsl.DeviceID = ar_address[0]  # self.address
            self.__tsl.Terminator = CommunicationTerminator.Cr
            errorcode = self.__tsl.Connect(CommunicationMethod.USB)

        else:
            print("There was NO interface")
            errorcode = -1

        if errorcode != 0:
            self.__tsl.DisConnect()
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        self.get_spec_wavelength()  # Gets TSL spec wavelength(nm)

        if not self.get_550_flag():
            self.get_max_power()

        return None

    def Query(self, command: str):
        """ Queries a command to the instrument and returns a string """
        command = command.upper()
        return self.__tsl.query(command)

    def Write(self, command: str):
        """ Writes a command to the instrument """
        command = command.upper()
        return self.__tsl.write(command)

    def get_550_flag(self):
        """
        Checks if the connected TSL is TSL-550/TSL-710

        Returns:
            bool: True if TSL-550/TSL-710; else False.
        """

        tsl_name = self.__tsl.Information.ProductName

        return tsl_name in ("TSL-550", "TSL-710")

    def get_spec_wavelength(self):
        """
        Gets Min and Max wavelengths supported by the connected TSL.

        Raises:
            Exception: In case couldn't get spec min and max wavelengths from the TSL.
        """

        errorcode, self.spec_min_wav, self.spec_max_wav = self.__tsl.Get_Spec_Wavelength(0, 0)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None

    def get_sweep_speed_table(self):
        """
        Returns sweep sweep_speed table of TSL-570:
        [1,2,5,10,20,50,100,200] (nm/sec)

        Raises:
            Exception: "DeviceError" when other TSL is connected.

        Returns:
            array: Sweep speeds allowed by the TSL-570.
        """

        errorcode, table = self.__tsl.Get_Sweep_Speed_table(None)
        self.return_table = []

        # This function only support "TSL-570"
        # When other TSL connected, errorcode return "DeviceError"
        if errorcode == ExceptionCode.DeviceError:
            errorcode = 0
        else:
            for item in table:
                self.return_table.append(item)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

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

        errorcode, self.max_power = self.__tsl.Get_APC_Limit_for_Sweep(self.spec_min_wav,
                                                                       self.spec_max_wav,
                                                                       0.0)

        if errorcode == ExceptionCode.DeviceError:
            self.max_power = 999
            errorcode = 0

        if errorcode != 0:
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
        self.power = power
        errorcode = self.__tsl.Set_APC_Power_dBm(self.power)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        errorcode = self.__tsl.TSL_Busy_Check(3000)
        if errorcode != 0:
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

        errorcode = self.__tsl.Set_Wavelength(wavelength)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        errorcode = self.__tsl.TSL_Busy_Check(3000)
        if errorcode != 0:
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
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))

        self.tsl_busy_check()

        return None

    def soft_trigger(self):
        """
        Issues a soft trigger to start TSL sweep.

        Raises:
            RuntimeError: In case TSL is not in Standby mode, or if TSL cannot start the sweep.
        """
        errorcode = self.__tsl.Set_Software_Trigger()
        if errorcode != 0:
            raise RuntimeError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None

    def start_sweep(self):
        """
        Runs the wavelength sweep. Method to be used when TSL is not connected
        to STS.

        Raises:
            Exception: In case TSL doesn't start the sweep.
        """
        errorcode = self.__tsl.Sweep_Start()
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None

    def stop_sweep(self, except_if_error=True):
        """
        Stops the sweep.

        Args:
            except_if_error (bool, optional): Set True if raising exception is
            needed within this method. Else, i.e. if this method is inserted within STS
            then set False so the exception  will be raised from STS method.
            Defaults to True.

        Raises:
            Exception: In case failure in stopping the TSL.
        """
        errorcode = self.__tsl.Sweep_Stop()
        if errorcode != 0 and except_if_error is True:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None

    def tsl_busy_check(self):
        """
        Checks if the TSL is busy with other tasks.
        Default timeout = 3000 ms

        Raises:
            Exception: In case no response from TSL after timeout.
        """
        errorcode = self.__tsl.TSL_Busy_Check(3000)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
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
        _status = {
            1: self.__tsl.Sweep_Status.Standby,
            2: self.__tsl.Sweep_Status.Running,
            3: self.__tsl.Sweep_Status.Pausing,
            4: self.__tsl.Sweep_Status.WaitingforTrigger,
            5: self.__tsl.Sweep_Status.Returning
        }
        errorcode = self.__tsl.Waiting_For_Sweep_Status(waiting_time, _status[sweep_status])

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + instrument_error_strings(errorcode))
        return None

    def Disconnect(self):
        """
        Disconnects the TSL.
        """
        self.__tsl.DisConnect()
        return None
