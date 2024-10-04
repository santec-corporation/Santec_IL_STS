# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Santec IL STS
"""

import os
import json
import time
from matplotlib.pyplot import plot, show

# Importing modules from the santec directory
from santec import (TslInstrument, MpmInstrument, SpuDevice,
                    GetAddress, file_logging, StsProcess)


def setting_tsl_sweep_params(connected_tsl: TslInstrument, previous_param_data: dict) -> None:
    """
    Set sweep parameters for the TSL instrument.

    Parameters:
        connected_tsl (TslInstrument): Instance of the TSL class.
        previous_param_data (dict): Previous sweep process data, if available.

    Returns:
        None
    """
    if previous_param_data is not None:
        start_wavelength = float(previous_param_data["start_wavelength"])
        stop_wavelength = float(previous_param_data["stop_wavelength"])
        sweep_step = float(previous_param_data["sweep_step"])
        sweep_speed = float(previous_param_data["sweep_speed"])
        power = float(previous_param_data["power"])

        print("Start Wavelength (nm): " + str(start_wavelength))
        print("Stop Wavelength (nm): " + str(stop_wavelength))
        print("Sweep Step (nm): " + str(sweep_step))  # nm, not pm.
        print("Sweep Speed (nm): " + str(sweep_speed))
        print("Output Power (dBm): " + str(power))
    else:
        start_wavelength = float(input("\nInput Start Wavelength (nm): "))
        stop_wavelength = float(input("Input Stop Wavelength (nm): "))
        sweep_step = float(input("Input Sweep Step (pm): ")) / 1000

        if connected_tsl.get_tsl_type_flag() is True:
            sweep_speed = float(input("Input Sweep Speed (nm/sec): "))
        else:
            num = 1
            print('\nSpeed table:')
            for i in connected_tsl.get_sweep_speed_table():
                print(str(num) + "- " + str(i))
                num += 1
            speed = input("Select a sweep speed (nm/sec): ")
            sweep_speed = connected_tsl.get_sweep_speed_table()[int(speed) - 1]

        power = float(input("Input Output Power (dBm): "))
        while power > 10:
            print("Invalid value of Output Power ( <=10 dBm )")
            power = float(input("Input Output Power (dBm): "))

    # Set TSL parameters
    connected_tsl.set_power(power)
    connected_tsl.set_sweep_parameters(start_wavelength, stop_wavelength, sweep_step, sweep_speed)


def prompt_and_get_previous_param_data(file_last_scan_params: str) -> dict | None:
    """
    Prompt user to load previous parameter settings if available.

    Parameters:
        file_last_scan_params (str): Path to the file containing last scan parameters.

    Returns:
        dict: Previous settings loaded from the file, or None if not available.
    """
    if not os.path.exists(file_last_scan_params):
        return None

    ans = input("\nWould you like to load the most recent parameter settings from {}? [y|n]: "
                .format(file_last_scan_params))
    if ans not in "Yy":
        return None

    # Load the json data.
    with open(file_last_scan_params, encoding='utf-8') as json_file:
        previous_settings = json.load(json_file)

    return previous_settings


def prompt_and_get_previous_reference_data() -> dict | None:
    """
    Ask user if they want to use the previous reference data if it exists.

    Returns:
        dict: Previous reference data loaded from the file, or None if not available.
    """
    if not os.path.exists(file_logging.FILE_LAST_SCAN_REFERENCE_JSON):
        return None

    ans = input("\nWould you like to use the most recent reference data from file '{}'? [y|n]: "
                .format(file_logging.FILE_LAST_SCAN_REFERENCE_JSON))

    if ans not in "Yy":
        return None

    # Get the file size.
    int_file_size = int(os.path.getsize(file_logging.FILE_LAST_SCAN_REFERENCE_JSON))
    str_file_size = f"{int_file_size / 1000000:.2f} MB" if int_file_size > 1000000 else f"{int_file_size / 1000:.2f} KB"

    print("Opening " + str_file_size + " file '" + file_logging.FILE_LAST_SCAN_REFERENCE_JSON + "'...")
    # Load the json data.
    with open(file_logging.FILE_LAST_SCAN_REFERENCE_JSON, encoding='utf-8') as json_file:
        previous_reference = json.load(json_file)
    return previous_reference


def save_all_data(tsl: TslInstrument, previous_param_data: dict, ilsts: StsProcess) -> None:
    """
    Save measurement and reference data to files.

    Parameters:
        tsl (TslInstrument): Instance of the TSL class.
        previous_param_data (dict): Previous sweep process data, if available.
        ilsts (StsProcess): Instance of the ILSTS class.

    Returns:
        None
    """
    if previous_param_data is None:
        print("Saving parameters to file " + file_logging.FILE_LAST_SCAN_PARAMS + "...")
        file_logging.save_sts_parameter_data(tsl, ilsts, file_logging.FILE_LAST_SCAN_PARAMS)

    print("\nSaving measurement data to file " + file_logging.FILE_MEASUREMENT_DATA_RESULTS + "...")
    file_logging.save_measurement_data(ilsts, file_logging.FILE_MEASUREMENT_DATA_RESULTS)

    print("Saving reference csv data to file " + file_logging.FILE_REFERENCE_DATA_RESULTS + "...")
    file_logging.save_reference_result_data(ilsts, file_logging.FILE_REFERENCE_DATA_RESULTS)

    print("Saving DUT data to file " + file_logging.FILE_DUT_DATA_RESULTS + "...")
    file_logging.save_dut_result_data(ilsts, file_logging.FILE_DUT_DATA_RESULTS)

    print("Saving reference json to file " + file_logging.FILE_LAST_SCAN_REFERENCE_JSON + "...")
    file_logging.save_reference_data_json(ilsts, file_logging.FILE_LAST_SCAN_REFERENCE_JSON)


def main() -> None:
    """
    Main method of the project.
    Connects to devices, sets parameters, and performs measurements.

    Returns:
        None
    """
    mpm = None
    dev = None

    device_address = GetAddress()
    device_address.initialize_instrument_addresses()
    tsl_address = device_address.get_tsl_address()
    mpm_address = device_address.get_mpm_address()
    dev_address = device_address.get_dev_address()
    interface = 'GPIB'

    # Connect to the devices
    if tsl_address is not None:
        tsl = TslInstrument(interface, tsl_address)
        tsl.connect()
    else:
        raise Exception("There must be a TSL connected")

    if mpm_address is not None:
        mpm = MpmInstrument(interface, mpm_address)
        mpm.connect()

    if dev_address is not None:
        dev = SpuDevice(dev_address)
        dev.connect()

    # Set the TSL properties
    previous_param_data = prompt_and_get_previous_param_data(
        file_logging.FILE_LAST_SCAN_PARAMS)
    setting_tsl_sweep_params(tsl, previous_param_data)

    # If there is an MPM, create an instance of ILSTS
    if mpm is not None:
        ilsts = StsProcess(tsl, mpm, dev)
        ilsts.set_selected_channels(previous_param_data)
        ilsts.set_selected_ranges(previous_param_data)

        ilsts.set_sts_data_struct()
        ilsts.set_parameters()

        previous_ref_data_array = None
        if previous_param_data is not None:
            previous_ref_data_array = prompt_and_get_previous_reference_data()
        if previous_ref_data_array is not None:
            ilsts.reference_data_array = previous_ref_data_array

        if len(ilsts.reference_data_array) == 0:
            print("\nConnect for Reference measurement and press ENTER")
            print("Reference process:")
            ilsts.sts_reference()
        else:
            print("Loading reference data...")
            ilsts.sts_reference_from_saved_file()

        # Perform the sweeps
        ans = "y"
        while ans in "yY":
            print("\nDUT measurement")
            reps = ""
            while not reps.isnumeric():
                reps = input("Input repeat count, and connect the DUT and press ENTER: ")
                if not reps.isnumeric():
                    print("Invalid repeat count, enter a number.\n")

            for _ in range(int(reps)):
                print("\nScan {} of {}...".format(str(_ + 1), reps))
                ilsts.sts_measurement()
                user_map_display = input("\nDo you want to view the graph ?? (y/n): ")
                if user_map_display == "y":
                    plot(ilsts.wavelength_table, ilsts.il)
                    show()
                time.sleep(2)

            # Get and store DUT scan data
            ilsts.get_dut_data()

            ans = input("\nRedo Scan ? (y/n): ")
        save_all_data(tsl, previous_param_data, ilsts)


if __name__ == "__main__":
    main()
