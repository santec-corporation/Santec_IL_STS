# -*- coding: utf-8 -*-

"""
Created on Fri Jan 21 17:17:26 2022

@author: chentir
@organization: santec holdings corp.
"""

# Basic imports
import os
import json
import time

from matplotlib.pyplot import plot, show

# Importing high level santec package and its modules
from santec import TslDevice, MpmDevice, SpuDevice, GetAddress, file_logging, StsProcess

# Initializing get instrument address class
device_address = GetAddress()


def setting_tsl_sweep_params(connected_tsl: TslDevice, previous_param_data):
    """
    Setting sweep parameters. Will ask for:

        start_wavelength:  Starting wavelength (nm)
        stop_wavelength:   Stopping wavelength (nm)
        sweep_step:       Sweep sweep_step (pm)
        sweep_speed:      Sweep sweep_speed (nm/sec).
                    In case of TSL-570, the code will prompt
                    invite to select a sweep_speed from a list.
        power:      Output power (dBm)

    These arguments will be passed to the connected_tsl object.

    Args:
        connected_tsl (TslDevice): Instanced TSL class.
        previous_param_data: If previous sweep process data is selected.

    Returns:
        None
    """

    if previous_param_data is not None:
        start_wavelength = float(previous_param_data["start_wavelength"])
        stop_wavelength = float(previous_param_data["stop_wavelength"])
        sweep_step = float(previous_param_data["sweep_step"])  # sweep_step is .001, but sweep_step is .1. we need the nm value.
        sweep_speed = float(previous_param_data["sweep_speed"])
        power = float(previous_param_data["power"])

        print("Start Wavelength (nm): " + str(start_wavelength))
        print("Stop Wavelength (nm): " + str(stop_wavelength))
        print("Sweep Step (nm): " + str(sweep_step))  # nm, not pm.
        print("Sweep Speed (nm): " + str(sweep_speed))
        print("Output Power (nm): " + str(power))

    else:
        start_wavelength = float(input("\nInput Start Wavelength (nm): "))
        stop_wavelength = float(input("Input Stop Wavelength (nm): "))
        sweep_step = float(input("Input Sweep Step (pm): ")) / 1000

        if connected_tsl.get_550_flag() is True:
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

    # Now that we have our parameters, set them on the TSL.
    # TSL Power setting
    connected_tsl.set_power(power)

    connected_tsl.set_sweep_parameters(start_wavelength, stop_wavelength, sweep_step, sweep_speed)

    return None


def prompt_and_get_previous_param_data(file_last_scan_params):
    """
    If a file for a previous scan exists, then ask the user if it should be used to load ranges, channels,
    previous reference data etc.
    """
    if not os.path.exists(file_last_scan_params):
        return None

    ans = input("\nWould you like to load the most recent parameter settings from {}? [y|n]: ".format(file_last_scan_params))
    if ans not in "Yy":
        return None

    # Load the json data.
    with open(file_last_scan_params) as json_file:
        previous_settings = json.load(json_file)

    return previous_settings


def prompt_and_get_previous_reference_data():
    """
    Ask the user if they want to use the previous reference data (if it exists).
    If so, then load it.
    """

    if not os.path.exists(file_logging.file_last_scan_reference_json):
        return None

    ans = input("\nWould you like to use the most recent reference data from file '{}'? [y|n]: ".format(
        file_logging.file_last_scan_reference_json))

    if ans not in "Yy":
        return None

    # Get the file size. If It's huge, then the load will freeze for a few seconds.
    int_file_size = int(os.path.getsize(file_logging.file_last_scan_reference_json))
    if int_file_size > 1000000:
        str_file_size = str(int(int_file_size / 1000 / 1000)) + " MB"
    else:
        str_file_size = str(int(int_file_size / 1000)) + " KB"

    print("Opening " + str_file_size + " file '" + file_logging.file_last_scan_reference_json + "'...")
    # load the json data.
    with open(file_logging.file_last_scan_reference_json) as json_file:
        previous_reference = json.load(json_file)

    return previous_reference


def main():
    """ Main method of this project """

    tsl = None
    mpm = None
    dev = None
    ilsts = None

    device_address.initialize_instrument_addresses('SME')
    tsl_address = device_address.get_tsl_address()
    mpm_address = device_address.get_mpm_address()
    dev_address = device_address.get_dev_address()
    interface = 'GPIB'

    # Only connect to the devices that the user wants to connect
    if tsl_address is not None:
        tsl = TslDevice(interface, tsl_address)
        tsl.ConnectTSL()
    else:
        raise Exception("There must be a TSL connected")

    if mpm_address is not None:
        mpm = MpmInstrument(interface, mpm_address)
        mpm.connect()

    if dev_address is not None:
        dev = SpuDevice(dev_address)
        dev.ConnectSPU()

    # Set the TSL properties
    previous_param_data = prompt_and_get_previous_param_data(
        file_logging.file_last_scan_params)             # might be empty, if there is no data, or if the user chose to not load it.
    setting_tsl_sweep_params(tsl, previous_param_data)  # previous_param_data might be none

    # If there is an MPM, then create instance of ILSTS
    if mpm.address is not None:
        ilsts = StsProcess(tsl, mpm, dev)

        ilsts.set_selected_channels(previous_param_data)
        ilsts.set_selected_ranges(previous_param_data)

        ilsts.set_data_struct()  # will automatically use either newly-input data, or saved data from the previous_param_data.
        ilsts.set_parameters()  # will automatically use either newly-input data, or saved data from the previous_param_data.

        previous_ref_data_array = None
        if previous_param_data is not None:
            # Determine if we should load reference data
            previous_ref_data_array = prompt_and_get_previous_reference_data()  # trigger, monitor, and log_data. Might be null if the user said no, or the file didn't exist.
        if previous_ref_data_array is not None:
            ilsts._reference_data_array = previous_ref_data_array  # ensures that we always have an array, empty or otherwise.

        if len(ilsts._reference_data_array) == 0:

            print("\nConnect for Reference measurement and press ENTER")
            print("Reference process:")
            ilsts.sts_reference()

        else:
            # Load the reference data from file.
            print("Loading reference data...")
            ilsts.sts_reference_from_saved_file()  # loads from the cached array reference_data_array which is a property of ilsts

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

            # Get and store dut scan data of each channel, each range
            ilsts.get_dut_data()

            ans = input("\nRedo Scan ? (y/n): ")

        # Save IL measurement data
        print("\nSaving measurement data to file " + file_logging.file_measurement_data_results + "...")
        file_logging.save_meas_data(ilsts, file_logging.file_measurement_data_results)

        # Save reference data
        print("Saving reference csv data to file " + file_logging.file_reference_data_results + "...")
        file_logging.save_reference_result_data(ilsts, file_logging.file_reference_data_results)

        # Save dut data
        print("Saving reference csv data to file " + file_logging.file_dut_data_results + "...")
        file_logging.save_dut_result_data(ilsts, file_logging.file_dut_data_results)

        # Save reference data into json file
        print("Saving reference json to file " + file_logging.file_last_scan_reference_json + "...")
        file_logging.save_reference_json_data(ilsts, file_logging.file_last_scan_reference_json)

    # Save the parameters, whether we have an MPM or not. But only if there is no save file, or the user just set new settings.
    if previous_param_data is None:
        print("Saving parameters to file " + file_logging.file_last_scan_params + "...")
        file_logging.sts_save_param_data(tsl, ilsts, file_logging.file_last_scan_params)  # ilsts might be None


if __name__ == "__main__":
    main()
