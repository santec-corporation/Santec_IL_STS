# -*- coding: utf-8 -*-
#import----------------------------------------
from array import array                             # array
import time                                         #for measurement of time
import csv                                          #for save csv
import numpy                                        #for cast
import clr                                          # python for .net
import os
# santec DLL import-----------------------------

root = str(os.path.dirname(__file__))+'\\DLL\\'
print(root)

path1 ='InstrumentDLL'
path2 ='STSProcess'
#Add in santec.Instrument.DLL
ans = clr.AddReference(root+path1)

print (ans)
from Santec import*                                    #　name space of instrument DLL
from Santec import CommunicationTerminator             # import CommunicationTerminator Enumration Class
from Santec.Communication import CommunicationMethod   # import CommunicationMethod Enumration Class
from Santec.Communication import GPIBConnectType       # import GPIBConnectType Enumration Class
from Santec.Communication import MainCommunication     # import MainCommuncation Class

ans = clr.AddReference(root+path2)
print(ans)

from Santec.STSProcess import*                         # name space of  STSProcess DLL
from Santec.STSProcess import STSDataStruct            # import STSDataStruct structuer Class
from Santec.STSProcess import STSDataStructForMerge    # import STSDataStructForMerge structure class
from Santec.STSProcess import Module_Type              # import Module_Type Enumration Class
from Santec.STSProcess import RescalingMode            #import RescalingMode Enumration Class

# Golbal variable define--------------------------
_TSL = TSL()
_SPU = SPU()                                 #SPU Class instance : Member of "Santec" name space
_MPM = MPM()                                 #MPM Class instance: Member of "Santec" name space
_ILSTS = ILSTS()                             #IL STS Process Class instance : Member of "Santec.STSProcess" name space

#data structure for STS
Lst_Measdata_st = []                        #list of measurement data for STSDataStruct
Lst_Refdata_st = []                         #list of Reference data for STSDatastruct
Lst_MeasMonitor_st = []                     #list of  mesurementmonitor data for STSDataStruct
Lst_RefMonitor_st = []                      #list of refernce monitor data for STSDatastruct
Lst_Merge_st= []                            #list of merge data for STSDatastrunctForMerge

#MPM Range list
Lst_Range = []

#ErrorDictionary
Inst_Error = {}                             #for Instrument DLL error dictionary
Process_Error = {}                          #for STSProcess DLL error dictionary

#Communication Support Function-----------------
# Get USB Resourcee
def func_Get_USB_resouce():
    Comm :str = MainCommunication.Get_USB_Resouce()
    return Comm

# Get SPU(DAQ) Resouce
def func_Get_SPU_resouce():
    errorcode,res = _SPU.Get_Device_ID(None)
    return res

#%%TLS  Functions----------------------------------------------------------------

# TSL Connect
def func_init_TSL(interface,address,port = None):


    # ---Propaty settiong befor "Connect"------------

    # GPIB Terminater can set by TSL Front panel.
    # In this code, GPIB terminator must match TSL's GPIB terminator.
    # When LAN/USB Communication, terminator becomes "Cr"  at TSL.

    # When GPIB communication
   if(interface =="GPIB"):
        _TSL.Terminator = CommunicationTerminator.CrLf
        print(_TSL.Terminator)
        _TSL.GPIBAddress = int(address)
        print(_TSL.GPIBAddress)
        _TSL.Bordnumber = 0
        _TSL.GPIBConnectType = GPIBConnectType.NI4882
        print(_TSL.GPIBConnectType)
        errorcode = _TSL.Connect(CommunicationMethod.GPIB)
        print(errorcode)
    # When LAN Communication
   elif(interface == "LAN"):
        _TSL.Terminator = CommunicationTerminator.Cr
        _TSL.IPAddress  = address
        _TSL.Port = port #port =5000

        errorcode = _TSL.Connect(CommunicationMethod.TCPIP)

     # When USB communication
   elif(interface == "USB"):
       #USB DeviceID is defined uint32, So must be change variable type to unit32
       # this code typechange with numpy array
        ar_address = numpy.array([address],dtype ="uint32")
        _TSL.DeviceID = ar_address[0]
        _TSL.Terminator = CommunicationTerminator.Cr
        errorcode = _TSL.Connect(CommunicationMethod.USB)
   errorstr = ""
   if (errorcode !=0):
       _TSL.DisConnect()
       errorstr = func_return_InstrumentErrorStr(errorcode)
   return errorstr

