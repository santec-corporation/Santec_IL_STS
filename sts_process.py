# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:21:13 2022

@author: chentir
"""

import os
import clr
import re
from dev_intr_class import SpuDevice
from mpm_instr_class import MpmDevice
from tsl_instr_class import TslDevice                                          # python for .net

ROOT = str(os.path.dirname(__file__))+'\\DLL\\'
print(ROOT)

PATH2 ='STSProcess'
#Add in santec.STSProcess.DLL
ans = clr.AddReference(ROOT+PATH2)
print(ans)

from Santec.STSProcess import *                        # name space of  STSProcess DLL
from Santec.STSProcess import ILSTS
from Santec.STSProcess import STSDataStruct            # import STSDataStruct structuer Class
from Santec.STSProcess import STSDataStructForMerge    # import STSDataStructForMerge structure class
from Santec.STSProcess import Module_Type              # import Module_Type Enumration Class
from Santec.STSProcess import RescalingMode            #import RescalingMode Enumration Class

from error_handing_class import stsprocess_err_str


class StsProcess:
    '''STS processing class'''
    _tsl: TslDevice
    _mpm: MpmDevice
    _spu: SpuDevice

    def __init__(self, _tsl, _mpm, _spu):
        self._tsl = _tsl
        self._mpm = _mpm
        self._spu = _spu
        self._ilsts = ILSTS()

    #def set_parameters(self,minwave,maxwave,wavestep,speed):
    def set_parameters(self):
        '''
        Sets parameters for STS process.

        Parameters
        ----------
        minwave : TYPE
            DESCRIPTION.
        maxwave : TYPE
            DESCRIPTION.
        wavestep : TYPE
            DESCRIPTION.
        speed : TYPE
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

        #do not set the sweep params for TSL, because we did that already in the TSL portion
        ##self._tsl.set_sweep_parameters(self._tsl.minwave, self._tsl.maxwave, self._tsl.wavestep, self._tsl.speed)
        #actual_step = self._tsl.actual_step

        #Logging parameters for MPM
        self._mpm.set_logging_parameters(self._tsl.startwave,
                                         self._tsl.stopwave,
                                         self._tsl.step,
                                         self._tsl.speed)

        #averaging_time = self._mpm.get_averaging_time() #not needed anymore

        #Logging parameter for SPU(DAQ)
        self._spu.set_logging_parameters(self._tsl.startwave,
                                         self._tsl.stopwave,
                                         self._tsl.speed,
                                         self._tsl.actual_step)

        #pass MPM averaging time to SPU　 Class
        self._spu.AveragingTime = self._mpm.get_averaging_time()

        #-----STS Process setting Class
        #Clear measurement data
        sts_error = self._ilsts.Clear_Measdata()
        if (sts_error !=0):
            raise Exception(str(sts_error) + ": " + stsprocess_err_str(sts_error))

        #Reference data Clear
        sts_error  = self._ilsts.Clear_Refdata()
        if (sts_error !=0):
            raise Exception(str(sts_error) + ": " + stsprocess_err_str(sts_error))

        #Make Wavelength table at sweep
        sts_error = self._ilsts.Make_Sweep_Wavelength_Table(self._tsl.startwave,
                                                            self._tsl.stopwave,
                                                            self._tsl.actual_step)

        if (sts_error !=0):
            raise Exception(str(sts_error) + ": " + stsprocess_err_str(sts_error))

        #make wavelength table as rescaling
        sts_error = self._ilsts.Make_Target_Wavelength_Table(self._tsl.startwave,
                                                             self._tsl.stopwave,
                                                             self._tsl.step)

        if (sts_error !=0):
            raise Exception(str(sts_error) + ": " + stsprocess_err_str(sts_error))

        #Set Rescaling mode for STSProcess class
        sts_error = self._ilsts.Set_Rescaling_Setting(RescalingMode.Freerun_SPU,
                                                      self._mpm.get_averaging_time(),
                                                      True)

        if (sts_error !=0):
            raise Exception(str(sts_error) + ": " + stsprocess_err_str(sts_error))

        return stsprocess_err_str(sts_error) #errorstr

    def channel_select(self,_mpm):
        '''This method to select channels to be measured.
        It offers the user to choose between different ways to select MPM channels.
        For this purpose, method calls the following methods:
        - all_chans
        - even_chans
        - odd_chans
        - special
        - cancel'''
        self.selected_chans = []
        self.all_channels = self._mpm.get_mods_chans()  #array of arrays: array 0  displays the connected modules
                                                        #the following arrays contain ints of available channels of each module

        #do some error handling to make sure we have at least 1 channel <- Done@ mpm class get_mods_chans line 93
        #            0. last chosen settings, chosen from either memory or from the reference data.
        #        - Its possible that neither exist. Think about also saving this to a file?
        # this option was removed... need to check some error handling (presence or not of the file, the file being or not in the desired format etc.)
        print(
        '''Select channels to be measured:
            1. All channels
            2. Even channels
            3. Odd channels
            4. Specific channels
            5. Cancel
        ''')
        for mod in self.all_channels[0]:
            print ('''Available modules/channels:
                        Module {}: Channels {}'''.format(mod,self.all_channels[mod+1]))
        choices = {'1': self.all_chans,
                   '2': self.even_chans,
                   '3': self.odd_chans,
                   '4': self.special,
                   '5': self.cancel}

        selection = input()
        choices[selection]()

    def all_chans(self):
        '''Selects all modules and all channels that are connected to MPM.'''
        for i in self.all_channels[0]:
            for j in self.all_channels[i+1]:
                self.selected_chans.append([i,j])
        return self.selected_chans

    def even_chans(self):
        '''Selects only even channels on the MPM.'''
        for i in self.all_channels[0]:
            for j in self.all_channels[i+1]:
                if j%2 !=0:
                    self.selected_chans.append([i,j])

    def odd_chans(self):
        '''Selects only odd channels on the MPM.'''
        for i in self.all_channels[0]:
            for j in self.all_channels[i+1]:
                if j%2 ==0:
                    self.selected_chans.append([i,j])

    def special(self,num_of_chan):
        '''Manually enter/select the channels to be measured'''
        #TODO: raising exception if entered module/channel doesn't exist
        print('Input (module,channel) to be tested [ex: (0,1); (1,1)]')
        selection = input()
        selection = re.findall(r"[\w']+",selection)
        i=0
        while i<= len(selection)-1:
            self.selected_chans.append([i,i+1])
    
    def cancel(self):
        self._tsl.disconnect()
        self._mpm.disconnect()
        self._spu.disconnect()

    def range_select(self,_mpm):
        self.selected_ranges = []
        print('Select the dynamic range. ex: 1, 3, 5')
        print('Available dynamic ranges:')
        i=1
        for range in self._mpm.get_range():
            print('{}- {}'.format(i,range))
            i +=1
        selection = input()
        self.selected_ranges = re.findall(r"[\w']+",selection)

    # Config each STSDatastruct from ch data And ranges
    def set_data_struct(self,selected_chans,selected_ranges):

        counter =1

        #List data clear
        self.dut_monitor = []   #Lst_MeasMonitor_st.clear()
        self.dut_data = []      #Lst_Measdata_st.clear()
        self.merge_data = []    #Lst_Merge_st.clear()
        self.ref_monitor = []   #Lst_RefMonitor_st.clear()
        self.ref_data = []      #Lst_Refdata_st.clear()
        self.range = []         #Lst_Range.clear()

        # config STSDatastruct for each measurment
        for m_range in self.selected_ranges:
            for ch in self.selected_chans:
                data_st = STSDataStruct()
                data_st.MPMNumber = 0           #TODO need to find a way to implement multi-MPM protocol
                data_st.SlotNumber = ch[0]      #slot number
                data_st.ChannelNumber = ch[1]   #channel number
                data_st.RangeNumber = m_range
                data_st.SweepCount = counter
                data_st.SOP = 0
                self.dut_data.append(data_st)

                rangeindex =  self.selected_ranges.index(m_range)
                chindex = self.selected_chans.index(ch)

                #measurement monitor data need only 1ch for each range.
                if(chindex == 0):
                    self.dut_monitor.append(data_st)
                    self.range.append(m_range)
                    
                # reference data need only 1 range for each ch
                if (rangeindex ==0 ):
                    self.ref_data.append(data_st)
                # reference monitor data need only 1 data
                if (chindex ==0) and (rangeindex == 0):
                    self.ref_monitor.append(data_st)

            counter +=1

        #config STSDataStruct for merge
        for ch in self.selected_chans:
            mergest = STSDataStructForMerge()

            mergest.MPMnumber = 0           #TODO need to find a way to implement multi-MPM protocol
            mergest.SlotNumber = ch[0]      #slot number
            mergest.ChannelNumber = ch[1]   #channel number
            mergest.SOP = 0

            self.merge_data.append(mergest)

    # STS Reference handling
    def sts_reference(self, _mpm):

        errorstr = ""
        for i in self.ref_data:
            print('Connect Slot{}Ch{}, then press any key'.format(i.SlotNumber,i.ChannelNumber))
            input()
            #set MPM range for 1st setting renge
            self._mpm.set_range(self.range[0]) #No need to raise exception as it is done@ mpm_instr_class


            #TSL Wavelength set to use Sweep Start Command
            errorcode = self._tsl.Sweep_Start()
            if errorcode !=0:
                raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

            #Sweep handling
            errorstr = func_STS_SweepProcess()
            if (errorstr != ""):
                return errorstr

            #get sampling data & Add in STSProcess Class
            errorstr = func_STS_GetReferenceData(i)
            if (errorstr != ""):
                  return errorstr

            # rescaling for reference data
            errorcode = _ILSTS.Cal_RefData_Rescaling()
            if (errorcode !=0):
                errorstr = func_return_STSProcessErrorStr(errorcode)
                return errorstr

            #TSL Sweep stop
            errorcode = _TSL.Sweep_Stop()
            if (errorcode !=0):
                errorstr = func_return_InstrumentErrorStr(errorcode)
                return errorstr

        return errorstr

    #STS Measurement handling
    def func_STS_Measurement():
        errorstr = ""

        #TSL Sweep Start
        errorcode = _TSL.Sweep_Start()
        if (errorcode != 0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

        #Range loop
        sweepcount = 1
        for mpmrange in Lst_Range:
            #set MPM Range
            errorstr = func_MPM_SetRange(mpmrange)
            if (errorstr != ""):
                return errorstr

            #sweep handling
            errorstr = func_STS_SweepProcess()
            if (errorstr != ""):
                return errorstr

            #Get Reference data
            errorstr = func_STS_GetMeasurementData(sweepcount)
            if (errorstr !=""):
                return errorstr
            sweepcount += 1

        # rescaling
        errorcode = _ILSTS.Cal_MeasData_Rescaling()
        if (errorcode !=0):
            errorstr = func_return_STSProcessErrorStr(errorcode)
            return errorstr

        # range data merge
        errorcode = _ILSTS.Cal_IL_Merge(Module_Type.MPM_211)
        if (errorcode != 0):
            errorstr = func_return_STSProcessErrorStr(errorcode)
            return errorstr

        #TSL stop
        errorcode = _TSL.Sweep_Stop()
        if (errorcode !=0):
            errorstr  = func_return_InstrumentErrorStr(errorcode)
            return errorstr


        return errorstr


    # STS Sweep Process
    def sts_sweep_process(self):
        errorstr =""
        #MPM Logging Start
        errorcode =self._mpm.logging_start()

        # Waiting for TSL sweep status to "Trigger Standby"
        errorcode = self._tsl.wait_for_sweep_status()

        #errorhandling  TSL error -> MPM Logging stop
        if (errorcode != 0):
            self._mpm.logging_stop(errorcode)

        #SPU sampling start
        errorcode = self._spu.sampling_start()
        if(errorcode !=0):
            self._tsl.stop_sweep()
            self._mpm.logging_stop(errorcode)

        #TSL issue software trigger
        errorcode = _TSL.Set_Software_Trigger()
        if (errorcode !=0):
            _MPM.Logging_Stop()
            _TSL.Sweep_Stop()
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

        #SPU Waiting for sampling(waiting for during sweep time)
        errorcode = _SPU.Waiting_for_sampling()
        if (errorcode !=0):
            _MPM.Logging_Stop()
            _TSL.Sweep_Stop()
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

        #Check MPM Loging stopped
        timeA = time.perf_counter()
        status = 0                    #MPM Logging status  0: During logging 1: Completed, -1:stoped
        logging_point = 0

        while status == 0:
            errorcode,status,logging_point = _MPM.Get_Logging_Status(0,0)
            if(errorcode !=0):
                break

            #if more than 2sec have passed for sweep time
            elaspand_time = time.perf_counter() -timeA
            if (elaspand_time > 2000):
                    errorcode = -999
                    break
        #Logging stop
        _MPM.Logging_Stop()

        if (errorcode == -999):
            errorstr = "MPM Trigger receive error! Please check trigger cable connection."
            return errorstr

        if (errorcode != 0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

         # Waiting for TSL sweep status to "Standby"
        errorcode = _TSL.Waiting_For_Sweep_Status(5000,TSL.Sweep_Status.Standby)
        if (errorcode !=0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

        #TSL Wavelength set to use Sweep Start Command for next sweep
        errorcode = _TSL.Sweep_Start()
        if (errorcode !=0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

        return errorstr

    # get logging data & add STSProcess Class for Reference
    def func_STS_GetReferenceData(item):
        errorstr = ""

        # for item in Lst_Refdata_st:
        #Get MPM logging data
        slotnumber =item.SlotNumber
        ch = item.ChannelNumber
        errorcode,logdata = _MPM.Get_Each_Channel_Logdata(slotnumber,ch,None)

        if (errorcode !=0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

        #Add MPM Logging data for STS Process Class
        ary_loggdata = array('f',logdata)                       #List to Array
        errorcode = _ILSTS.Add_Ref_MPMData_CH(ary_loggdata,item)
        if (errorcode !=0):
            errorstr = func_return_STSProcessErrorStr(errorcode)
            return errorstr

        #Get SPU sampling data
        errorcode,trigger,monitor = _SPU.Get_Sampling_Rawdata(None,None)
        if (errorcode !=0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

        #Add Monitor data for STS Process Class
        errorcode = _ILSTS.Add_Ref_MonitorData(trigger,monitor,Lst_RefMonitor_st[0])
        if (errorcode !=0):
            errorstr = func_return_STSProcessErrorStr(errorcode)
            return errorstr

        return errorstr


    # get logging data & add STSProcess class for Measuerment
    def func_STS_GetMeasurementData(sweepcount):
        errorstr = ""

        for item in Lst_Measdata_st:
            if (item.SweepCount != sweepcount):
                continue
            slotnumber = item.SlotNumber
            ch = item.ChannelNumber

            #Get MPM loggin data
            errorcode,loggdata = _MPM.Get_Each_Channel_Logdata(slotnumber,ch,None)
            if (errorcode !=0):
                errorstr = func_return_InstrumentErrorStr(errorcode)
                return errorstr
            aryloggdata = array("f",loggdata)                           #List to Array

            #Add MPM Logging data for STSPrcess Class with STSDatastruct
            errorcode = _ILSTS.Add_Meas_MPMData_CH(aryloggdata,item)
            if (errorcode !=0):
                errorstr = func_return_STSProcessErrorStr(errorcode)
                return errorstr

        # Get monitor data
        errorcode,trigger,monitor = _SPU.Get_Sampling_Rawdata(None,None)

        if (errorcode !=0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

        arytrigger = array("f",trigger)                             #List to Array
        arymonitor = array("f",monitor)                             #list to Array

        #search place of add in
        for item in Lst_MeasMonitor_st:
            if (item.SweepCount != sweepcount):
                continue
            #Add Monirot data for STSProcess Class  with STSDataStruct
            errorcode = _ILSTS.Add_Meas_MonitorData(arytrigger,arymonitor,item)
            if (errorcode !=0):
                errorstr = func_return_STSProcessErrorStr(errrorcode)
                return errorstr

        return errorstr

    # Config each STSDatastruct from ch data And ranges
    def func_STS_SetDataStruct(usech,useranges):

        counter =1

        #List data clear
        Lst_MeasMonitor_st.clear()
        Lst_Measdata_st.clear()
        Lst_Merge_st.clear()
        Lst_RefMonitor_st.clear()
        Lst_Refdata_st.clear()
        Lst_Range.clear()

        # config STSDatastruct for each measurment
        for m_range in useranges:
            for ch in usech:
                datast = STSDataStruct()
                slotnum = int(str(ch[4]))   #slotnumber
                chnumber =int(str(ch[7]))   #ch number

                datast.MPMNumber = 0
                datast.SlotNumber = slotnum
                datast.ChannelNumber = chnumber
                datast.RangeNumber = m_range
                datast.SweepCount = counter
                datast.SOP = 0
                Lst_Measdata_st.append(datast)

                rangeindex =  useranges.index(m_range)
                chindex = usech.index(ch)

                #measurement monitor data need only 1ch for each range.
                if(chindex == 0):
                    Lst_MeasMonitor_st.append(datast)
                    Lst_Range.append(m_range)

                # reference data need only 1 range for each ch
                if (rangeindex ==0 ):
                    Lst_Refdata_st.append(datast)
                # reference monitor data need only 1 data
                if (chindex ==0) and (rangeindex == 0):
                    Lst_RefMonitor_st.append(datast)

            counter +=1

         #config STSDataStruct for merge
        for ch in usech:
             mergest = STSDataStructForMerge()
             slotnum = int(str(ch[4]))   #slotnumber
             chnumber =int(str(ch[7]))   #ch number

             mergest.MPMnumber = 0
             mergest.SlotNumber = slotnum
             mergest.ChannelNumber = chnumber
             mergest.SOP = 0

             Lst_Merge_st.append(mergest)


    # Save Reference raw data
    def func_STS_Save_Referance_Rawdata(filepath):

        errorstr = ""

        #wavelength data
        errorcode,wavetable = _ILSTS.Get_Target_Wavelength_Table(None)
        if (errorcode !=0):
            errorstr = func_return_STSProcessErrorStr(errorcode)
            return errorstr

        lstpow = []
        #Pull out reference raw data of aftar rescaling
        for item in Lst_Refdata_st:
            errorcode,power,monitor = _ILSTS.Get_Ref_RawData(item,None,None)
            if (errorcode !=0):
                errorstr = func_return_STSProcessErrorStr(errorcode)
                return errorcode
            arypow = array("f",power)     #List to Array
            lstpow.append(arypow)

        #File open and write data  for .csv
        with open(filepath,"w",newline="")as f:
            writer = csv.writer(f)
            hedder = ["Wavelength(nm)"]

            #for hedder
            for item in Lst_Refdata_st:
                slotnum = item.SlotNumber
                chnum = item.ChannelNumber
                hedder_str  = "Slot" +str(slotnum) +"Ch" +str(chnum)
                hedder.append(hedder_str)
            hedder_str = "Monitor"
            hedder.append(hedder_str)
            writer.writerow(hedder)

            writest = []
            #for data
            counter = 0
            for wave in wavetable:
                writest.append(wave)
                for item in lstpow:
                    data = item[counter]
                    writest.append(data)

                data = monitor[counter]
                writest.append(data)
                writer.writerow(writest)
                writest.clear()
                counter +=1

            f.close()

        return errorstr

    #Save measurement Rawdata for specific range
    def func_STS_Save_Rawdata(fpath,mpmrange):
        errorstr = ""

        #wavelength table
        errorcode,wavetable = _ILSTS.Get_Target_Wavelength_Table(None)
        if (errorcode !=0):
            errorstr = func_return_STSProcessErrorStr(errorcode)
            return errorstr

        lstpow = []
        #data
        for item in Lst_Measdata_st:
            print(item)
            if (item.RangeNumber != mpmrange):
                print('hey')
                print(item.RangeNumber)
                input()
                continue
            #Pull out measurement raw data of aftar rescaling
            errorcode,power,monitor = _ILSTS.Get_Meas_RawData(item,None,None)
            if (errorcode !=0):
                errorstr = func_return_STSProcessErrorStr(errorcode)
                return errorstr
            arypow = array("f",power)         #List to Array
            arymoni = array("f",monitor)      #List to Array
            lstpow.append(arypow)

        #for hedder
        hedder = ["Wavelength(nm)"]

        for item in Lst_Measdata_st:
            if (item.RangeNumber != mpmrange):
                continue
            hedder_str = "Slot" + str(item.SlotNumber) + "Ch" + str(item.ChannelNumber)
            hedder.append(hedder_str)

        hedder_str = "Monitor"
        hedder.append(hedder_str)

        #Open file and write data for .csv
        with open(fpath,"w",newline = "") as f:
            writer = csv.writer(f)
            writer.writerow(hedder)

            #for data
            write_st =[]
            counter = 0
            for wave in wavetable:
                write_st.append(wave)
                #power data
                for item in lstpow:
                    data = item[counter]
                    write_st.append(data)
                #monitor data
                data = arymoni[counter]
                write_st.append(data)
                writer.writerow(write_st)
                write_st.clear()
                counter += 1
            f.close()

        return errorstr

    # save measunrement data
    def func_STS_Save_Measurement_data(filepath):
        wavelengthtable =[]
        ILdata = []
        LstILdata = []

        errorstr = ""

        #Get rescaling wavelength table
        errorcode,wavelengthtable = _ILSTS.Get_Target_Wavelength_Table(None)
        if (errorcode !=0):
            errorstr = func_return_STSProcessErrorStr(errorcode)
            return errorstr

        for item in Lst_Merge_st:
            #Pull out IL data of aftar merge
            errocode,ILdata = _ILSTS.Get_IL_Merge_Data(None,item)
            if (errorcode !=0):
                errorstr = func_return_STSProcessErrorStr(errorcode)
                return errorstr

            aryIL = array("f",ILdata)               #List to Array
            LstILdata.append(aryIL)


        #Open file And write data for .csv
        with open(filepath,"w",newline ="") as f:
            writer = csv.writer(f)

            hedder =["Wavelength(nm)"]
            writestr =[]

            #hedder
            for item in Lst_Merge_st:
                ch = "Slot" + str(item.SlotNumber) +"Ch" + str(item.ChannelNumber)
                hedder.append(ch)

            writer.writerow(hedder)
            counter = 0
            for wave in wavelengthtable:
                writestr.append(str(wave))

                for item in LstILdata:
                     data = item[counter]
                     writestr.append(data)
                writer.writerow(writestr)
                writestr.clear()
                counter +=1

        f.close()
        return errorstr

    #Load Reference Raw data
    def func_STS_Load_ReferenceRawData(lstchdata,lstmonitor):

        errorstr = ""
        counter = 0
        for item in Lst_Refdata_st:

            chdata = lstchdata[counter]
            arychdata = array("f",chdata)       #List to Array
            arymonitor = array("f",lstmonitor)

            #Add in Reference Raw data
            errorcode = _ILSTS.Add_Ref_Rawdata(arychdata,arymonitor,item)
            if (errorcode !=0):
                errorstr = func_return_STSProcessErrorStr(errorcode)
                return errorstr
            counter +=1
        return errorstr
