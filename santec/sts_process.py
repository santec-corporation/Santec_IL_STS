# -*- coding: utf-8 -*-

"""
STS Process Class.

@organization: Santec Holdings Corp.
"""

import re
from array import array

# Importing classes from STSProcess DLL
from Santec.STSProcess import *  # namespace of STSProcess DLL

# Importing instrument classes and sts error strings
from .daq_device_class import SpuDevice
from .mpm_instrument_class import MpmInstrument
from .tsl_instrument_class import TslInstrument
from .error_handing_class import STSProcessError, sts_process_error_strings

# Import program logger
from . import logger


class STSData:
    """ STS Process data class. """
    log_data = None
    il = None
    il_data = None
    il_data_array = None
    wavelength_table = None
    range = None
    ref_data = None
    ref_monitor = None
    merge_data = None
    dut_data = None
    dut_monitor = None
    selected_ranges = None
    all_channels = None
    selected_chans = None
    reference_data_array = []
    dut_data_array = []


class StsProcess(STSData):
    """
    Swept Test System processing class
    """
    def __init__(self,
                 _tsl: TslInstrument,
                 _mpm: MpmInstrument,
                 _spu: SpuDevice):
        logger.info("Initializing STS Process class.")
        self._tsl = _tsl
        self._mpm = _mpm
        self._spu = _spu
        self._ilsts = ILSTS()
        logger.info(f"STS Process details, TslInstrument: {_tsl}, MpmInstrument: {_mpm},"
                    f" SpuDevice: {_spu}")

    @property
    def ilsts(self):
        return self._ilsts

    def set_parameters(self):
        """
        Sets parameters for STS process.
        Args:
            start wave (float): Input the start wavelength value.
            stop_wavelength (float): Input the stop wavelength value.
            sweep_step (float): Input the sweep sweep_step wavelength value.
            sweep_speed (float): Input the sweep sweep_speed value.

        Raises:
            Exception:  When Reference/DUT data couldn't been erased.
                        When Wavelength table couldn't be created
                        Error with rescaling

        Returns
        -------
        TYPE
            DESCRIPTION.
        """
        logger.info("Set STS params")
        # Logging parameters for MPM
        self._mpm.set_logging_parameters(self._tsl.start_wavelength,
                                         self._tsl.stop_wavelength,
                                         self._tsl.sweep_step,
                                         self._tsl.sweep_speed)

        # Logging parameter for SPU(DAQ)
        self._spu.set_logging_parameters(self._tsl.start_wavelength,
                                         self._tsl.stop_wavelength,
                                         self._tsl.sweep_speed,
                                         self._tsl.actual_step)

        # Pass MPM averaging time to SPU Class
        self._spu.AveragingTime = self._mpm.get_averaging_time()

        # STS Process setting Class
        sts_error = self._ilsts.Clear_Measdata()        # Clear measurement data
        if sts_error != 0:
            logger.error("Error while clearing measurement data, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        sts_error = self._ilsts.Clear_Refdata()     # Reference data Clear
        if sts_error != 0:
            logger.error("Error while clearing reference data, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        # Make Wavelength table at sweep
        sts_error = self._ilsts.Make_Sweep_Wavelength_Table(self._tsl.start_wavelength,
                                                            self._tsl.stop_wavelength,
                                                            self._tsl.actual_step)

        if sts_error != 0:
            logger.error("Error while making wavelength table at sweep, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        # Make wavelength table as rescaling
        sts_error = self._ilsts.Make_Target_Wavelength_Table(self._tsl.start_wavelength,
                                                             self._tsl.stop_wavelength,
                                                             self._tsl.sweep_step)

        if sts_error != 0:
            logger.error("Error while making wavelength table as rescaling, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        # Set Rescaling mode for STSProcess class
        sts_error = self._ilsts.Set_Rescaling_Setting(RescalingMode.Freerun_SPU,
                                                      self._mpm.get_averaging_time(),
                                                      True)

        if sts_error != 0:
            logger.error("Error while rescaling setting, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))
        logger.info("STS params set.")

    def set_selected_channels(self, previous_param_data):
        """
        This method to select channels to be measured.
        It offers the user to choose between different ways to select MPM channels.
        For this purpose, method calls the following methods:
        - all_chans
        - even_chans
        - odd_chans
        - special
        - cancel
        """
        logger.info("STS set selected channels for measurement")
        if previous_param_data is not None:
            logger.info("Loading selected channels from previous scan params")
            self.selected_chans = previous_param_data["selected_chans"]  # an array, like [1,3,5]
            allModChans = ""
            for this_mod_channel in self.selected_chans:
                allModChans += ",".join(
                    [str(element) for element in this_mod_channel]) + "; "  # contains numbers so do a conversion
            logger.info("Loaded the selected channels: " + allModChans.strip())
            print("Loaded the selected channels: " + allModChans.strip())
            return None

        self.selected_chans = []
        # Array of arrays: array 0 displays the connected modules
        # The following arrays contain ints of available channels of each module
        self.all_channels = self._mpm.get_modules_and_channels()

        print("\nAvailable modules/channels:")
        logger.info(f"Available modules/channels: {self.all_channels}")
        for i in range(len(self.all_channels)):
            if len(self.all_channels[i]) == 0:
                continue
            print("\r" + "Module {}: Channels {}".format(i, self.all_channels[i]))

        mpm_choices = {'1': self.set_all_channels,
                       '2': self.set_even_channels,
                       '3': self.set_odd_channels,
                       '4': self.set_special_channels
                       }

        user_selection = input("""\nSelect channels to be measured:
                            1. All channels
                            2. Even channels
                            3. Odd channels
                            4. Specific channels
                            """)
        mpm_choices[user_selection]()
        logger.info("STS channel selection done.")

    def set_all_channels(self):
        """ Selects all modules and all channels that are connected to MPM """
        logger.info("Setting all channels")
        for i in range(len(self.all_channels)):
            for j in self.all_channels[i]:
                self.selected_chans.append([i, j])

    def set_even_channels(self):
        """ Selects only even channels on the MPM """
        logger.info("Setting even channels")
        for i in range(len(self.all_channels)):
            for j in self.all_channels[i]:
                if j % 2 == 0:
                    self.selected_chans.append([i, j])

    def set_odd_channels(self):
        """ Selects only odd channels on the MPM """
        logger.info("Setting odd channels")
        for i in range(len(self.all_channels)):
            for j in self.all_channels[i]:
                if j % 2 != 0:
                    self.selected_chans.append([i, j])

    def set_special_channels(self):
        """ Manually enter/select the channels to be measured """
        logger.info("Set special channels")
        selection = input("Input (module,channel) to be tested [ex: (0,1); (1,1)]  ")
        selection = re.findall(r"[\w']+", selection)
        logger.info("Special channel selection: %s", selection)

        i = 0
        while i <= len(selection) - 1:
            self.selected_chans.append([selection[i], selection[i + 1]])
            i += 2
        logger.info("Special channels set.")

    def set_selected_ranges(self, previous_param_data):
        """ Sets the optical dynamic range of the MPM """
        logger.info("STS set selected ranges")
        if previous_param_data is not None:  # Display previously used optical dynamic ranges
            logger.info("Loading selected ranges from previous scan params")
            self.selected_ranges = previous_param_data["selected_ranges"]  # an array, like [1,3,5]
            str_all_ranges = ""
            str_all_ranges += ",".join(
                [str(elem) for elem in self.selected_ranges])  # contains numbers so do a conversion
            logger.info("Using the loaded dynamic ranges: " + str_all_ranges)
            print("Using the loaded dynamic ranges: " + str_all_ranges)

        else:
            self.selected_ranges = []
            print("\nSelect a dynamic range. ex: 1 or 3 or 5")
            print("Available dynamic ranges:")
            i = 1
            self._mpm.get_range()
            for mpm_range in self._mpm.range_data:
                print('{}- {}'.format(i, mpm_range))
                i += 1
            selection = input()
            logger.info("User selected range(s): %s", selection)
            self.selected_ranges = re.findall(r"[\w']+", selection)

        # Convert the string ranges to ints, because that is what the DLL is expecting.
        self.selected_ranges = [int(i) for i in self.selected_ranges]
        logger.info(f"Selected ranges: {self.selected_ranges}")
        return None

    def clear_sts_data_struct(self):
        """ Clear all the sts data struct lists. """
        logger.info("Clear all the sts data struct lists.")
        self.dut_monitor = []
        self.dut_data = []
        self.merge_data = []
        self.ref_monitor = []
        self.ref_data = []
        self.range = []

    def set_sts_data_struct(self):
        """ Create the data structures, which includes the potentially savable reference data """
        logger.info("Set STS data struct")
        self.clear_sts_data_struct()
        counter = 1

        # Configure STSDatastruct for each measurement
        for m_range in self.selected_ranges:
            for ch in self.selected_chans:
                data_st = STSDataStruct()
                data_st.MPMNumber = 0
                data_st.SlotNumber = int(ch[0])  # slot number
                data_st.ChannelNumber = int(ch[1])  # channel number
                data_st.RangeNumber = m_range  # array of MPM ranges
                data_st.SweepCount = counter
                data_st.SOP = 0
                self.dut_data.append(data_st)

                range_index = self.selected_ranges.index(m_range)
                channel_index = self.selected_chans.index(ch)

                # measurement monitor data need only 1 channel for each range.
                if channel_index == 0:
                    self.dut_monitor.append(data_st)
                    self.range.append(m_range)

                # reference data need only 1 range for each ch
                if range_index == 0:
                    self.ref_data.append(data_st)
                    self.ref_monitor.append(data_st)
            counter += 1

        # Configure STSDataStruct for merge
        for ch in self.selected_chans:
            merge_sts = STSDataStructForMerge()
            merge_sts.MPMnumber = 0
            merge_sts.SlotNumber = int(ch[0])  # slot number
            merge_sts.ChannelNumber = int(ch[1])  # channel number
            merge_sts.SOP = 0
            self.merge_data.append(merge_sts)
        logger.info("STS data struct set.")

    def sts_reference(self):
        """ Take reference data for each module/channel selected by the user """
        logger.info("STS reference operation")
        for i in self.ref_data:
            input("\nConnect Slot{} Ch{}, then press ENTER".format(i.SlotNumber, i.ChannelNumber))
            logger.info("STS reference of Slot{} Ch{}".format(i.SlotNumber, i.ChannelNumber))

            # Set MPM range for 1st setting renge
            self._mpm.set_range(self.range[0])

            print("\nScanning...")
            self.sts_sweep_process(0)

            # Get sampling data & Add in STSProcess Class
            self.get_reference_data(i)

            # TSL Sweep stop
            self._tsl.stop_sweep()
        logger.info("STS reference completed.")

    def sts_reference_from_saved_file(self):
        """ Loading reference data from saved file """
        logger.info("Loading STS reference from data file.")
        if self.reference_data_array is None or len(self.reference_data_array) == 0:
            raise Exception("\nThe reference data array cannot be null or empty when loading reference data from files.")

        if len(self.reference_data_array) != len(self.ref_data):
            raise Exception(
                "The length is difference between the saved reference array and the newly-obtained reference array")

        matched_data_structure = None

        for cached_ref_object in self.reference_data_array:
            # self.ref_data is an array of data structures. We need to get that exact data structure because the object is special.
            # Find the matching data structure between ref_data and reference_data_array.
            for i in [
                x for x in self.ref_data
                if x.MPMNumber == cached_ref_object["MPMNumber"]
                and x.SlotNumber == cached_ref_object["SlotNumber"]
                and x.ChannelNumber == cached_ref_object["ChannelNumber"]
            ]:
                matched_data_structure = i

            print('Loading reference data for Slot{} Ch{}...'.format(matched_data_structure.SlotNumber,
                                                                     matched_data_structure.ChannelNumber))

            errorcode = self._ilsts.Add_Ref_MPMData_CH(cached_ref_object["log_data"], matched_data_structure)
            if errorcode != 0:
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            errorcode = self._ilsts.Add_Ref_MonitorData(cached_ref_object["trigger"], cached_ref_object["monitor"],
                                                        matched_data_structure)
            if errorcode != 0:
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            errorcode = self._ilsts.Cal_RefData_Rescaling()     # Rescaling for reference data.
            if errorcode != 0:
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    def sts_measurement(self):
        """ DUT measurement """
        logger.info("STS measurement operation")
        sweep_count = 1
        for mpm_range in self.range:
            error_string = self._mpm.set_range(mpm_range)       # Set MPM Range
            # print(error_string)
            self.sts_sweep_process(sweep_count)     # sweep handling
            error_string = self.sts_get_measurement_data(sweep_count)      # Get DUT data
            # print(error_string)
            sweep_count += 1

        errorcode = self._ilsts.Cal_MeasData_Rescaling()        # Rescaling
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        errorcode = self._ilsts.Cal_IL_Merge(Module_Type.MPM_211)   # Range data merge
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        self._tsl.stop_sweep()      # TSL stop

        #####################################################################

        # This portion of the code just to get wavelengths and IL data at the end of the scan
        # It can be commented out if needed
        self.wavelength_table = []
        self.il_data = []
        self.il_data_array = []

        # Get rescaling wavelength table
        for wav in list(self._ilsts.Get_Target_Wavelength_Table(None)[1]):
            self.wavelength_table.append(wav)
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        for item in self.merge_data:
            # Pull out IL data of after merge
            errorcode, self.il_data = self._ilsts.Get_IL_Merge_Data(None, item)
            if errorcode != 0:
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            self.il_data = array("d", self.il_data)  # List to Array
            self.il_data_array.append(self.il_data)
        self.il = []
        for i in self.il_data_array[0]:
            self.il.append(i)

        #####################################################################

    def sts_sweep_process(self, sweep_count: int):
        """
        Configures TSL/MPM and Daq card to perform the sweep process.

        Args:
            sweep count (int)

        Raises:
            RuntimeError: If TSL/MPM and Daq instruments are not synchronized
            TSL or MPM times out or issues with the Daq card.
            Exception: If there is an issue with TSL sweep process.
        """
        logger.info("STS sweep proces")
        self._tsl.start_sweep()     # TSL Sweep Start
        self._mpm.logging_start()       # MPM Logging Start
        try:
            self._tsl.wait_for_sweep_status(waiting_time=3000, sweep_status=4)      # Waiting for Trigger
            self._spu.sampling_start()
            self._tsl.soft_trigger()
            self._spu.sampling_wait()
            self._mpm.wait_for_log_completion()
            self._mpm.logging_stop(True)
        except RuntimeError as scan_exception:
            self._tsl.stop_sweep(False)
            self._mpm.logging_stop(False)
            raise scan_exception
        except Exception as tsl_exception:
            self._mpm.logging_stop(False)
            raise tsl_exception
        self._tsl.wait_for_sweep_status(waiting_time=5000, sweep_status=1)      # Standby
        logger.info("STS sweep process done.")
        return None

    def get_reference_data(self, data_struct_item):
        """
        Get the reference data by using the parameter data structure, as well as the trigger points, and monitor data.
        Args:
            data_struct_item (Data structure): contains all information of tested module/channel.

        Raises:
            Exception: If power monitor/MPM data were not added to the data structure.
            Exception: Issues with the recalling process.
            Exception: Mismatch between the length of the power monitor data and the length of the MPM data
        """
        logger.info("STS get reference data")
        # Get MPM logging data
        log_data = self._mpm.get_each_channel_log_data(data_struct_item.SlotNumber, data_struct_item.ChannelNumber)

        # Add MPM Logging data for STS Process Class
        self.log_data = array('d', log_data)  # List to Array
        logger.info(f"Reference log details: MPMNumber={data_struct_item.MPMNumber}, SlotNumber={data_struct_item.SlotNumber}"
                    f"ChannelNumber={data_struct_item.ChannelNumber}, RangeNumber={data_struct_item.RangeNumber},"
                    f"Log data length={len(log_data)}")

        errorcode = self._ilsts.Add_Ref_MPMData_CH(log_data, data_struct_item)
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # Get SPU sampling data
        trigger, monitor = self._spu.get_sampling_raw_data()
        logger.info("Trigger length: %d, monitor length: %d", len(trigger), len(monitor))

        # Add Monitor data for STS Process Class
        errorcode = self._ilsts.Add_Ref_MonitorData(trigger, monitor, data_struct_item)
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # Rescaling for reference data.
        # We must rescale before we get the reference data.
        # Otherwise, we end up with way too many monitor and logging points.
        errorcode = self._ilsts.Cal_RefData_Rescaling()
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # After rescaling is done, get the raw reference data.
        errorcode, rescaled_ref_pwr, rescaled_ref_mon = self._ilsts.Get_Ref_RawData(data_struct_item, None, None)

        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        errorcode, wavelength_array = self._ilsts.Get_Target_Wavelength_Table(None)
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        if (len(wavelength_array) == 0 or len(wavelength_array) != len(rescaled_ref_pwr) or len(wavelength_array) != len(
                rescaled_ref_mon)):
            raise Exception(
                "The length of the wavelength array is {}, the length of the reference power array is {}, and the length of the reference monitor is {}. They must all be the same length.".format(
                    len(wavelength_array), len(rescaled_ref_pwr), len(rescaled_ref_mon))
            )

        # Save all desired reference data into the reference array of this StsProcess class.
        ref_object = {
            "MPMNumber": data_struct_item.MPMNumber,
            "SlotNumber": data_struct_item.SlotNumber,
            "ChannelNumber": data_struct_item.ChannelNumber,
            "log_data": list(self.log_data),
            # unscaled log data is required if we want to load the reference data later.
            "trigger": list(array('d', trigger)),
            # motor positions that correspond to wavelengths. required if we want to load the reference data later.
            "monitor": list(array('d', monitor)),
            # unscaled monitor data is required if we want to load the reference data later.
            "rescaled_monitor": list(array('d', rescaled_ref_mon)),  # rescaled monitor data
            "rescaled_wavelength": list(array('d', wavelength_array)),  # all wavelengths, including triggers inbetween.
            "rescaled_reference_power": list(array('d', rescaled_ref_pwr)),  # rescaled reference power
        }

        self.reference_data_array.append(ref_object)
        return None

    def get_wavelength_table(self, data_struct_item: STSDataStruct, trigger_length: int):
        """ Get the list of wavelengths from the most recent scan """
        logger.info("STS get wavelength table")
        datapoint_count = 0
        wavelength_array = []

        # Rescaling for reference data
        errorcode = self._ilsts.Cal_RefData_Rescaling()
        if errorcode != 0:
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        errorcode, ref_pwr, ref_mon = self._ilsts.Get_Ref_RawData(data_struct_item, None, None)  # testing 2...
        errorcode, wavelength_table = self._ilsts.Get_Target_Wavelength_Table(None)
        # errorcode,wavelength_table = self._ilsts.Get_Target_Wavelength_Table(wavelength_array) #TODO; testing.....

        if len(wavelength_table) != trigger_length:
            raise Exception(
                "The length of the wavelength array is {} but the length of the trigger array is {}. They should have been the same. ".format(
                    len(wavelength_table), trigger_length
                ))
        logger.info("Wavelength table length: %d", len(wavelength_table))
        return wavelength_table

    def sts_get_measurement_data(self, sweep_count):
        """
        Gets logged data during DUT measurement.
        Args:
            sweep count (int)

        Raises:
            Exception: if power monitor/MPM data couldn't be added to the data structure
        """
        logger.info("STS get measurement data")
        errorcode = 0
        for item in self.dut_data:
            if item.SweepCount != sweep_count:
                continue

            # Get MPM logging data
            log_data = self._mpm.get_each_channel_log_data(item.SlotNumber, item.ChannelNumber)
            log_data = array("d", log_data)  # List to Array
            logger.info(f"Measurement log details: MPMNumber={item.MPMNumber}, SlotNumber={item.SlotNumber}"
                        f"ChannelNumber={item.ChannelNumber}, RangeNumber={item.RangeNumber},"
                        f"Log data length={len(log_data)}")

            # Add MPM Logging data for STSProcess Class with STSDatastruct
            errorcode = self._ilsts.Add_Meas_MPMData_CH(log_data, item)
            if errorcode != 0:
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # Get monitor data
        trigger, monitor = self._spu.get_sampling_raw_data()

        trigger = array("d", trigger)  # List to Array
        monitor = array("d", monitor)  # list to Array
        logger.info("Trigger length: %d, monitor length: %d", len(trigger), len(monitor))

        # Search place of add in
        for item in self.dut_monitor:
            if item.SweepCount != sweep_count:
                continue
            # Add Monitor data for STSProcess Class with STSDataStruct
            errorcode = self._ilsts.Add_Meas_MonitorData(trigger, monitor, item)
            if errorcode != 0:
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))
        return errorcode

    def get_dut_data(self):
        """
        Gets DUT data.
        """
        logger.info("STS get dut data")
        # After rescaling is done, get the raw dut data
        for data_struct_item in self.dut_data:
            errorcode, rescaled_dut_pwr, rescaled_dut_mon = self._ilsts.Get_Meas_RawData(data_struct_item,
                                                                                         None, None)
            if errorcode != 0:
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            errorcode, wavelength_array = self._ilsts.Get_Target_Wavelength_Table(None)
            if errorcode != 0:
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            if len(wavelength_array) == 0 or len(wavelength_array) != len(rescaled_dut_pwr) or len(
                    wavelength_array) != len(rescaled_dut_mon):
                raise Exception(
                    "The length of the wavelength array is {}, the length of the dut power array is {},"
                    " and the length of the dut monitor is {}. They must all be the same length.".format(
                        len(wavelength_array), len(rescaled_ref_pwr), len(rescaled_ref_mon))
                )

            # print("Channel: {}, Range: {} ".format(data_struct_item.ChannelNumber, data_struct_item.RangeNumber))
            dut_object = {
                "MPMNumber": data_struct_item.MPMNumber,
                "SlotNumber": data_struct_item.SlotNumber,
                "ChannelNumber": data_struct_item.ChannelNumber,
                "RangeNumber": data_struct_item.RangeNumber,
                "rescaled_wavelength": list(array('d', wavelength_array)),
                # all wavelengths, including triggers in between.
                "rescaled_dut_monitor": list(array('d', rescaled_dut_mon)),  # rescaled monitor data
                "rescaled_dut_power": list(array('d', rescaled_dut_pwr)),  # rescaled dut power
            }
            self.dut_data_array.append(dut_object)
            logger.info("STS get dut data done.")

    def disconnect_instruments(self):
        """ Disconnect instrument connections. """
        logger.info("Disconnect instrument connections.")
        try:
            self._tsl.disconnect()
            self._mpm.disconnect()
            self._spu.disconnect()
        except Exception as e:
            logger.error("Error while disconnecting instruments, %s", e)
            raise Exception("Error while disconnecting instruments, %s", e)
        logger.info("Disconnected instrument connections.")