# retunr TSL-550 or not  True: TSL-550/710  False: TSL-570
def func_TSL_Get550Flag():

    tsl_name = _TSL.Information.ProductName

    if(tsl_name == "TLS-550") or (tsl_name == "TSL-710"):
        return True
    else:
        return False


# retunr Spec Wavelength range
def func_TSL_GetSpecWavelenth():

    errorcode,minwave,maxwave = _TSL.Get_Spec_Wavelength(0,0)

    errorstr = ""
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorstr)
    return errorstr,minwave,maxwave

 # return Sweep speed table of TSL-570
def func_TSL_GetSweepSpeedTable():
     errorcode,table = _TSL.Get_Sweep_Speed_table(None)
     return_table = []
     # this function only support "TSL-570"
     # when othre TSL connected, errorcode return "DeviceError"
     if (errorcode == ExceptionCode.DeviceError):
         errorcode = 0
     else:
         for item in table:
             return_table.append(item)

     errstr = ""
     if (errorcode !=0):
         errstr = func_return_InstrumentErrorStr(errorcode)

     return errstr,return_table

# retune APC max power with wavelength span
def func_TSL_GetMaxAPCPower(minwave,maxwave):
    errorcode,maxpower = _TSL.Get_APC_Limit_for_Sweep(minwave,maxwave,0.0)

    #this functuion only support "TSL-570"
    # when other TSL connected, errorcode return "DeviceError"
    if (errorcode == ExceptionCode.DeviceError):
        maxpower = 999
        errorcode = 0

    errorstr = ""
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)

    return errorstr,maxpower

 # Set APC power of TSL
def func_TSL_SetPower(power):
    errorcode = _TSL.Set_APC_Power_dBm(power)

    errorstr = ""
    if(errorcode != 0):
        errorstr = func_return_InstrumentErrorStr(errorcode)
        return errorstr

    errorcode = _TSL.TSL_Busy_Check(3000)
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)

    return errorstr

# Set wavelenth(nm) of TSL
def func_TSL_SetWavelength(wavelength):
    errorcode = _TSL.Set_Wavelength(wavelength)

    errorstr = ""
    if (errorcode != 0):
         errorstr = func_return_InstrumentErrorStr(errorcode)
         return errorstr

    errorcode = _TSL.TSL_Busy_Check(3000)
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)
    return errorstr


# Set Sweep parameter for STS of TSL
def func_TSL_SetSweep_Paramters(startwave,stopwave,resstep,speed):
    #this function return error code & TSL actual trigger step
    errorcode,acctual_step = _TSL.Set_Sweep_Parameter_for_STS(startwave,stopwave,speed,resstep,0)

    errorstr =""
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)

    return errorstr,acctual_step

#%%MPM Function------------------------------------------------------------------

# MPM Connect
def func_init_MPM(interface,address, port = None):

    mpm_commincation_method : CommunicationMethod

    #When GPIB Commincation
    if (interface == "GPIB"):
        mpm_commincation_method = CommunicationMethod.GPIB
        _MPM.GPIBAddress = int(address)
        _MPM.Bordnumber = 0
        _MPM.GPIBConnectType = GPIBConnectType.NI4882
    else :
        mpm_commincation_method  = CommunicationMethod.TCPIP
        _MPM.IPAddress = address
        _MPM.Port = port #port = 5000

    _MPM.TimeOut = 2000             # time out value for MPM
    errorstr = ""

    errorcode = _MPM.Connect(mpm_commincation_method)
    if (errorcode !=0):
        _MPM.DisConnect()
        errorstr = func_return_InstrumentErrorStr(errrorcode)

    return errorstr

#return enable ch list for module type
def func_MPM_Get_Eablech():

    enablech = []

    for slotcount in range(5):
        if(_MPM.Information.ModuleEnable[slotcount]== True):
            if(func_MPM_Check_212(slotcount) == True):
                enablech.append("Slot{0}Ch1".format(str(slotcount)))
                enablech.append("Slot{0}Ch2".format(str(slotcount)))
            else :
                enablech.append("Slot{0}Ch1".format(str(slotcount)))
                enablech.append("Slot{0}Ch2".format(str(slotcount)))
                enablech.append("Slot{0}Ch3".format(str(slotcount)))
                enablech.append("Slot{0}Ch4".format(str(slotcount)))
    return enablech

