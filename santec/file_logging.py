# -*- coding: utf-8 -*-

"""
Created on Thu Mar 17 19:51:35 2022

@author: chentir
@organization: santec holdings corp.
"""

import os
import json
import csv
from array import array
from datetime import datetime

import santec.sts_process as sts
from santec.tsl_instr_class import TslDevice
from santec.error_handing_class import sts_process_error_strings

# from mpm_instr_class import MpmDevice
# from dev_instr_class import SpuDevice

file_last_scan_params = "last_scan_params.json"
file_last_scan_reference_json = "last_scan_reference_data.json"
file_measurement_data_results = "data_measurement.csv"
file_reference_data_results = "data_reference.csv"


def sts_save_param_data(tsl: TslDevice, ilsts: sts.StsProcess, strfilename: str):
    rename_old_file(strfilename)

    # create a pseudo object for our array of STSDataStruct (self.ref_data)
    jsondata = {
        "selected_chans": ilsts.selected_chans,
        "selected_ranges": ilsts.selected_ranges,
        "startwave": tsl.startwave,
        "stopwave": tsl.stopwave,
        "step": tsl.step,
        "speed": tsl.speed,
        "power": tsl.power,  # only really used on the TSL, and not on the mpm or spu.
        "actual_step": tsl.actual_step,
    }

    if ilsts is not None:
        jsondata['selected_chans'] = ilsts.selected_chans
        jsondata['selected_ranges'] = ilsts.selected_ranges

    # save several of our data structure properties.
    with open(strfilename, 'w') as exportfile:
        json.dump(jsondata, exportfile, indent=4)  # an array

    return None


def save_reference_json_data(ilsts: sts.StsProcess, strfilename: str):
    rename_old_file(strfilename)

    with open(strfilename, 'w') as exportfile:
        json.dump(ilsts._reference_data_array,
                  exportfile)  # No indents or newlines for this large file. If needed, then look at the CSV instead.

    return None


def rename_old_file(filename: str):
    if (os.path.exists(filename) == True):

        # Create a new subfolder, if it doesn't already exist.
        str_previous_folder = "previous"
        if os.path.exists(r"./" + str_previous_folder) == False:
            os.mkdir(str_previous_folder)

        timenow = datetime.now()
        strnewfilenameandpath = str_previous_folder + "/" + timenow.strftime("%Y%m%d_%H%M%S") + "_" + filename

        try:
            os.rename(filename, strnewfilenameandpath)
        except Exception as ex:
            print("Failed to rename and move file '{}' to '{}: '.".format(filename, strnewfilenameandpath))
            print(str(ex))
            print("Press ENTER to attempt to move the file again.")
            input()
            os.rename(filename, strnewfilenameandpath)

    return None


# save reference data to CSV for human consumption. Differs from the json data.
def save_reference_result_data(ilsts: sts.StsProcess, strfilename: str):
    rename_old_file(strfilename)

    # Create a CSV file that has columns similar to...
    # Wavelength Slot1Ch1_TSLPower Slot1Ch1_MPMPower Slot1Ch2_TSLPower Slot1Ch2_MPMPower

    ref_data_array = ilsts._reference_data_array

    # header. wavelength is kinda static. There could be any number of slots and channels.
    header = ["Wavelength(nm)"]
    for item in ref_data_array:
        header.append("Slot{}Ch{}_TSLPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"])))
        header.append("Slot{}Ch{}_MPMPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"])))

    allrows = []  # our row array will contain one array for each line.

    wavelengthtable = ref_data_array[0][
        "rescaled_wavelength"]  # all the wavelengths are all the same for any slot and channel. So just get the first one.
    # errorcode,wavelengthtable = ilsts._ilsts.Get_Target_Wavelength_Table(None)

    # For each wavelength, get the data
    i = 0
    for thiswavelength in wavelengthtable:
        this_row_array = [thiswavelength]  # wavelength
        for thisrefdata in ref_data_array:
            this_row_array.append(str(thisrefdata["rescaled_monitor"][i]))  # TSL power
            this_row_array.append(str(thisrefdata["rescaled_referencepower"][i]))  # MPM power

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
    rename_old_file(filepath)
    wavelengthtable = []
    ilsts.il_data = []
    il_data_array = []

    # Get rescaling wavelength table
    errorcode, wavelengthtable = ilsts._ilsts.Get_Target_Wavelength_Table(None)
    if errorcode != 0:
        raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    for item in ilsts.merge_data:
        # Pull out IL data of aftar merge
        errorcode, ilsts.il_data = ilsts._ilsts.Get_IL_Merge_Data(None, item)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        ilsts.il_data = array("d", ilsts.il_data)  # List to Array
        il_data_array.append(ilsts.il_data)

    # Open file And write data for .csv
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)

        header = ["Wavelength(nm)"]
        writestr = []

        # header
        for item in ilsts.merge_data:
            ch = "Slot" + str(item.SlotNumber) + "Ch" + str(item.ChannelNumber)
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
            counter += 1

    f.close()
    return None


