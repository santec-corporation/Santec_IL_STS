# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:21:13 2022

@author: chentir
"""
from array import array
import os
import clr
import re
import time
import csv
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
            errorstr = self.sts_sweep_process()
            if (errorstr != ""):
                return errorstr

            #get sampling data & Add in STSProcess Class
            errorstr = self.get_reference_data(i)

            # rescaling for reference data
            errorcode = self._ilsts.Cal_RefData_Rescaling()
            if errorcode !=0:
                raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

            #TSL Sweep stop
            self._tsl.stop_sweep()
        return None

    #STS Measurement handling
    def sts_measurement(self):
        errorstr = ""

        #TSL Sweep Start
        self._tsl.start_sweep()


        #Range loop
        sweepcount = 1
        for mpmrange in self.range:
            #set MPM Range
            errorstr = self._mpm.set_range(mpmrange)

            #sweep handling
            errorstr = self.sts_sweep_process()

            #Get Reference data
            errorstr = self.sts_get_meas_data(sweepcount)

            sweepcount += 1

        # rescaling
        errorcode = self._ilsts.Cal_MeasData_Rescaling()
        if (errorcode !=0):
            raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

        # range data merge
        errorcode = self._ilsts.Cal_IL_Merge(Module_Type.MPM_211)
        if (errorcode != 0):
            raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

        #TSL stop
        self._tsl.stop_sweep()

        return None

    # STS Sweep Process
    def sts_sweep_process(self):
        #MPM Logging Start
        self._mpm.logging_start() #if this errors, an exception is thrown

        try:
            self._tsl.wait_for_sweep_status(waiting_time= 2000,sweep_status=4) #WaitingforTrigger
            self._spu.sampling_start()
            self._tsl.soft_trigger()
            self._mpm.wait_log_completion()  #DONE but need to be checked
            self._mpm.logging_stop(True)
        except RuntimeError as scan_exception:
            self._tsl.stop_sweep(False)
            self._mpm.logging_stop(False)
            raise scan_exception
        except Exception as tsl_exception:
            self._mpm.logging_stop(False)
            raise tsl_exception
        self._tsl.wait_for_sweep_status(waiting_time=5000, sweep_status=1) #Standby 

        #TSL Wavelength set to use Sweep Start Command for next sweep
        self._tsl.start_sweep()
        return None

    # get logging data & add STSProcess Class for Reference
    def get_reference_data(self, item):
        errorstr = ""

        # for item in Lst_Refdata_st:
        #Get MPM logging data
        logdata = self._mpm.get_each_chan_logdata(item.SlotNumber, item.ChannelNumber)

        #Add MPM Logging data for STS Process Class
        logdata = array('f',logdata)                       #List to Array
        errorcode = self._ilsts.Add_Ref_MPMData_CH(logdata,item)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        #Get SPU sampling data
        trigger,monitor = self._spu.get_sampling_raw()

        #Add Monitor data for STS Process Class
        errorcode = self._ilsts.Add_Ref_MonitorData(trigger,monitor,self.ref_monitor[0])
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

    # get logging data & add STSProcess class for Measuerment
    def sts_get_meas_data(self,sweepcount):

        for item in self.dut_data:
            if (item.SweepCount != sweepcount):
                continue

            #Get MPM loggin data
            logdata = self._mpm.get_each_chan_logdata(item.SlotNumber,item.ChannelNumber)
            logdata = array("f",logdata)                           #List to Array

            #Add MPM Logging data for STSPrcess Class with STSDatastruct
            errorcode = self._ilsts.Add_Meas_MPMData_CH(logdata,item)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        # Get monitor data
        trigger,monitor = self._spu.get_sampling_raw()

        trigger = array("f",trigger)                             #List to Array
        monitor = array("f",monitor)                             #list to Array

        #search place of add in
        for item in self.dut_monitor:
            if (item.SweepCount != sweepcount):
                continue
            #Add Monirot data for STSProcess Class  with STSDataStruct
            errorcode = self._ilsts.Add_Meas_MonitorData(trigger,monitor,item)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        return None

    # Save Reference raw data
    def sts_save_ref_rawdata(self,filepath):
        #wavelength data
        errorcode,wavetable = self._ilsts.Get_Target_Wavelength_Table(None)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        lstpow = []
        #Pull out reference raw data of aftar rescaling
        for item in self.ref_data:
            errorcode,ref_pwr,ref_mon = self._ilsts.Get_Ref_RawData(item,None,None)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

            ref_pwr = array("f",ref_pwr)     #List to Array
            ref_mon = array("f",ref_mon)
            lstpow.append(ref_pwr)

        #File open and write data  for .csv
        with open(filepath,"w",newline="")as f:
            writer = csv.writer(f)
            header = ["Wavelength(nm)"]

            #for hedder
            for item in self.ref_data:
                header_str  = "Slot" +str(item.SlotNumber) +"Ch" +str(item.ChannelNumber)
                header.append(header_str)
            header_str = "Monitor"
            header.append(header_str)
            writer.writerow(header)

            writest = []
            #for data
            counter = 0
            for wave in wavetable:
                writest.append(wave)
                for item in lstpow:
                    data = item[counter]
                    writest.append(data)

                data = ref_mon[counter]
                writest.append(data)
                writer.writerow(writest)
                writest.clear()
                counter +=1

            f.close()

        return None

    #Save measurement Rawdata for specific range
    def sts_save_rawdata(self,fpath,mpmrange):
        errorstr = ""

        #wavelength table
        errorcode,wavetable = self._ilsts.Get_Target_Wavelength_Table(None)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        lstpow = []
        #data
        for item in self.dut_data:
            print(item)
            if (item.RangeNumber != mpmrange):
                print('hey')
                print(item.RangeNumber)
                input()
                continue
            #Pull out measurement raw data of aftar rescaling
            errorcode,dut_pwr,dut_mon = self._ilsts.Get_Meas_RawData(item,None,None)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

            dut_pwr = array("f",dut_pwr)      #List to Array
            dut_mon = array("f",dut_mon)      #List to Array
            lstpow.append(dut_pwr)

        #for hedder
        header = ["Wavelength(nm)"]

        for item in self.dut_data:
            if (item.RangeNumber != mpmrange):
                continue
            header_str = "Slot" + str(item.SlotNumber) + "Ch" + str(item.ChannelNumber)
            header.append(header_str)

        header_str = "Monitor"
        header.append(header_str)

        #Open file and write data for .csv
        with open(fpath,"w",newline = "") as f:
            writer = csv.writer(f)
            writer.writerow(header)

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
                data = dut_mon[counter]
                write_st.append(data)
                writer.writerow(write_st)
                write_st.clear()
                counter += 1
            f.close()

        return errorstr

    # save measunrement data
    def sts_save_meas_data(self,filepath):
        wavelengthtable =[]
        self.il_data= []
        il_data_array = []

        #Get rescaling wavelength table
        errorcode,wavelengthtable = self._ilsts.Get_Target_Wavelength_Table(None)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        for item in self.merge_data:
            #Pull out IL data of aftar merge
            errorcode,self.il_data = self._ilsts.Get_IL_Merge_Data(None,item)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

            self.il_data = array("f",self.il_data)               #List to Array
            il_data_array.append(self.il_data)


        #Open file And write data for .csv
        with open(filepath,"w",newline ="") as f:
            writer = csv.writer(f)

            header =["Wavelength(nm)"]
            writestr =[]

            #hedder
            for item in self.merge_data:
                ch = "Slot" + str(item.SlotNumber) +"Ch" + str(item.ChannelNumber)
                header.append(ch)

            writer.writerow(header)
            counter = 0
            for wave in wavelengthtable:
                writestr.append(str(wave))

                for item in il_data_array:
                     data = item[counter]
                     writestr.append(data)
                writer.writerow(writestr)
                writestr.clear()
                counter +=1

        f.close()
        return None

    #Load Reference Raw data
    def sts_load_ref_data(self,lstchdata,lstmonitor):

        errorstr = ""
        counter = 0
        for item in self.ref_data:

            chdata = lstchdata[counter]
            arychdata = array("f",chdata)       #List to Array
            arymonitor = array("f",lstmonitor)

            #Add in Reference Raw data
            errorcode = self._ilsts.Add_Ref_Rawdata(arychdata,arymonitor,item)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))
            counter +=1
        return errorstr