# Check MPM module type
def func_MPM_Check_Module():

    flag_215 = False
    flag_213 = False
    slot = 0
    count_215 = 0
    errorcode = 0

    for slotcount in range(5):
        if(_MPM.Information.ModuleEnable[slotcount] == True):
            flag_215= func_MPM_Check_215(slotcount)
            flag_213 = func_MPM_Check_213(slotcount)
            slot += 1
            if (flag_215 == True):
                count_215 += 1
    errorstr = ""
    # MPM-215 can't use with other module
    if (flag_215 == True) and (count_215 != slot):
       errorstr = "MPM-215 can't use with other module"

    return errorstr, flag_215,flag_213

# Module 215 or not
def func_MPM_Check_215(slotcount):
    if (_MPM.Information.ModuleType[slotcount] == "MPM-215"):
        return True
    else :
        return False

# Module 213 or not
def func_MPM_Check_213(slotcount):
    if (_MPM.Information.ModuleType[slotcount] == "MPM-213"):
        return True
    else :
        return False
# Module 212 or not
def func_MPM_Check_212(slotcount):
    if (_MPM.Information.ModuleType[slotcount]== "MPM-212"):
        return True
    else :
        return False

#MPM Set Power range
def func_MPM_SetRange(powerrange):
    errorcode = _MPM.Set_Range(powerrange)

    errorstr = ""
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)
    return errorstr
#MPM Zeroing
def  func_MPM_Zeroing():
    errorcode = _MPM.Zeroing()
    errorstr = ""

    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)
    return errorstr
#MPM Get Averaging Time
def func_MPM_GetAveragingtime():
    errorcode,averaging_time = _MPM.Get_Averaging_Time(0)

    errorstr = ""
    if (errorcode != 0):
        errorstr = func_return_InstrumentErrorStr(errorcode)

    return errorstr,averaging_time
# MPM Set Logging parameter for STS
def func_MPM_SetLoggingParameters(startwave,stopwave,resstep,speed):
    errorcode = _MPM.Set_Logging_Paremeter_for_STS(startwave,stopwave,resstep,speed,MPM.Measurement_Mode.Freerun)

    errorstr = ""
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)

    return errorstr

#%%SPU Function------------------------------------------------------------------
#SPU Connect
def func_init_SPU(devicename):
    _SPU.DeviceName = str(devicename)

    errorcode,ans = _SPU.Connect("")
    errorstr = ""
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)

    return errorstr

# SPU Set logging paramter
def func_SPU_SetLoggingparameters(startwave,stopwave,speed,tsl_acctualste):
    errorcode = _SPU.Set_Sampling_Parameter(startwave,stopwave,speed,tsl_acctualste)

    errorstr = ""
    if (errorcode !=0):
        errorstr = func_return_InstrumentErrorStr(errorcode)

    return errorstr

#instrument Disconnect
def func_Instrument_Disconect():
    _TSL.DisConnect()
    _MPM.DisConnect()
    _SPU.DisConnect()

#%%instrument Error handling-----------------------------------------------------
# define Error deictionary for Santec DLL
def func_set_ErrorDictionary():

    #for instrument DLL
    Inst_Error[-2147483648] = "Unknown"
    Inst_Error[-40] = "InUseError"
    Inst_Error[-30] = "ParameterError"
    Inst_Error[-20] = "DeviceError"
    Inst_Error[-14] = "CommunicationFaulure"
    Inst_Error[-13] = "UbauthorizeAccess"
    Inst_Error[-12] = "IOException"
    Inst_Error[-11] = "NotConnected"
    Inst_Error[-10] = "Uninitialized"
    Inst_Error[-2]  = "TimeOut"
    Inst_Error[-1]  = "Failure"
    Inst_Error[-5]  = "CountMismatch"
    Inst_Error[0]   = "Succeed"
    Inst_Error[11]  = "AlreadyConnected"
    Inst_Error[10]  = "Stopped"

    Process_Error[-2147483648] = "Unknown"
    Process_Error[-1115] = "MeasureNotMatch"
    Process_Error[-1114] = "MeasureNotRescaling"
    Process_Error[-1113] = "MeasureNotExist"
    Process_Error[-1112] = "ReferenceNotMatch"
    Process_Error[-1111] = "ReferenceNotRescaling"
    Process_Error[-1110] = "ReferenceNotExist"
    Process_Error[-1000] = "NoCalculated"
    Process_Error[-30] = "ParameterError"
    Process_Error[-1] = "Failure"
    Process_Error[0] = "Succeed"