# Save Reference raw data
def sts_save_ref_rawdata_unused(ilsts: sts.StsProcess, filepath: str):  # TODO: delete this method
    rename_old_file(filepath)
    # wavelength data
    errorcode, wavetable = ilsts._ilsts.Get_Target_Wavelength_Table(None)
    if errorcode != 0:
        raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    lstpow = []
    # Pull out reference raw data of after rescaling
    for item in ilsts.ref_data:
        errorcode, ref_pwr, ref_mon = ilsts._ilsts.Get_Ref_RawData(item, None, None)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        ref_pwr = array("d", ref_pwr)  # List to Array
        ref_mon = array("d", ref_mon)
        lstpow.append(ref_pwr)

    # File open and write data  for .csv
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        header = ["Wavelength(nm)"]

        # for header
        for item in ilsts.ref_data:
            header_str = "Slot" + str(item.SlotNumber) + "Ch" + str(item.ChannelNumber)
            header.append(header_str)
        header_str = "Monitor"
        header.append(header_str)
        writer.writerow(header)

        writest = []
        # for data
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
            counter += 1

        f.close()

    return None


# Save measurement Rawdata for specific range
def sts_save_rawdata_unused(ilsts: sts.StsProcess, fpath: str, mpmrange):
    """
    Saves raw data (MPM and power monitor) during DUT measurement
    Args:
        ilsts (StsProcess)
        fpath (str): path and file name
        mpmrange (int): Optical dynamic range of interest
    """
    errorstr = ""

    # wavelength table
    errorcode, wavetable = ilsts._ilsts.Get_Target_Wavelength_Table(None)
    if (errorcode != 0):
        raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    lstpow = []
    # data
    for item in ilsts.dut_data:
        print(item)
        if item.RangeNumber != mpmrange:
            print(item.RangeNumber)
            input()
            continue
        # Pull out measurement raw data of aftar rescaling
        errorcode, dut_pwr, dut_mon = ilsts._ilsts.Get_Meas_RawData(item, None, None)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        dut_pwr = array("d", dut_pwr)  # List to Array
        dut_mon = array("d", dut_mon)  # List to Array
        lstpow.append(dut_pwr)

    # for hedder
    header = ["Wavelength(nm)"]

    for item in ilsts.dut_data:
        if item.RangeNumber != mpmrange:
            continue
        header_str = "Slot" + str(item.SlotNumber) + "Ch" + str(item.ChannelNumber)
        header.append(header_str)

    header_str = "Monitor"
    header.append(header_str)

    # Open file and write data for .csv
    with open(fpath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # for data
        write_st = []
        counter = 0
        for wave in wavetable:
            write_st.append(wave)
            # power data
            for item in lstpow:
                data = item[counter]
                write_st.append(data)
            # monitor data
            data = dut_mon[counter]
            write_st.append(data)
            writer.writerow(write_st)
            write_st.clear()
            counter += 1
        f.close()

    return errorstr


# Load Reference Raw data
def sts_load_ref_data_unused(ilsts, lstchdata, lstmonitor):  # TODO: delete this method

    errorstr = ""
    counter = 0
    for item in ilsts.ref_data:

        chdata = lstchdata[counter]
        arychdata = array("d", chdata)  # List to Array
        arymonitor = array("d", lstmonitor)

        # Add in Reference Raw data
        errorcode = ilsts._ilsts.Add_Ref_Rawdata(arychdata, arymonitor, item)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))
        counter += 1
    return errorstr
