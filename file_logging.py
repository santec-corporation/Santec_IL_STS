import os
from datetime import datetime
import json
import csv
from array import array
from tsl_instr_class import TslDevice
import sts_process as sts
from error_handing_class import stsprocess_err_str
#from mpm_instr_class import MpmDevice
#from dev_intr_class import SpuDevice

file_last_scan_params = "last_scan_params.json" 
file_last_scan_reference_json = "last_scan_reference_data.json" 
file_measurement_data_results = "data_measurement.csv" 
file_reference_data_results = "data_reference.csv" 


def sts_save_param_data(strfilename: str, tsl: TslDevice, ilsts: sts.StsProcess):
    rename_old_file(strfilename)

    #create a psuedo object for our array of STSDataStruct (self.ref_data)
    jsondata = {
        "selected_chans" : ilsts.selected_chans,
        "selected_ranges" : ilsts.selected_ranges,
        "startwave" :tsl.startwave,
        "stopwave" :tsl.stopwave,
        "step" :tsl.step,
        "speed" :tsl.speed,
        "power" :tsl.power, #only really used on the TSL, and not on the mpm or spu.
        "actual_step" :tsl.actual_step,
    }

    if (ilsts is not None):
        jsondata['selected_chans'] = ilsts.selected_chans
        jsondata['selected_ranges'] = ilsts.selected_ranges

    #save several of our data structure properties. 
    with open(strfilename, 'w') as exportfile:
        json.dump(jsondata, exportfile) #an array
    
    return None

def save_reference_json_data(ilsts: sts.StsProcess, strfilename: str):
    rename_old_file(strfilename)

    with open(strfilename, 'w') as exportfile:
        json.dump(ilsts._reference_data_array, exportfile) #an array
    
    return None


def rename_old_file(filename: str):
    if (os.path.exists(filename)):
        
        #Create a new subfolder, if it doesn't already exist.
        str_previous_folder = "previous"
        if (os.path.exists("/" + str_previous_folder)):
            os.mkdir(str_previous_folder)

        timenow = datetime.now()
        strnewfilenameandpath = str_previous_folder + "/" + timenow.strftime("%Y%m%d_%H%M%S") + "_" + filename
        
        os.rename(filename, strnewfilenameandpath )
    
    return None

# save reference data to CSV for human consumption. Differs from the json data.
def save_reference_result_data(ilsts: sts.StsProcess, strfilename: str):
    rename_old_file(strfilename)

    #Create a CSV file that has columns similar to...
    #Wavelength Slot1Ch1_TSLPower Slot1Ch1_MPMPower Slot1Ch2_TSLPower Slot1Ch2_MPMPower

    ref_data_array = ilsts._reference_data_array 

    #header. wavelength is kinda static. There could be any number of slots and channels.
    header =["Wavelength(nm)"]
    for item in ref_data_array:
        header.append( "Slot{}Ch{}_TSLPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"])) )
        header.append( "Slot{}Ch{}_MPMPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"])) )

    allrows = [] #our row array will contain one array for each line.

    #wavelengthtable = ref_data_array[0]["wavelength"] #all of the wavelengths are all the same for any slot and channel.

    errorcode,wavelengthtable = ilsts._ilsts.Get_Target_Wavelength_Table(None)

    #For each wavelength, get the data
    i = 0
    for thiswavelength in wavelengthtable:
        this_row_array = [ thiswavelength ] #wavelength 
        for thisrefdata in ref_data_array:
            this_row_array.append(str(thisrefdata["monitor"][i])) #TSL power
            this_row_array.append(str(thisrefdata["logdata"][i])) #MPM power

        allrows.append(this_row_array)
        i += 1


    with open(strfilename, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        # write the header
        writer.writerow(header)
        # write all rows
        writer.writerows(allrows)
        
    return None


# save measurement data
def save_meas_data(ilsts: sts.StsProcess, filepath: str):
    wavelengthtable =[]
    ilsts.il_data= []
    il_data_array = []

    #Get rescaling wavelength table
    errorcode,wavelengthtable = ilsts._ilsts.Get_Target_Wavelength_Table(None)
    if (errorcode !=0):
        raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

    for item in ilsts.merge_data:
        #Pull out IL data of aftar merge
        errorcode,ilsts.il_data = ilsts._ilsts.Get_IL_Merge_Data(None,item)
        if (errorcode !=0):
            raise Exception (str(errorcode) + ": " + stsprocess_err_str(errorcode))

        ilsts.il_data = array("f",ilsts.il_data) #List to Array
        il_data_array.append(ilsts.il_data)


    #Open file And write data for .csv
    with open(filepath,"w",newline ="") as f:
        writer = csv.writer(f)

        header =["Wavelength(nm)"]
        writestr =[]

        #header
        for item in ilsts.merge_data:
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
