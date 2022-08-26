# -*- coding: utf-8 -*-
"""
Created on Fri Jan 21 17:21:13 2022

@author: chentir
"""
from array import array
from ast import Raise
from operator import ilshift
import os
from tokenize import Name
import clr # python for .net
import re
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
    #_reference_data_array : array

    def __init__(self, _tsl, _mpm, _spu ):
        self._tsl = _tsl
        self._mpm = _mpm
        self._spu = _spu
        self._ilsts = ILSTS()
        #self._reference_data_array = _reference_data_array
        self._reference_data_array = []

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

    def set_selected_channels(self,previous_param_data):
        '''This method to select channels to be measured.
        It offers the user to choose between different ways to select MPM channels.
        For this purpose, method calls the following methods:
        - all_chans
        - even_chans
        - odd_chans
        - special
        - cancel
        '''
        if (previous_param_data is not None):
            self.selected_chans = previous_param_data["selected_chans"] #an array, like [1,3,5]
            allModChans = ""
            for thismodchan in self.selected_chans:
                allModChans += ",".join([str(elem) for elem in thismodchan]) + "; " #contains numbers so do a converstion

            print("Loaded the selected channels: " + allModChans.strip())
            return None


        self.selected_chans = []
        #array of arrays: array 0  displays the connected modules
        #the following arrays contain ints of available channels of each module
        self.all_channels = self._mpm.get_mods_chans()

        print('''
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
            print ("\r\n" + "Module {}: Channels {}".format(i,self.all_channels[i]))

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

    def set_selected_ranges(self,previous_param_data):
        
        if (previous_param_data is not None):
            self.selected_ranges = previous_param_data["selected_ranges"] #an array, like [1,3,5]
            str_all_ranges = ""
            str_all_ranges += ",".join([str(elem) for elem in self.selected_ranges])  #contains numbers so do a converstion
            print("Using the loaded dynamic ranges: " + str_all_ranges)

        else:
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
                if (rangeindex == 0 ):
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
    def sts_reference(self):

        for i in self.ref_data:
            print('Connect Slot{} Ch{}, then press ENTER'.format(i.SlotNumber,i.ChannelNumber))
            input()
            #set MPM range for 1st setting renge
            self._mpm.set_range(self.range[0])

            #TSL Wavelength set to use Sweep Start Command
            #self._tsl.start_sweep() #redundant, also exists within sts_sweep_process

            #Sweep handling
            print ("Scanning...")
            self.sts_sweep_process(0)

            #get sampling data & Add in STSProcess Class
            self.get_reference_data(i)

            # rescaling for reference data.. This is called within get_reference_data, so that we can get rescaled power data in the same method.
            #errorcode = self._ilsts.Cal_RefData_Rescaling()
            #if errorcode !=0:
            #    raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

            #TSL Sweep stop
            self._tsl.stop_sweep()

        return None

    def sts_reference_from_saved_file(self):
        if (self._reference_data_array is None or len(self._reference_data_array) == 0):
            raise Exception ("The reference data array cannot be null or empty when loading reference data from files." )
        
        if (len(self._reference_data_array) != len(self.ref_data)):
            raise Exception("The length is difference between the saved reference array and the newly-obtained reference array")

        for cached_ref_object in self._reference_data_array:
            
            #self.ref_data is an array of data structures. We need to get that exact data structure because the object is special.
            #Find the matching data structure between ref_data and reference_data_array.

            for i in [
                x for x in self.ref_data 
                if x.MPMNumber == cached_ref_object["MPMNumber"]
                and x.SlotNumber == cached_ref_object["SlotNumber"]
                and x.ChannelNumber == cached_ref_object["ChannelNumber"]
            ]:
                matched_data_structure = i

            print('Loading reference data for Slot{} Ch{}...'.format(matched_data_structure.SlotNumber,matched_data_structure.ChannelNumber))

            #Get MPM logging data
            #logdata = self._mpm.get_each_chan_logdata(matched_data_structure.SlotNumber, matched_data_structure.ChannelNumber)
            #self.logdata = cached_ref_object.logdata #self.logdata = array('f',logdata) #list to array

            errorcode = self._ilsts.Add_Ref_MPMData_CH(cached_ref_object["logdata"], matched_data_structure)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

            #Get SPU sampling data
            #trigger,monitor = self._spu.get_sampling_raw()

            #Add Monitor data for STS Process Class
            #errorcode = self._ilsts.Add_Ref_MonitorData(trigger,monitor,data_struct_item)
            errorcode = self._ilsts.Add_Ref_MonitorData(cached_ref_object["trigger"], cached_ref_object["monitor"], matched_data_structure)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

            # rescaling for reference data. 
            errorcode = self._ilsts.Cal_RefData_Rescaling()
            if errorcode !=0:
                raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))



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

        # rescaling,
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

            self.il_data = array("d",self.il_data)               #List to Array
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
        '''Get the reference data by using the parameter data structure, as well as the trigger points, and monitor data.'''

        #Get MPM logging data
        logdata = self._mpm.get_each_chan_logdata(data_struct_item.SlotNumber, data_struct_item.ChannelNumber)

        #Add MPM Logging data for STS Process Class
        self.logdata = array('d',logdata) #List to Array

        errorcode = self._ilsts.Add_Ref_MPMData_CH(logdata,data_struct_item)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        #Get SPU sampling data
        trigger,monitor = self._spu.get_sampling_raw()
 
        #Add Monitor data for STS Process Class
        errorcode = self._ilsts.Add_Ref_MonitorData(trigger,monitor,data_struct_item)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        # rescaling for reference data. We must rescale before we get the reference data. Otherwise we end up with way too many monitor and logging points.
        errorcode = self._ilsts.Cal_RefData_Rescaling()
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

        #after rescaling is done, get the raw reference data.
        errorcode,rescaled_ref_pwr,rescaled_ref_mon = self._ilsts.Get_Ref_RawData(data_struct_item,None,None)
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

        errorcode,wavelengtharray = self._ilsts.Get_Target_Wavelength_Table(None)
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))
        
        if (len(wavelengtharray) == 0 or len(wavelengtharray) != len(rescaled_ref_pwr) or len(wavelengtharray) != len(rescaled_ref_mon)):
            raise Exception("The length of the wavelength array is {}, the length of the reference power array is {}, and the length of the reference monitor is {}. They must all be the same length.".format(
                len(wavelengtharray), len(rescaled_ref_pwr), len(rescaled_ref_mon))
            )


        #save all desired reference data into the reference array of this StsProcess class.
        ref_object = {
            "MPMNumber" : data_struct_item.MPMNumber,
            "SlotNumber" : data_struct_item.SlotNumber,
            "ChannelNumber" : data_struct_item.ChannelNumber,
            "logdata" : list(self.logdata), #unscaled logdata data is required if we want to load the reference data later.
            "trigger" : list(array('d',trigger)), #motor positions that correspond to wavelengths. required if we want to load the reference data later.
            "monitor" : list(array('d',monitor)), #unscaled monitor data is required if we want to load the reference data later.
            "rescaled_monitor" : list(array('d',rescaled_ref_mon)), #rescaled monitor data
            "rescaled_wavelength" : list(array('d',wavelengtharray)), #all wavelengths, including triggers inbetween. 
            "rescaled_referencepower" : list(array('d',rescaled_ref_pwr)), #rescaled reference power
        }

        self._reference_data_array.append(ref_object)

        return None

    def get_wavelengths(self, data_struct_item: STSDataStruct, triggerlength: int):
        '''Get the list of wavelengths from the most recent scan.'''
        datapointcount = 0
        wavelengtharray = []
        
        # rescaling for reference data
        errorcode = self._ilsts.Cal_RefData_Rescaling()
        if errorcode !=0:
            raise Exception(str(errorcode) + ": " + stsprocess_err_str(errorcode))

        errorcode,ref_pwr,ref_mon = self._ilsts.Get_Ref_RawData(data_struct_item,None,None) #testing 2...
        errorcode,wavelengthtable = self._ilsts.Get_Target_Wavelength_Table(None)
        #errorcode,wavelengthtable = self._ilsts.Get_Target_Wavelength_Table(wavelengtharray) #TODO; testing.....
        

        #errorcode,datapointcount,wavelengthtable = self._tsl._tsl.Get_Logging_Data(datapointcount, wavelengtharray) #I take 3 seconds??


        
        #errorcode,wavelengtharray = self._ilsts.Get_Target_Wavelength_Table(None)
        #if (errorcode !=0):
        #    raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode) + ". Failed to get wavelengths from TSL.")

        if (len(wavelengthtable) != triggerlength):
            raise Exception ( "The length of the wavelength array is {} but the length of the trigger array is {}. They should have been the same. ".format(
                len(wavelengthtable), triggerlength
            ))

        return wavelengthtable


    # get logging data & add STSProcess class for Measuerment
    def sts_get_meas_data(self,sweepcount):

        for item in self.dut_data:
            if (item.SweepCount != sweepcount):
                continue

            #Get MPM loggin data
            logdata = self._mpm.get_each_chan_logdata(item.SlotNumber,item.ChannelNumber)
            logdata = array("d",logdata)                           #List to Array

            #Add MPM Logging data for STSPrcess Class with STSDatastruct
            errorcode = self._ilsts.Add_Meas_MPMData_CH(logdata,item)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        # Get monitor data
        trigger,monitor = self._spu.get_sampling_raw()

        trigger = array("d",trigger)                             #List to Array
        monitor = array("d",monitor)                             #list to Array

        #search place of add in
        for item in self.dut_monitor:
            if (item.SweepCount != sweepcount):
                continue
            #Add Monirot data for STSProcess Class  with STSDataStruct
            errorcode = self._ilsts.Add_Meas_MonitorData(trigger,monitor,item)
            if (errorcode !=0):
                raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        return None

