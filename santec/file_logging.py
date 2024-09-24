# -*- coding: utf-8 -*-

"""
Created on Thu Mar 17 19:51:35 2022

@author: chentir
@organization: santec holdings corp.
"""

# Basic imports
import os
import json
import csv
from array import array
from datetime import datetime

# Importing STS process and instrument classes
import santec.sts_process as sts
from santec.tsl_instrument_class import TslInstrument
from santec.error_handing_class import sts_process_error_strings

# from mpm_instr_class import MpmDevice
# from dev_instr_class import SpuDevice

# Get the current date and time
now = datetime.now()
# Format the date and time as YYYY-MM-DD HH:MM:SS
formatted_datetime = now.strftime("%Y%m%d_%Hhr%Mm%Ssec")

file_last_scan_params = "last_scan_params.json"
file_last_scan_reference_json = "last_scan_reference_data.json"
file_measurement_data_results = f"data_measurement_{formatted_datetime}.csv"
file_reference_data_results = f"data_reference_{formatted_datetime}.csv"
file_dut_data_results = f"data_dut_{formatted_datetime}.csv"


def sts_save_param_data(tsl: TslInstrument, ilsts: sts.StsProcess, str_filename: str):
    rename_old_file(str_filename)

    # Create a pseudo object for our array of STSDataStruct (self.ref_data)
    json_data = {
        "selected_chans": ilsts.selected_chans,
        "selected_ranges": ilsts.selected_ranges,
        "start_wavelength": tsl.start_wavelength,
        "stop_wavelength": tsl.stop_wavelength,
        "sweep_step": tsl.sweep_step,
        "sweep_speed": tsl.sweep_speed,
        "power": tsl.power,                 # only really used on the TSL, and not on the mpm or spu.
        "actual_step": tsl.actual_step,
    }

    if ilsts is not None:
        json_data['selected_chans'] = ilsts.selected_chans
        json_data['selected_ranges'] = ilsts.selected_ranges

    # Save several of our data structure properties.
    with open(str_filename, 'w') as export_file:
        json.dump(json_data, export_file, indent=4)  # an array

    return None


def save_reference_json_data(ilsts: sts.StsProcess, str_filename: str):
    rename_old_file(str_filename)

    with open(str_filename, 'w') as export_file:
        json.dump(
            ilsts._reference_data_array,
            export_file)     # No indents or newlines for this large file. If needed, then look at the CSV instead.

    return None


def rename_old_file(filename: str):
    if os.path.exists(filename):

        # Create a new sub folder, if it doesn't already exist.
        str_previous_folder = "previous"
        if not os.path.exists(r"./" + str_previous_folder):
            os.mkdir(str_previous_folder)

        time_now = datetime.now()
        str_new_filename_and_path = str_previous_folder + "/" + time_now.strftime("%Y%m%d_%H%M%S") + "_" + filename

        try:
            os.rename(filename, str_new_filename_and_path)
        except Exception as ex:
            print("Failed to rename and move file '{}' to '{}: '.".format(filename, str_new_filename_and_path))
            print(str(ex))
            print("Press ENTER to attempt to move the file again.")
            input()
            os.rename(filename, str_new_filename_and_path)

    return None