# reutrn  InstrumentDLL Error string
def func_return_InstrumentErrorStr(errorcode):
    str_error = Inst_Error[errorcode]
    return str(str_error)

# return STSProcess DLL Error string
def func_return_STSProcessErrorStr(errorcode):
    str_error = Process_Error[errorcode]
    return str(str_error)

#%%STS function -----------------------------------------------------------------
def func_STS_SetParameters(minwave,maxwave,wavestep,speed):

    errorstr = ""
    #------instrument setting
    #Sweep parameter for TSL
    errorstr,acctual_step  = func_TSL_SetSweep_Paramters(minwave, maxwave, wavestep, speed)
    if (errorstr !=""):
        return errorstr
    #Logging parameters for MPM
    errorstr = func_MPM_SetLoggingParameters(minwave, maxwave, wavestep, speed)
    if (errorstr != ""):
        return errorstr

    errorstr,averaging_time = func_MPM_GetAveragingtime()
    if (errorstr !=""):
        return errorstr

    #Logging parameter for SPU(DAQ)
    errorstr  = func_SPU_SetLoggingparameters(minwave, maxwave, speed, acctual_step)
    if (errorstr != ""):
        return errorstr

    #pass MPM averaging time to SPU　 Class
    _SPU.AveragingTime = averaging_time


    #-----STS Process setting Class
    #Measurement data clear
    sts_error = _ILSTS.Clear_Measdata()
    if (sts_error !=0):
        errorstr = func_return_STSProcessErrorStr(sts_error)
        return errorstr
    #Reference data Clear
    sts_error  = _ILSTS.Clear_Refdata()
    if (sts_error !=0):
        errorstr = func_return_STSProcessErrorStr(sts_error)
        return errorstr
    #Make Wavelength table at sweep
    sts_error = _ILSTS.Make_Sweep_Wavelength_Table(minwave,maxwave,acctual_step)
    if (sts_error !=0):
        errorstr = func_return_STSProcessErrorStr(sts_error)
        return errorstr
    #make wavelength table as rescaling
    sts_error = _ILSTS.Make_Target_Wavelength_Table(minwave,maxwave,wavestep)
    if (sts_error !=0):
        errorstr = func_return_STSProcessErrorStr(sts_error)
        return errorstr

    #Set Rescaling mode for STSProcess class
    sts_error = _ILSTS.Set_Rescaling_Setting(RescalingMode.Freerun_SPU,averaging_time,True)
    if (sts_error !=0):
        errorstr = func_return_STSProcessErrorStr(sts_error)
        return errorstr

    return errorstr

# STS Reference handling
def func_STS_Reference():
    errorstr = ""
    for i in Lst_Refdata_st:
        print('Connect Slot{}Ch{}, then press any key'.format(i.SlotNumber,i.ChannelNumber))
        input()
        #set MPM range for 1st setting renge
        errorstr = func_MPM_SetRange(Lst_Range[0])
        if (errorstr !=""):
            return errorstr

        #TSL Wavelength set to use Sweep Start Command
        errorcode = _TSL.Sweep_Start()
        if (errorcode !=0):
            errorstr = func_return_InstrumentErrorStr(errorcode)
            return errorstr

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
def func_STS_SweepProcess():
    errorstr =""
    #MPM Logging Start
    errorcode =_MPM.Logging_Start()
    if (errorcode !=0):
        errorstr  =func_return_InstrumentErrorStr(errorcode)
        return errorstr

    # Waiting for TSL sweep status to "Trigger Standby"
    errorcode = _TSL.Waiting_For_Sweep_Status(2000,TSL.Sweep_Status.WaitingforTrigger)

    #errorhandling  TSL error -> MPM Logging stop
    if (errorcode != 0):
        _MPM.Logging_Stop()
        errorstr = func_return_InstrumentErrorStr(errorcode)
        return errorstr

    #SPU sampling start
    errorcode = _SPU.Sampling_Start()
    if(errorcode !=0):
        _MPM.Logging_Stop()
        _TSL.Sweep_Stop()
        errorstr = func_return_InstrumentErrorStr(errorcode)
        return errorstr

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











'''
IL STS Sample Software for Python
IL STS module
Ver 1.0.0
Copyright 2021 Santec
'''
