# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 11:33:52 2022

@author: chentir
"""

import os
import numpy
import clr                                          # python for .net

ROOT = str(os.path.dirname(__file__))+'\\DLL\\'
print(ROOT)

PATH1 ='InstrumentDLL'
PATH2 ='STSProcess'
#Add in santec.Instrument.DLL
ans = clr.AddReference(ROOT+PATH1)

print (ans)
from Santec import TSL, ExceptionCode                  #　name space of instrument DLL
from Santec import CommunicationTerminator             # import CommunicationTerminator Enumration Class
from Santec.Communication import CommunicationMethod   # import CommunicationMethod Enumration Class
from Santec.Communication import GPIBConnectType       # import GPIBConnectType Enumration Class
from Santec.Communication import MainCommunication     # import MainCommuncation Class

from error_handing_class import inst_err_str

# ans = clr.AddReference(root+path2)
# print(ans)

# from Santec.STSProcess import*                         # name space of  STSProcess DLL
# from Santec.STSProcess import STSDataStruct            # import STSDataStruct structuer Class
# from Santec.STSProcess import STSDataStructForMerge    # import STSDataStructForMerge structure class
# from Santec.STSProcess import Module_Type              # import Module_Type Enumration Class
# from Santec.STSProcess import RescalingMode            #import RescalingMode Enumration Class

class TslDevice:
    '''TSL device class'''

    def __init__(self, interface: str, address: str, port: int = None):
        self._tsl = TSL()
        self.interface = interface
        self.address = address
        self.port = port

        if interface not in ("GPIB", "LAN", "USB"):
            raise Exception ('This interface is not supported')

    # TSL Connect
    def connect_tsl(self):
        '''
        Method handling the connection protocol of the TSL.
        It also gets TSL specs: Min and Max wavelength, Max output power and,
        if applicable, Sweep Speed Table (TSL-570 case).

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        '''

        # ---Property setting befor "Connect"------------

        # GPIB Terminater can set by TSL Front panel.
        # In this code, GPIB terminator must match TSL's GPIB terminator.
        # When LAN/USB Communication, terminator becomes "Cr"  at TSL.

        errorcode = 0

        # When GPIB communication
        if self.interface =="GPIB":
            self._tsl.Terminator = CommunicationTerminator.CrLf
            print(self._tsl.Terminator)
            self._tsl.GPIBAddress = int(self.address)
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
            self._tsl.DeviceID = ar_address[0]
            self._tsl.Terminator = CommunicationTerminator.Cr
            errorcode = self._tsl.Connect(CommunicationMethod.USB)
        else:
            print("there was no interface")
            errorcode = -1

        if errorcode !=0:
            self._tsl.DisConnect()
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        #Now that we are connected, get the flags and wavelengths and limits etc
        #TSL handling
        flag_550 = self.get_550_flag()                                #550/710 or not
        self.spec_min_wav, self.spec_max_wav = self.get_spec_wavelenth() #get spec wavelength(nm)

        if errorcode !=0:
            self._tsl.DisConnect()
            raise Exception("Could not get the TSL wavelength limits: " +
                            str(errorcode) + ": " + inst_err_str(errorcode))


        if flag_550 is True:
            self.sweep_table = None #this should be configued after connecting, in the STS class
            self.maxpow = 10 #this should be configued after connecting, in the STS class
        else:
            # this handling only support for TSL-570
            self.sweep_table =self.get_sweep_speed_table()        #get Sweep speed tabel

            if errorcode !="":
                print("IL_STS",errorcode)
            #get APC limit power for wavelength range:
            errorcode,self.maxpow = self.get_max_power(self.spec_min_wav, self.spec_max_wav)#this should be called elsewhere, like in the STS class
            #also make this throw an exception if needed
            if errorcode != "":
                print("IL_STS",errorcode)

        return inst_err_str(errorcode)

    # retunr TSL-550 or not  True: TSL-550/710  False: TSL-570
    def get_550_flag(self):
        '''
        Checks if the connected TSL is TSL-550/TSL-710

        Returns
        -------
        bool
            DESCRIPTION.

        '''

        tsl_name = self._tsl.Information.ProductName

        return tsl_name in ("TLS-550" ,"TSL-710")

    def get_spec_wavelenth(self):
        '''
        Gets Min and Max wavelengths supported by the connected TSL.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.
        TYPE
            DESCRIPTION.

        '''

        errorcode,self.spec_min_wav,self.spec_max_wav = self._tsl.Get_Spec_Wavelength(0,0)

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return self.spec_min_wav,self.spec_max_wav

    def get_sweep_speed_table(self):
        '''
        Returns Sweep speed table of TSL-570

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''

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
            # errstr = inst_err_str(errorcode)

        return self.return_table

    def get_max_power(self, spec_min_wav, spec_max_wav):
        '''
        Returns the max output power that can be delivered by the connected
        TSL.
        This method is used when TSL-570 is connected.
        Otherwise, errorcode return "DeviceError".
        Parameters
        ----------
        spec_min_wav : TYPE
            Min wavelength supported by the connected TSL. This value is passed
            from get_spec_wavelenth method.
        spec_max_wav : TYPE
            Max wavelength supported by the connected TSL. This value is passed
            from get_spec_wavelenth method.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''

        errorcode,self.maxpower = self._tsl.Get_APC_Limit_for_Sweep(self.spec_min_wav,
                                                                    self.spec_max_wav,
                                                                    0.0)

        if errorcode == ExceptionCode.DeviceError:
            self.maxpower = 999 #!!! this is dangerous and needs to be experimentally checked
            errorcode = 0

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return self.maxpower

    def set_power(self, power):
        '''
        Sets the output power of the TSL

        Parameters
        ----------
        power : TYPE
            Input the output power value.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        errorcode : TYPE
            DESCRIPTION.

        '''

        errorcode = self._tsl.Set_APC_Power_dBm(self.power)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        errorcode = self._tsl.TSL_Busy_Check(3000)
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return inst_err_str(errorcode)

    def set_wavelength(self, wavelength):
        '''
        Sets the TSL at a wavelength.

        Parameters
        ----------
        wavelength : TYPE
            Input the wavelength value.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        errorcode : TYPE
            DESCRIPTION.

        '''

        errorcode = self._tsl.Set_Wavelength(wavelength)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        errorcode = self._tsl.TSL_Busy_Check(3000)
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return inst_err_str(errorcode)


    #
    def set_sweep_parameters(self, startwave,stopwave,step,speed):
        '''
        Sets the sweep parameter TSL

        Parameters
        ----------
        startwave : TYPE
            Input the start wavelength value.
        stopwave : TYPE
            Input the stop wavelength value.
        step : TYPE
            Input the sweep step wavelength value.
        speed : TYPE
            Input the sweep speed value.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
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
        #return self.actual_step we dont need to return this because it ssaved in the actual_step car
        return None
    def soft_trigger(self):
        errorcode = self._tsl.Set_Software_Trigger()
        if errorcode !=0:
            raise RuntimeError(str(errorcode) + ": " + inst_err_str(errorcode))

    #!!!create method to run the sweep
    def start_sweep(self):
        '''
        Runs the wavelength sweep. Method to be used when TSL is not connected
        to STS.

        Returns
        -------
        None.

        '''
        errorcode = self._tsl.Sweep_Start()
        if errorcode !=0 :
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

    def stop_sweep(self, except_if_error = True):
        errorcode = self._tsl.Sweep_Stop()
        if errorcode !=0 and except_if_error is True:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))


    def tsl_busy_check(self) :
        '''
        Checks if the TSL is busy with other tasks.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        errorcode = self._tsl.TSL_Busy_Check(3000)
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

    def wait_for_sweep_status(self, waiting_time: int, sweep_status: int):
        _status ={
            1:self._tsl.Sweep_Status.Standby,
            2:self._tsl.Sweep_Status.Running,
            3:self._tsl.Sweep_Status.Pausing,
            4:self._tsl.Sweep_Status.WaitingforTrigger,
            5:self._tsl.Sweep_Status.Returning
            }
        errorcode = self._tsl.Waiting_For_Sweep_Status(waiting_time,_status[sweep_status])
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return None

    def disconnect(self):
        self._tsl.DisConnect()