# Save reference data to CSV for human consumption. Differs from the json data.
def save_reference_result_data(ilsts: sts.StsProcess, str_filename: str):
    rename_old_file(str_filename)

    # Create a CSV file that has columns similar to...
    # Wavelength Slot1Ch1_TSLPower Slot1Ch1_MPMPower Slot1Ch2_TSLPower Slot1Ch2_MPMPower

    ref_data_array = ilsts._reference_data_array

    # Header wavelength is static. There could be any number of slots and channels.
    header = ["Wavelength(nm)"]
    for item in ref_data_array:
        header.append("Slot{}Ch{}_TSLPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"])))
        header.append("Slot{}Ch{}_MPMPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"])))

    all_rows = []  # our row array will contain one array for each line.

    # All the wavelengths are all the same for any slot and channel. So just get the first one.
    wavelength_table = ref_data_array[0]["rescaled_wavelength"]
    # errorcode, wavelength table = ilsts._ilsts.Get_Target_Wavelength_Table(None)

    # For each wavelength, get the data
    i = 0
    for this_wavelength in wavelength_table:
        this_row_array = [this_wavelength]  # wavelength
        for this_refdata in ref_data_array:
            this_row_array.append(str(this_refdata["rescaled_monitor"][i]))  # TSL power
            this_row_array.append(str(this_refdata["rescaled_reference_power"][i]))  # MPM power

        all_rows.append(this_row_array)
        i += 1

    with open(str_filename, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        # write the header
        writer.writerow(header)
        # write all rows
        writer.writerows(all_rows)

    return None


# Save dut data to CSV for human consumption.
def save_dut_result_data(ilsts: sts.StsProcess, str_filename: str):
    rename_old_file(str_filename)

    # Create a CSV file that has columns similar to...
    # Wavelength Slot1Ch1_TSLPower Slot1Ch1_MPMPower Slot1Ch2_TSLPower Slot1Ch2_MPMPower

    dut_data_array = ilsts._dut_data_array

    # Header wavelength is static. There could be any number of slots and channels.
    header = ["Wavelength(nm)"]
    for item in dut_data_array:
        header.append("Slot{}Ch{}R{}_TSLPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"]), str(item["RangeNumber"])))
        header.append("Slot{}Ch{}R{}_MPMPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"]), str(item["RangeNumber"])))

    all_rows = []  # our row array will contain one array for each line.

    # All the wavelengths are all the same for any slot and channel. So just get the first one.
    wavelength_table = dut_data_array[0]["rescaled_wavelength"]
    # errorcode, wavelength table = ilsts._ilsts.Get_Target_Wavelength_Table(None)

    # For each wavelength, get the data
    i = 0
    for this_wavelength in wavelength_table:
        this_row_array = [this_wavelength]  # wavelength
        for this_dutdata in dut_data_array:
            this_row_array.append(str(this_dutdata["rescaled_dut_monitor"][i]))  # TSL DUT power
            this_row_array.append(str(this_dutdata["rescaled_dut_power"][i]))  # MPM DUT power

        all_rows.append(this_row_array)
        i += 1

    with open(str_filename, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        # write the header
        writer.writerow(header)
        # write all rows
        writer.writerows(all_rows)

    return None


# save measurement data
def save_meas_data(ilsts: sts.StsProcess, filepath: str):
    rename_old_file(filepath)
    wavelength_table = []
    ilsts.il_data = []
    il_data_array = []

    # Get rescaling wavelength table
    errorcode, wavelength_table = ilsts._ilsts.Get_Target_Wavelength_Table(None)
    if errorcode != 0:
        raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    for item in ilsts.merge_data:
        # Pull out IL data of after merge
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
        for wave in wavelength_table:
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
    errorcode, wavelength_table = ilsts._ilsts.Get_Target_Wavelength_Table(None)
    if errorcode != 0:
        raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    lst_pow = []
    ref_mon = []
    # Pull out reference raw data of after rescaling
    for item in ilsts.ref_data:
        errorcode, ref_pwr, ref_mon = ilsts._ilsts.Get_Ref_RawData(item, None, None)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        ref_pwr = array("d", ref_pwr)  # List to Array
        ref_mon = array("d", ref_mon)
        lst_pow.append(ref_pwr)

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

        write_test = []
        # for data
        counter = 0
        for wave in wavelength_table:
            write_test.append(wave)
            for item in lst_pow:
                data = item[counter]
                write_test.append(data)

            data = ref_mon[counter]
            write_test.append(data)
            writer.writerow(write_test)
            write_test.clear()
            counter += 1

        f.close()

    return None


# Save measurement Rawdata for specific range
def sts_save_rawdata_unused(ilsts: sts.StsProcess, fpath: str, mpm_range):
    """
    Saves raw data (MPM and power monitor) during DUT measurement
    Args:
        ilsts (StsProcess)
        fpath (str): path and file name
        mpm_range (int): Optical dynamic range of interest
    """
    error_string = ""

    # wavelength table
    errorcode, wavelength_table = ilsts._ilsts.Get_Target_Wavelength_Table(None)
    if errorcode != 0:
        raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    lst_pow = []
    dut_mon = []
    # Data
    for item in ilsts.dut_data:
        print(item)
        if item.RangeNumber != mpm_range:
            print(item.RangeNumber)
            input()
            continue
        # Pull out measurement raw data of after rescaling
        errorcode, dut_pwr, dut_mon = ilsts._ilsts.Get_Meas_RawData(item, None, None)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        dut_pwr = array("d", dut_pwr)  # List to Array
        dut_mon = array("d", dut_mon)  # List to Array
        lst_pow.append(dut_pwr)

    # for header
    header = ["Wavelength(nm)"]

    for item in ilsts.dut_data:
        if item.RangeNumber != mpm_range:
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
        for wave in wavelength_table:
            write_st.append(wave)
            # power data
            for item in lst_pow:
                data = item[counter]
                write_st.append(data)
            # monitor data
            data = dut_mon[counter]
            write_st.append(data)
            writer.writerow(write_st)
            write_st.clear()
            counter += 1
        f.close()

    return error_string


# Load Reference Raw data
def sts_load_ref_data_unused(ilsts, lst_channel_data, lst_monitor):  # TODO: delete this method

    error_string = ""
    counter = 0
    for item in ilsts.ref_data:

        channel_data = lst_channel_data[counter]
        array_channel_data = array("d", channel_data)    # List to Array
        array_monitor = array("d", lst_monitor)

        # Add in Reference Raw data
        errorcode = ilsts._ilsts.Add_Ref_Rawdata(array_channel_data, array_monitor, item)
        if errorcode != 0:
            raise Exception(str(errorcode) + ": " + sts_process_error_strings(errorcode))
        counter += 1
    return error_string
