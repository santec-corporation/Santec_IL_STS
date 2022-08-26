# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 11:33:52 2022

@author: chentir
"""

import os
import numpy
import clr # python for .net

ROOT = str(os.path.dirname(__file__))+'\\DLL\\'
print(ROOT)

PATH1 ='InstrumentDLL'
#Add  santec.Instrument.DLL
ans = clr.AddReference(ROOT+PATH1)

print (ans)
from Santec import TSL, ExceptionCode                  #　namespace of instrument DLL
from Santec import CommunicationTerminator
from Santec.Communication import CommunicationMethod
from Santec.Communication import GPIBConnectType

from error_handing_class import inst_err_str

class TslDevice:
    '''TSL device class'''

    def __init__(self, interface: str, address: str, port: int = 5000):
        self._tsl = TSL()
        self.interface = interface
        self.address = address
        self.port = port
        #self.temp_counter = 0 #a temp counter for displaying debug info during each sweep.

        if interface not in ("GPIB", "LAN", "USB"):
            raise Exception ('This interface is not supported')

    def __str__(self):
        return "TslDevice"

    # TSL Connect
    def connect_tsl(self):
        """Method handling the connection protocol of the TSL.
        It also gets TSL specs: Min and Max wavelength and Max output power.

        Raises:
            Exception: In case failed to connect to the TSL.
        """
        # ---Property setting befor "Connect"------------

        # GPIB Terminater can set by TSL Front panel.
        # In this code, GPIB terminator must match TSL's GPIB terminator.
        # When LAN/USB Communication, terminator becomes "Cr"  at TSL.

        errorcode = 0

        # When GPIB communication
        if self.interface =="GPIB":
            self._tsl.Terminator = CommunicationTerminator.CrLf
            print(self._tsl.Terminator)
            self._tsl.GPIBAddress = int(self.address.split('::')[1])
            print(self._tsl.GPIBAddress)
            self._tsl.Bordnumber = 0
            self._tsl.GPIBConnectType = GPIBConnectType.NI4882
            print(self._tsl.GPIBConnectType)
            errorcode = self._tsl.Connect(CommunicationMethod.GPIB)
            print(errorcode)
         # When LAN Communication
        elif self.interface == "LAN":
            self._tsl.Terminator = CommunicationTerminator.Cr
            self._tsl.IPAddress  = self.address
            self._tsl.Port = self.port #port =5000

            errorcode = self._tsl.Connect(CommunicationMethod.TCPIP)

          # When USB communication
        elif self.interface == "USB":
            #USB DeviceID is defined uint32, So must be change variable type to unit32
            # this code typechange with numpy array
            ar_address = numpy.array([self.address],dtype ="uint32")
            self._tsl.DeviceID = ar_address[0]#self.address
            self._tsl.Terminator = CommunicationTerminator.Cr
            errorcode = self._tsl.Connect(CommunicationMethod.USB)
        else:
            print("there was no interface")
            errorcode = -1

        if errorcode !=0:
            self._tsl.DisConnect()
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        self.get_spec_wavelength() #get spec wavelength(nm)

        self.maxpow = self.get_max_power()

        return None

    def get_550_flag(self):
        """Checks if the connected TSL is TSL-550/TSL-710

        Returns:
            bool: True if TSL-550/TSL-710; else False.
        """

        tsl_name = self._tsl.Information.ProductName

        return tsl_name in ("TSL-550" ,"TSL-710")

    def get_spec_wavelength(self):
        """Gets Min and Max wavelengths supported by the connected TSL.

        Raises:
            Exception: In case couldn't get spec min and max wavleengths from the TSL.
        """

        errorcode,self.spec_min_wav,self.spec_max_wav = self._tsl.Get_Spec_Wavelength(0,0)

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return None

    def get_sweep_speed_table(self):
        """Returns sweep speed table of TSL-570:
        [1,2,5,10,20,50,100,200] (nm/sec)

        Raises:
            Exception: "DeviceError" when othre TSL is connected.

        Returns:
            array: Sweep speeds allowed by the TSL-570.
        """

        errorcode,table = self._tsl.Get_Sweep_Speed_table(None)
        self.return_table = []
        # this function only support "TSL-570"
        # when othre TSL connected, errorcode return "DeviceError"
        if errorcode == ExceptionCode.DeviceError:
            errorcode = 0
        else:
            for item in table:
                self.return_table.append(item)

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return self.return_table

    def get_max_power(self):
        """This method is used when TSL-570 is connected.
        Returns the max output power that can be delivered by the connected
        TSL.
        The method will call TSL object properties:min and max wavelentgh
        (spec_min_wav; spec_max_wav resp.)

        Otherwise, DeviceError errorcode is returned.

        Raises:
            Exception: In case TSL doesn't return the value.
        """

        errorcode,self.maxpower = self._tsl.Get_APC_Limit_for_Sweep(self.spec_min_wav,
                                                                    self.spec_max_wav,
                                                                    0.0)

        if errorcode == ExceptionCode.DeviceError.value__:
            self.maxpower = 999
            errorcode = 0

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return None

    def set_power(self, power):
        """Sets the output power of the TSL.

        Args:
            power (float): Setting output power.

        Raises:
            Exception: In case setting the output power is failed.
            Exception: In case TSL is busy.
        """
        self.power = power
        errorcode = self._tsl.Set_APC_Power_dBm(self.power)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        errorcode = self._tsl.TSL_Busy_Check(3000)
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return None

    def set_wavelength(self, wavelength):
        """Sets the TSL at a specific wavelength.

        Args:
            wavelength (float): setting wavelength.

        Raises:
            Exception: In case setting the wavelength is failed.
            Exception: In case TS is busy.
        """

        errorcode = self._tsl.Set_Wavelength(wavelength)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        errorcode = self._tsl.TSL_Busy_Check(3000)
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return None


    #
    def set_sweep_parameters(self, startwave,stopwave,step,speed):
        """Setting the sweep parameters and pass them in the TSL object.

        Args:
            startwave (float): Input the start wavelength value.
            stopwave (float): Input the stop wavelength value.
            step (float): Input the sweep step wavelength value.
            speed (float): Input the sweep speed value.

        Raises:
            Exception: In case the pass method fails
        """

        self.startwave = startwave
        self.stopwave = stopwave
        self.step = step
        self.speed = speed
        self.tsl_busy_check()

        errorcode,self.actual_step = self._tsl.Set_Sweep_Parameter_for_STS(self.startwave,
                                                                       self.stopwave,
                                                                       self.speed,
                                                                       self.step,
                                                                       0)

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        self.tsl_busy_check()

        return None

    def soft_trigger(self):
        """Issues a soft trigger to start TSL sweep.

        Raises:
            RuntimeError: In case TSL is not in Standby mode, or if TSL cannot start the sweep.
        """
        errorcode = self._tsl.Set_Software_Trigger()
        if errorcode !=0:
            raise RuntimeError(str(errorcode) + ": " + inst_err_str(errorcode))
        return None

    def start_sweep(self):
        """Runs the wavelength sweep. Method to be used when TSL is not connected
        to STS.

        Raises:
            Exception: In case TSL doesn't start the sweep.
        """
        errorcode = self._tsl.Sweep_Start()
        if errorcode !=0 :
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return None

    def stop_sweep(self, except_if_error = True):
        """Stops the sweep.

        Args:
            except_if_error (bool, optional): Set True if raising exception is
            needed within this method. Else, i.e. if this method is inserted within STS
            then set False so the exception  will be raised from STS method.
            Defaults to True.

        Raises:
            Exception: In case failure in stopping the TSL.
        """
        errorcode = self._tsl.Sweep_Stop()
        if errorcode !=0 and except_if_error is True:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return None


    def tsl_busy_check(self) :
        """Checks if the TSL is busy with other tasks.
        Default timeout = 3000 ms

        Raises:
            Exception: In case no response from TSL after timeout.
        """
        errorcode = self._tsl.TSL_Busy_Check(3000)
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return None

    def wait_for_sweep_status(self, waiting_time: int, sweep_status: int):
        """Wait until the TSL is set to a specified status prior the sweeping process.


        Args:
            waiting_time (int): Waiting time (milliseconds)
            sweep_status (int): Key value (1~5) of the _status dictionnary.
                                1: Standby
                                2: Running
                                3: Pause
                                4: Waiting for trigger
                                5:  Return

        Raises:
            Exception: In case TSL is not set to the specified status after timeout.
        """
        _status ={
            1:self._tsl.Sweep_Status.Standby,
            2:self._tsl.Sweep_Status.Running,
            3:self._tsl.Sweep_Status.Pausing,
            4:self._tsl.Sweep_Status.WaitingforTrigger,
            5:self._tsl.Sweep_Status.Returning
            }
        errorcode = self._tsl.Waiting_For_Sweep_Status(waiting_time, _status[sweep_status])

        #debug stuff to get the current status
        #current_enum = self._tsl.Sweep_Status.WaitingforTrigger #empty enum for now
        #test_num = -9999
        #test_num,current_enum = self._tsl.Get_Sweep_Status(current_enum)
        #str_currentVal = current_enum.value__
        
        #self.temp_counter += 1
        #print("current counter = {} status = {}".format(self.temp_counter, str_currentVal) )


        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return None

    def disconnect(self):
        """Disconnets the TSL.
        """
        self._tsl.DisConnect()
        return None
