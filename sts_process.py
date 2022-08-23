# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:21:13 2022

@author: chentir
"""
from array import array
import os
from tokenize import Name
import clr # python for .net
import re
import time
from datetime import datetime
import json
import csv
from dev_intr_class import SpuDevice
from mpm_instr_class import MpmDevice
from tsl_instr_class import TslDevice

ROOT = str(os.path.dirname(__file__))+'\\DLL\\'
print(ROOT)

PATH2 ='STSProcess'
#Add in santec.STSProcess.DLL
ans = clr.AddReference(ROOT+PATH2)
print(ans)

from Santec.STSProcess import * # namespace of  STSProcess DLL
from Santec.STSProcess import ILSTS
from Santec.STSProcess import STSDataStruct            # import structure Class
from Santec.STSProcess import STSDataStructForMerge    # import structure Class
from Santec.STSProcess import Module_Type              # import  Enumration Class
from Santec.STSProcess import RescalingMode            #import  Enumration Class

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


        #Logging parameters for MPM
        self._mpm.set_logging_parameters(self._tsl.startwave,
                                         self._tsl.stopwave,
                                         self._tsl.step,
                                         self._tsl.speed)

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

        return stsprocess_err_str(sts_error)

    def set_selected_channels(self,_mpm):
        '''This method to select channels to be measured.
        It offers the user to choose between different ways to select MPM channels.
        For this purpose, method calls the following methods:
        - all_chans
        - even_chans
        - odd_chans
        - special
        - cancel'''
        self.selected_chans = []
        #array of arrays: array 0  displays the connected modules
        #the following arrays contain ints of available channels of each module
        self.all_channels = self._mpm.get_mods_chans()

        print(
        '''
Select channels to be measured:
            1. All channels
            2. Even channels
            3. Odd channels
            4. Specific channels
            5. Cancel

Available modules/channels:

        ''')
        for i in range(len(self.all_channels)):
            if len(self.all_channels[i]) == 0:
                continue
            print ('''
            Module {}: Channels {}'''.format(i,self.all_channels[i]))

        choices = {'1': self.set_all_chans,
                   '2': self.set_even_chans,
                   '3': self.set_odd_chans,
                   '4': self.set_special,
                   '5': self.cancel}

        selection = input()
        choices[selection]()
        return None

    def set_all_chans(self):
        '''Selects all modules and all channels that are connected to MPM.'''
        for i in range(len(self.all_channels)):
            for j in self.all_channels[i]:
                self.selected_chans.append([i,j])
        return None

    def set_even_chans(self):
        '''Selects only even channels on the MPM.'''
        for i in range(len(self.all_channels)):
            for j in self.all_channels[i]:
                if j%2 ==0:
                    self.selected_chans.append([i,j])
        return None

    def set_odd_chans(self):
        '''Selects only odd channels on the MPM.'''
        for i in range(len(self.all_channels)):
            for j in self.all_channels[i]:
                if j%2 !=0:
                    self.selected_chans.append([i,j])
        return None

    def set_special(self):
        '''Manually enter/select the channels to be measured'''
        print('Input (module,channel) to be tested [ex: (0,1); (1,1)]')
        selection = input()
        selection = re.findall(r"[\w']+",selection)

        
        i=0
        while i<= len(selection)-1:
            self.selected_chans.append([selection[i],selection[i+1]])
            i+=2
        return None

    def cancel(self):
        self._tsl.disconnect()
        self._mpm.disconnect()
        self._spu.disconnect()

    def set_selected_ranges(self,_mpm):
        self.selected_ranges = []
        print('Select the dynamic range. ex: 1, 3, 5')
        print('Available dynamic ranges:')
        i=1
        self._mpm.get_range()
        for range in self._mpm.rangedata:
            print('{}- {}'.format(i,range))
            i +=1
        selection = input()
        self.selected_ranges = re.findall(r"[\w']+",selection)
        #convert the string ranges to ints, because that is what the DLL is expecting. 
        self.selected_ranges = [int(i) for i in self.selected_ranges] 
        return None

    # Config each STSDatastruct from ch data And ranges
    def set_data_struct(self):
        '''Create the data structures, which includes the potentially saveable reference data'''
        counter =1
        #List data clear
        self.dut_monitor = []
        self.dut_data = []
        self.merge_data = []
        self.ref_monitor = []
        self.ref_data = []
        self.range = []

        # config STSDatastruct for each measurment
        for m_range in self.selected_ranges:
            for ch in self.selected_chans:
                data_st = STSDataStruct()
                data_st.MPMNumber = 0
                data_st.SlotNumber = int(ch[0])      #slot number
                data_st.ChannelNumber = int(ch[1])   #channel number
                data_st.RangeNumber = m_range   #array of MPM ranges
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
                    self.ref_monitor.append(data_st)

                # reference monitor data need only 1 data
                #if (chindex ==0) and (rangeindex == 0):
                #    self.ref_monitor.append(data_st)

            counter +=1

        #config STSDataStruct for merge
        for ch in self.selected_chans:
            mergest = STSDataStructForMerge()
            mergest.MPMnumber = 0
            mergest.SlotNumber = int(ch[0])      #slot number
            mergest.ChannelNumber = int(ch[1])   #channel number
            mergest.SOP = 0

            self.merge_data.append(mergest)

    # STS Reference handling
    def sts_reference(self, _mpm):

        for i in self.ref_data:
            print('Connect Slot{}Ch{}, then press ENTER'.format(i.SlotNumber,i.ChannelNumber))
            input()
            #set MPM range for 1st setting renge
            self._mpm.set_range(self.range[0])

            #TSL Wavelength set to use Sweep Start Command
            self._tsl.start_sweep()

            #Sweep handling
            self.sts_sweep_process(0)

            #get sampling data & Add in STSProcess Class
            self.get_reference_data(i)

            # rescaling for reference data
            errorcode = self._ilsts.Cal_RefData_Rescaling()
            if errorcode !=0:
                raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

            #TSL Sweep stop
            self._tsl.stop_sweep()

        return None

    #STS Measurement handling
    def sts_measurement(self):

        #TSL Sweep Start
        #self._tsl.start_sweep() #moved to within the sts_sweep_process method, so that repeat scans properly work, 2022.08.22.

        #Range loop
        sweepcount = 1
        for mpmrange in self.range:
            #set MPM Range
            errorstr = self._mpm.set_range(mpmrange)

            #sweep handling
            errorstr = self.sts_sweep_process(sweepcount)

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

        #####################################################################!!!
        #This portion of the code just to get wavelengths and IL data at the end of the scan
        #It can be commented out if needed
        self.wavelengthtable =[]
        self.il_data= []
        self.il_data_array = []

        #Get rescaling wavelength table
        for wav in list(self._ilsts.Get_Target_Wavelength_Table(None)[1]):
            self.wavelengthtable.append(wav)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        for item in self.merge_data:
            #Pull out IL data of aftar merge
            errorcode,self.il_data = self._ilsts.Get_IL_Merge_Data(None,item)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

            self.il_data = array("f",self.il_data)               #List to Array
            self.il_data_array.append(self.il_data)
        self.il = []
        for i in self.il_data_array[0]:
            self.il.append(i)
        #####################################################################

        return None

    # STS Sweep Process
    def sts_sweep_process(self, sweepcount:int):
        
        #TSL Sweep Start
        self._tsl.start_sweep()
        
        #MPM Logging Start
        self._mpm.logging_start()
        try:
            self._tsl.wait_for_sweep_status(waiting_time=3000, sweep_status=4) #WaitingforTrigger
            self._spu.sampling_start()
            self._tsl.soft_trigger()
            self._spu.sampling_wait()
            self._mpm.wait_log_completion(sweepcount)
            self._mpm.logging_stop(True)
        except RuntimeError as scan_exception:
            self._tsl.stop_sweep(False)
            self._mpm.logging_stop(False)
            raise scan_exception
        except Exception as tsl_exception:
            self._mpm.logging_stop(False)
            raise tsl_exception
        self._tsl.wait_for_sweep_status(waiting_time=5000, sweep_status=1) #Standby

        return None

    # get logging data & add STSProcess Class for Reference
    def get_reference_data(self, data_struct_item):
        errorstr = ""

        #Get MPM logging data
        logdata = self._mpm.get_each_chan_logdata(data_struct_item.SlotNumber, data_struct_item.ChannelNumber)

        #Add MPM Logging data for STS Process Class
        self.logdata = array('f',logdata)                       #List to Array
        errorcode = self._ilsts.Add_Ref_MPMData_CH(logdata,data_struct_item)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        #Get SPU sampling data
        trigger,monitor = self._spu.get_sampling_raw()

        #Add Monitor data for STS Process Class
        errorcode = self._ilsts.Add_Ref_MonitorData(trigger,monitor,data_struct_item)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))
    
        return None

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

    def check_and_load_previous_param_data(self, file_last_scan_params):
        '''If a file for a previous scan exists, then ask the user if it should be used to load ranges, channels, etc.'''
        if (os.path.exists(file_last_scan_params) == False):
            return 
        
        #load the previous settings
        raise Exception ("not yet implemented")

    def sts_save_param_data(self, file_last_scan_params:str):
        self.sts_rename_old_file(file_last_scan_params)

        #create a psuedo object for our array of STSDataStruct (self.ref_data)

        arrayofdatastructures = []
        index = 0
        for this_datastruct in self.ref_data:
            
            #create a new hash table with this data
            thisHashOfDataStructProps = {
                "MPMNumber" : this_datastruct.MPMNumber,
                "SlotNumber" : this_datastruct.SlotNumber,
                "ChannelNumber" : this_datastruct.ChannelNumber,
                "RangeNumber" : this_datastruct.RangeNumber,
                "SweepCount" : this_datastruct.SweepCount,
                "SOP" : this_datastruct.SOP,
            }
            arrayofdatastructures.append(thisHashOfDataStructProps)
            index += 1
            
        jsondata = {
            "selected_chans" : self.selected_chans,
            "selected_ranges" :self.selected_ranges,
            "startwave" :self._tsl.startwave,
            "stopwave" :self._tsl.stopwave,
            "step" :self._tsl.step,
            "speed" :self._tsl.speed,
            "actual_step" :self._tsl.actual_step,
            "data_structures" : arrayofdatastructures,

        }


        #save several of our data structure properties. 
        with open(file_last_scan_params, 'w') as exportfile:
            json.dump(jsondata, exportfile) #an array
        
        return None

    

    def sts_rename_old_file(self, filename: str):
        if (os.path.exists(filename)):
            timenow = datetime.now()
            os.rename(filename, timenow.strftime("%Y%m%d_%H%M%S") + "_" + filename )
        
        return None
