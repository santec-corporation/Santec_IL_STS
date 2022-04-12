# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 19:48:11 2022

@author: chentir
"""

import os
import clr                                          # python for .net
import time

ROOT = str(os.path.dirname(__file__))+'\\DLL\\'
print(ROOT)

PATH1 ='InstrumentDLL'
PATH2 ='STSProcess'
#Add in santec.Instrument.DLL
ans = clr.AddReference(ROOT+PATH1)

print (ans)
from Santec import MPM                  #　name space of instrument DLL
from Santec.Communication import CommunicationMethod   # import CommunicationMethod Enumration Class
from Santec.Communication import GPIBConnectType       # import GPIBConnectType Enumration Class

from error_handing_class import inst_err_str

class MpmDevice:
    '''MPM device class'''

    def __init__(self, interface: str, address: str, port: int = None):
        self._mpm = MPM()
        self.interface = interface
        self.address = address
        self.port = port

    def connect_mpm(self):
        '''
        Method handling the connection protocol of the MPM.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        if self.interface == "GPIB":
            mpm_commincation_method = CommunicationMethod.GPIB
            self._mpm.GPIBAddress = int(self.address)
            self._mpm.Bordnumber = 0
            self._mpm.GPIBConnectType = GPIBConnectType.NI4882
        else :
            mpm_commincation_method  = CommunicationMethod.TCPIP
            self._mpm.IPAddress = self.address
            self._mpm.port = self.port #port = 5000

        self._mpm.TimeOut = 2000             # time out value for MPM

        errorcode = self._mpm.Connect(mpm_commincation_method)
        if errorcode !=0:
            self._mpm.DisConnect()
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return inst_err_str(errorcode)

    def get_mods_chans(self):
        '''
        Gets channels to be measured.

        Returns
        -------
        List of lists
            Item 0 from the returned list corresponds to the modules that are mounted.
            All remaining items are the number of channels of each module.
            ex:
            [[0,1],[1,2,3,4],[1,2]]
            Slot 0 and 1 have mounted MPM modules.
            The module at slot 0 has 4 available optical channels (either MPM-211 or MPM-215)
            The module at slot 1 has only 2 available optical channels (MPM-212).
        '''

        self.mods_and_chans = [[]] #todo: use me!

        for slotcount in range(5):
            if self._mpm.Information.ModuleEnable[slotcount] is True:
                self.mods_and_chans[0].append(slotcount)
                if self.check_mpm_212(slotcount) is True:
                    self.mods_and_chans.append([1,2])
                else :
                    self.mods_and_chans.append([1,2,3,4])
        if len(self.mods_and_chans[0]) == 0 or len(self.mods_and_chans)==1:
            raise Exception('No modules/channels were detected')
        return self.mods_and_chans

    #no more needed
    # def get_enabled_slots(self):

    #     enabled_slots = []
    #     for slotcount in range(5):
    #         if self._mpm.Information.ModuleEnable[slotcount] is True:
    #             enabled_slots.append(slotcount)

    #     return enabled_slots


    def check_module_type(self):
        '''
        Checks MPM modules type.

        Raises
        ------
        Exception
            MPM-215 can't be used with other MPM modules.

        Returns
        -------
        flag_215 : bool
            DESCRIPTION.
        flag_213 : bool
            DESCRIPTION.

        '''

        flag_215 = False
        flag_213 = False
        slot = 0
        count_215 = 0

        for slotcount in range(5):
            if self._mpm.Information.ModuleEnable[slotcount] is True:
                flag_215= self.check_mpm_215(slotcount)
                flag_213 = self.check_mpm_213(slotcount)
                slot += 1
                if flag_215 is True:
                    count_215 += 1

        if flag_215 is True and count_215 != slot:
            raise Exception("MPM-215 can't use with other modules")

        return flag_215,flag_213

    def check_mpm_215(self, slotcount):
        '''
        Checks if the mounted module is MPM-215.

        Parameters
        ----------
        slotcount : TYPE
            DESCRIPTION.

        Returns
        -------
        bool
            DESCRIPTION.

        '''

        return bool(self._mpm.Information.ModuleType[slotcount] == "MPM-215")

    def check_mpm_213(self,slotcount):
        '''
        Checks if the mounted module is MPM-213.

        Parameters
        ----------
        slotcount : TYPE
            DESCRIPTION.

        Returns
        -------
        bool
            DESCRIPTION.

        '''

        return bool( self._mpm.Information.ModuleType[slotcount] == "MPM-213")

    def check_mpm_212(self, slotcount):
        '''
        Checks if the mounted module is MPM-212.

        Parameters
        ----------
        slotcount : TYPE
            DESCRIPTION.

        Returns
        -------
        bool
            DESCRIPTION.

        '''

        return bool(self._mpm.Information.ModuleType[slotcount]== "MPM-212")

    def get_range(self):
        self.rangedata = []
        if self.check_mpm_215 is True:
            self.rangedata = [1]
        elif self.check_mpm_213 is True:
            #213 have 4 ranges
            self.rangedata = [1,2,3,4]
        else:
            self.rangedata = [1,2,3,4,5]

    def set_range(self, powerrange):
        '''
        Sets the dynamic range of the MPM.

        Parameters
        ----------
        powerrange : TYPE
            DESCRIPTION.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        '''

        errorcode = self._mpm.Set_Range(powerrange)

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return inst_err_str(errorcode)

    def  zeroing(self):
        '''
        Performs a Zeroing on all MPM channels.
        All the channels must be closed with respective balck caps before
        performing this operation.

        Returns
        -------
        errorstr : TYPE
            DESCRIPTION.

        '''
        errorcode = self._mpm.Zeroing()

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return inst_err_str(errorcode)

    def get_averaging_time(self):
        '''
        Gets the averaging time of the MPM.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''

        errorcode,self.averaging_time = self._mpm.Get_Averaging_Time(0)

        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return self.averaging_time

    def logging_start(self):
        errorcode = self._mpm.Logging_Start()
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
    
    def logging_stop(self, except_if_error = True):
        errorcode = self._mpm.Logging_Stop()
        if errorcode != 0 and except_if_error is True:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        

    def set_logging_parameters(self,startwave,stopwave,step,speed):
        '''
        Sets the logging parameter for MPM integrated in STS


        Parameters
        ----------
        startwave : TYPE
            DESCRIPTION.
        stopwave : TYPE
            DESCRIPTION.
        step : TYPE
            DESCRIPTION.
        speed : TYPE
            DESCRIPTION.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        errorcode = self._mpm.Set_Logging_Paremeter_for_STS(startwave,
                                                           stopwave,
                                                           step,
                                                           speed,
                                                           self._mpm.Measurement_Mode.Freerun)

        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return inst_err_str(errorcode)

    def disconnect(self):
        self._mpm.DisConnect()

    def wait_log_completion(self):

        #Check MPM Loging stopped
        timeA = time.perf_counter()
        status = 0                    #MPM Logging status  0: During logging 1: Completed, -1:stoped
        logging_point = 0

        while status == 0:
            errorcode,status,logging_point = self._mpm.Get_Logging_Status(0,0)
            if(errorcode !=0):
                break

            #if more than 2sec have passed for sweep time
            elaspand_time = time.perf_counter() -timeA
            if (elaspand_time > 2000):
                errorcode = -999
                break
        
        if (status != 0):
            raise RuntimeError("MPM status is " + status + ". Timeout error occurred")

           #Logging stop
        if (errorcode == -999):
            errorstr = "MPM Trigger received an error! Please check trigger cable connection."
            raise RuntimeError(errorstr)

        if (errorcode != 0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            raise RuntimeError(errorstr)

        return None