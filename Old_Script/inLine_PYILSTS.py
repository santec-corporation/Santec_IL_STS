# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 15:23:43 2021

@author: chentir
"""
#%% Import packages

from decimal import Decimal, ROUND_HALF_UP   # for rounding
import IL_STS as STS
from Get_address import Get_address_IL
import pandas as pd
from datetime import datetime
import os
import csv
import glob
from matplotlib.pyplot import plot

#%% Initialization
TSL, OPM, Dev = Get_address_IL()

errorcode = STS.func_init_TSL('GPIB',TSL.split('::')[1])

if errorcode != "":
    print("IL_STS","TSL Connection Error")

errorcode = STS.func_init_MPM('GPIB',OPM.split('::')[1])
if errorcode != "":
    print("IL_STS","MPM Connection Error")

errorcode = STS.func_init_SPU(Dev)
if errorcode !="":
    print("IL_STS","SPU Connection Error")

#-------TSL handling
flag_550 = STS.func_TSL_Get550Flag()                                #550/710 or not
errorcode,minwave,maxwave = STS.func_TSL_GetSpecWavelenth()         #get spec wavelength(nm)

if flag_550 == True:
    sweep_table = None
    maxpow = 10
else:
    # this handling only support for TSL-570
    errorcode,sweep_table =STS.func_TSL_GetSweepSpeedTable()        #get Sweep speed tabel

    if errorcode !="":
        print("IL_STS",errorcode)
    #get APC limit power for wavelength range:
    errorcode,maxpow = STS.func_TSL_GetMaxAPCPower(minwave,maxwave)

    if errorcode != "":
        print("IL_STS",errorcode)

maxpow = Decimal(str(maxpow)).quantize(Decimal('0'),rounding = ROUND_HALF_UP)

errorcode,Flag_215,Flag_213 = STS.func_MPM_Check_Module()

if errorcode != "":
    print("IL_STS",errorcode)

#-specify enable range for module
global rangedata
rangedata = []
if Flag_215 == True:
    rangedata = [1]
elif Flag_213 == True:
    #213 have 4 ranges
    rangedata = [1,2,3,4]
else:
    rangedata = [1,2,3,4,5]

#%% Function definitions
def func_set_sweep_paramter():
    print('Input Start Wavelength (nm):')
    minwave = input()
    print('Input Stop Wavelength (nm):')
    maxwave = input()
    print('Input Sweep Step (pm):')
    wavestep = input()
    if flag_550 == True:
        print('Input Sweep Speed (nm/sec):')
        speed = input()
    else :
        print('Select sweep speed (nm/sec):')
        num = 1
        for i in sweep_table:
            print(str(num)+'- '+str(i))
            num +=1
        speed = sweep_table[int(input())-1]
    print('Input Output Power (dB):')
    power = input()

    minwave = float(minwave)
    maxwave = float(maxwave)
    wavestep = float(wavestep)/1000
    speed = float(speed)
    power = float(power)

    #TSL Power setting
    errorstr = STS.func_TSL_SetPower(power)

    if errorstr !="":
        print("IL_STS",errorstr)
        return

    # setting sweep condition for each insturments
    errorstr = STS.func_STS_SetParameters(minwave,maxwave,wavestep,speed)
    if errorstr != "":
        print("ILSTS",errorstr)
        return

    #set TSL sweep start wavelength
    errorstr = STS.func_TSL_SetWavelength(minwave)

    if errorstr !="":
        print("IL_STS",errorstr)
        return

    enablech = STS.func_MPM_Get_Eablech()                                #get MPM enable ch

    print ('How many channels will be measured?')
    numOfChan = input()
    while int(numOfChan)>len(enablech) or int(numOfChan) == 0:
        print('Invalid number of Channels')
        print ('How many channels will be measured?')
        numOfChan = input()

    print ('Select channels to be measured:')
    numChan = 1
    for i in enablech:
        print('{} - {}'.format(numChan,i))
        numChan+=1

    #-select slot and module
    global lstusech
    lstusech = []
    i=1
    while i <= int(numOfChan):
        print('Select Channel {}'.format(i))
        lstusech.append(enablech[int(input())-1])
        i+=1

    print ('How many power ranges will be used?')
    numOfRange = input()
    while int(numOfRange)>len(rangedata) or int(numOfRange) == 0:
        print('Invalid number of power ranges')
        print ('How many power ranges will be used?')
        numOfRange = input()


    #-select power range
    global lstrange
    lstrange = []
    print ('Select power range:')
    numRange = 1
    for i in rangedata:
        print('{} - {}'.format(numRange,i))
        numRange+=1

    i=1
    while i <= int(numOfRange):
        print('Select range {}'.format(i))
        lstrange.append(rangedata[int(input())-1])
        i+=1
    STS.func_STS_SetDataStruct(lstusech,lstrange)

    global fieldnames
    fieldnames = ['Start Wavelength (nm)', 'Stop Wavelength (nm)', 'Step (pm)',
                 'Speed (nm/sec)', 'Power (dBm)', 'Channel list', 'Power range list']
    global rows
    rows = [
        {'Start Wavelength (nm)': minwave,
         'Stop Wavelength (nm)': maxwave,
         'Step (pm)': str(float(wavestep)*1000),
         'Speed (nm/sec)': speed,
         'Power (dBm)': power,
         'Channel list': lstusech,
         'Power range list':lstrange}
        ]

    print("IL_STS","Setting Completed.")

def func_get_reference():
    with open('Last Scan params.csv', 'w', encoding='UTF8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        f.close()
    errorstr = STS.func_STS_Reference()
    if errorstr != "":
        print("IL_STS",errorstr)
        return

    print("IL_STS","Refernce Completed.")

def check_ref_file():
    if len(glob.glob('REF*.csv'))!=0:
        print('Load previous reference data?')

def func_get_measure():
    errorstr = STS.func_STS_Measurement()
    if errorstr !="":
        print("IL_STS",errorstr)
        return

    fileName = 'IL_{}'.format(datetime.today().strftime('%Y%m%d%H%M%S'))
    filepath = r'.\{}.csv'.format(fileName)
    errorstr = STS.func_STS_Save_Measurement_data(filepath)
    if errorstr != "":
        print("IL_STS",errorstr)
        return

    print("IL_STS","Completed.")

def func_get_reference_rawdata():
    fileName = 'REF_{}'.format(datetime.today().strftime('%Y%m%d%H%M%S'))
    filepath = r'.\{}.csv'.format(fileName)

    errorstr = STS.func_STS_Save_Referance_Rawdata(filepath)
    if errorstr != "":
        print("IL_STS",errorstr)
        return

    print("IL_STS","Completed")

def func_Load_ReferenceData(filepath):
    #Load file data

    with open(filepath,"r",newline="") as f:
        reader = csv.reader(f)
        #for header
        header  = next(f)
        header = header.strip()
        lstheader = header.split(",")

        chcount = len(lstheader)-2
        lstcsv_ch = []
        lstcsv_wave = []
        lstcsvmonitor = []
        lstcsv_chdata = [[]for i in range(chcount)]
        for data in lstheader:
            if(data == "Wavelength(nm)") or (data =="Monitor"):
                continue
            lstcsv_ch.append(data)
        #check setting condition match or not

        #for data
        counter = 0
        for row in f:
            row = row.strip()
            lstrow = row.split(",")
            lstrow = list(map(float,lstrow))

            datacount = len(lstrow)

            lstcsv_wave.append(lstrow[0])
            for loop1 in range(datacount -2):
                lstcsv_chdata[loop1].append(lstrow[loop1+1])
            counter +=1
            lstcsvmonitor.append(lstrow[len(lstrow)-1])

    f.close()
    # data pass for STS_Class
    errorstr =STS.func_STS_Load_ReferenceRawData(lstcsv_chdata,lstcsvmonitor)
    if (errorstr != ""):
        print("IL_STS",errorstr)
        return

    print("IL_STS","Completed")

def func_get_Meas_rawdata():

    # for each range
    for mpm_range in STS.Lst_Range :
        fileName = 'Save Range' + str(mpm_range) +'Rawdata_{}'.format(datetime.today().strftime('%Y%m%d%H%M%S'))
        filepath = r'.\{}.csv'.format(fileName)
        errorstr = STS.func_STS_Save_Rawdata(filepath,mpm_range)
        if errorstr != "":
            print("IL_STS",errorstr)
            return

    print("IL_STS","Completed")

#%% Main
print('Reference process:')

lstref = glob.glob('REF*.csv')
if len(lstref) == 0:
    func_set_sweep_paramter()
    func_get_reference()
    func_get_reference_rawdata()
else:
    ans = ' '
    while ans not in 'nNyY':
        print('Do you want to take Ref data? (Y/N)')
        ans =input()
        if ans in 'yY':
            func_set_sweep_paramter()
            func_get_reference()
            func_get_reference_rawdata()
            break
        elif ans in'nN':
            print('Last sweep parameters:')
            fieldnames = ['Start Wavelength (nm)', 'Stop Wavelength (nm)', 'Step (pm)',
                          'Speed (nm/sec)', 'Power (dBm)', 'Channel list', 'Power range list']
            with open('Last Scan params.csv', encoding="utf8") as f:
                csv_reader = csv.DictReader(f, fieldnames)
                print(list(csv_reader)[1])
            func_set_sweep_paramter()
            func_Load_ReferenceData(lstref[-1])
            break


print('Connect DUT then press any key')
input()
func_get_measure()

root = str(os.path.dirname(__file__))
all_files = glob.glob(root+'\\*.csv')
latest_csv = max(all_files, key=os.path.getctime)
df = pd.read_csv(latest_csv)
for i in df.keys():
    if i=='Wavelength(nm)':
        pass
    else:
        plot(df['Wavelength(nm)'],df[i])
STS.func_STS_Save_Rawdata('Raw.csv',len(lstrange))
