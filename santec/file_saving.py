# -*- coding: utf-8 -*-

"""
File Logging.
Save STS parameter data.
Save STS loss data.

@organization: Santec Holdings Corp.
"""

import os
import json
import csv
from array import array
from datetime import datetime

# Importing STS process and instrument classes
from .sts_process import StsProcess
from .tsl_instrument_class import TslInstrument
from .error_handling_class import sts_process_error_strings

now = datetime.now()        # Get the current date and time
formatted_datetime = now.strftime("%Y%m%d_%Hhr%Mm%Ssec")        # Format the date and time as YYYY-MM-DD HH:MM:SS

FILE_LAST_SCAN_PARAMS = "last_scan_params.json"
FILE_LAST_SCAN_REFERENCE_DATA = "last_scan_reference_data.dat"
FILE_MEASUREMENT_DATA_RESULTS = f"data_measurement_{formatted_datetime}.csv"
FILE_REFERENCE_DATA_RESULTS = f"data_reference_{formatted_datetime}.csv"
FILE_DUT_DATA_RESULTS = f"data_dut_{formatted_datetime}.csv"


def save_sts_parameter_data(tsl: TslInstrument,
                            ilsts: StsProcess,
                            str_filename: str):
    """ Save STS parameter data. """
    check_and_rename_old_file(str_filename)

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
    with open(str_filename, 'w', encoding='utf8') as export_file:
        json.dump(json_data, export_file, indent=4)


def save_reference_data(ilsts: StsProcess, str_filename: str):
    """ Save reference data as a data file. """
    check_and_rename_old_file(str_filename)
    data = str(ilsts.reference_data_array).replace("'", '"')
    with open(str_filename, 'w', encoding='utf-8') as file:
        file.write(data)


def check_and_rename_old_file(filename: str):
    """ Check and rename old file. """
    if os.path.exists(filename):

        # Create a new subfolder if it doesn't already exist.
        str_previous_folder = "previous"
        if not os.path.exists(r"./" + str_previous_folder):
            os.mkdir(str_previous_folder)

        time_now = datetime.now()
        str_new_filename_and_path = str_previous_folder + "/" + time_now.strftime("%Y%m%d_%H%M%S") + "_" + filename

        try:
            os.rename(filename, str_new_filename_and_path)
        except Exception as ex:
            print("Failed to rename and move file %s to %s.", filename, str_new_filename_and_path)
            print(str(ex))
            print("Press ENTER to attempt to move the file again.")
            input()
            os.rename(filename, str_new_filename_and_path)


def save_reference_result_data(ilsts: StsProcess,
                               str_filename: str):
    """ Save reference data to CSV for human consumption. Differs from the json data. """
    check_and_rename_old_file(str_filename)

    # Create a CSV file that has columns similar to...
    # Wavelength Slot1Ch1_TSLPower Slot1Ch1_MPMPower Slot1Ch2_TSLPower Slot1Ch2_MPMPower

    ref_data_array = ilsts.reference_data_array

    # Header wavelength is static. There could be any number of slots and channels.
    header = ["Wavelength(nm)"]
    for item in ref_data_array:
        header.append("Slot{}Ch{}_TSLPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"])))
        header.append("Slot{}Ch{}_MPMPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"])))

    all_rows = []  # our row array will contain one array for each line.

    # All the wavelengths are all the same for any slot and channel. So just get the first one.
    wavelength_table = ref_data_array[0]["rescaled_wavelength"]
    # errorcode, wavelength table = ilsts.ilsts.Get_Target_Wavelength_Table(None)

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


def save_dut_result_data(ilsts: StsProcess,
                         str_filename: str):
    """ Save dut data to CSV for human consumption. """
    check_and_rename_old_file(str_filename)

    # Create a CSV file that has columns similar to...
    # Wavelength Slot1Ch1_TSLPower Slot1Ch1_MPMPower Slot1Ch2_TSLPower Slot1Ch2_MPMPower

    dut_data_array = ilsts.dut_data_array

    # Header wavelength is static. There could be any number of slots and channels.
    header = ["Wavelength(nm)"]
    for item in dut_data_array:
        header.append("Slot{}Ch{}R{}_TSLPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"]), str(item["RangeNumber"])))
        header.append("Slot{}Ch{}R{}_MPMPower".format(str(item["SlotNumber"]), str(item["ChannelNumber"]), str(item["RangeNumber"])))

    all_rows = []  # our row array will contain one array for each line.

    # All the wavelengths are all the same for any slot and channel. So just get the first one.
    wavelength_table = dut_data_array[0]["rescaled_wavelength"]
    # errorcode, wavelength table = ilsts.ilsts.Get_Target_Wavelength_Table(None)

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


def save_measurement_data(ilsts: StsProcess,
                          filepath: str):
    """ Save measurement data. """
    check_and_rename_old_file(filepath)
    wavelength_table = []
    ilsts.il_data = []
    il_data_array = []

    # Get rescaling wavelength table
    errorcode, wavelength_table = ilsts.ilsts.Get_Target_Wavelength_Table(None)
    if errorcode != 0:
        raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    for item in ilsts.merge_data:
        # Pull out IL data of after merge
        errorcode, ilsts.il_data = ilsts.ilsts.Get_IL_Merge_Data(None, item)
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        ilsts.il_data = array("d", ilsts.il_data)  # List to Array
        il_data_array.append(ilsts.il_data)

    # Open file And write data for .csv
    with open(filepath, "w", newline="", encoding='utf-8') as f:
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


def sts_save_rawdata_unused(ilsts: StsProcess,
                            fpath: str,
                            mpm_range):
    """
    Save measurement Rawdata for specific range.
    Saves raw data (MPM and power monitor) during DUT measurement
    Args:
        ilsts (StsProcess)
        fpath (str): path and file name
        mpm_range (int): Optical dynamic range of interest
    """
    errorcode, wavelength_table = ilsts.ilsts.Get_Target_Wavelength_Table(None)
    if errorcode != 0:
        raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    lst_pow = []
    dut_mon = []
    for item in ilsts.dut_data:
        print(item)
        if item.RangeNumber != mpm_range:
            print(item.RangeNumber)
            input()
            continue
        # Pull out measurement raw data of after rescaling
        errorcode, dut_pwr, dut_mon = ilsts.ilsts.Get_Meas_RawData(item, None, None)
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

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
    with open(fpath, "w", newline="", encoding='utf-8') as f:
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
