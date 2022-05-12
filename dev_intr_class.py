# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 20:04:16 2022

@author: chentir
"""

from error_handing_class import inst_err_str
import os
import clr                                          # python for .net

ROOT = str(os.path.dirname(__file__))+'\\DLL\\'
print(ROOT)

PATH1 = 'InstrumentDLL'
PATH2 = 'STSProcess'
#Add in santec.Instrument.DLL
ans = clr.AddReference(ROOT+PATH1)
from Santec import SPU  # 　name space of instrument DLL

print(ans)


class SpuDevice:
    '''DAQ board device class'''

    def __init__(self, devicename: str):
        self._spu = SPU()
        self.devicename = devicename

    def connect_spu(self):
        '''
        Connects the DAQ board (SPU Connect).

        Parameters
        ----------
        devicename : TYPE
            DESCRIPTION.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        self._spu.DeviceName = str(self.devicename)

        errorcode, ans = self._spu.Connect("")
        if (errorcode != 0):
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return inst_err_str(errorcode)

    # SPU Set logging paramter
    def set_logging_parameters(self, startwave,
                               stopwave, speed,
                               tsl_actual_step):
        '''


        Parameters
        ----------
        startwave : TYPE
            DESCRIPTION.
        stopwave : TYPE
            DESCRIPTION.
        speed : TYPE
            DESCRIPTION.
        tsl_acctualste : TYPE
            DESCRIPTION.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''

        errorcode = self._spu.Set_Sampling_Parameter(startwave,
                                                     stopwave,
                                                     speed,
                                                     tsl_actual_step)

        if (errorcode != 0):
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))

        return inst_err_str(errorcode)

    def sampling_start(self):
        errorcode = self._spu.Sampling_Start()
        if (errorcode != 0):
            raise RuntimeError(str(errorcode) + ": " + inst_err_str(errorcode))

    def sampling_wait(self):
        errorcode = self._spu.Waiting_for_sampling()
        if (errorcode != 0):
            raise RuntimeError(str(errorcode) + ": " + inst_err_str(errorcode))

    def get_sampling_raw(self):
        errorcode, trigger, monitor = self._spu.Get_Sampling_Rawdata(
            None, None)
        if (errorcode != 0):
            raise Exception(str(errorcode) + ": " + inst_err_str(errorcode))
        return trigger, monitor

    def disconnect(self):
        self._spu.DisConnect()