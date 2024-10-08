
## Detailed README

> [!IMPORTANT]    
> ⚠️ Crucial information below.
> Precautions before running the script
> - Make sure that the TSL LD diode is switched ON and warm up during 30min.
> - It is recommended to perform a zeroing of the MPM before running an STS operation. 


## Core Scripts Overview
- [get_address.py]: Detects connected instruments via GPIB and USB.
- [tsl_instrument_class.py]: Manages TSL instrument functionality.
- [mpm_instrument_class.py]: Handles MPM instrument operations.
- [daq_device_class.py]: Interacts with DAQ devices.
- [sts_process.py]: Processes data from the Swept Test System.
- [error_handling_class.py]: Manages errors related to Instrument DLL and STS Process DLL.
- [file_logging.py]: Records operational data for the Swept Test System.

---

## How to Run the Script

Verify the instrument connections before running the script, <br>
- [Front Connections](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/connection_front.png)
- [Rear Connections](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/connection_rear.png)

#### 1. Initialize the System
Run the `main.py` script to launch the measurement interface. 

#### 2. Instrument Selection
A list of connected instruments will be displayed.\
Select the following:\
Light Source,\
Power Meter,\
DAQ Board.

#### 3. Reference Data Configuration
- The program will search for previously saved reference data.
- If no data is found, input the following sweep parameters: \
Start and stop wavelengths,\
Sweep speed,\
Sweep resolution (step size),\
Output power,\
MPM optical channels to measure,\
Optical dynamic ranges.

#### 4. Utilizing Existing Data
If recorded reference data is available, the script will prompt you to upload the sweep parameters and associated data.

#### 5. Optical Channel Connection
- Follow the prompts to connect each selected optical channel.
- Begin measuring reference data.

**Note**: Use a patch cord to connect the TSL directly to each optical port.

#### 6. Connecting the Device Under Test (DUT)
- Connect the DUT.
- Enter the number of measurement repetitions.
- Press ENTER to start the measurement.

#### 7. Measurement Results
- The script will display the Insertion Loss results.
- You can choose to conduct a second measurement if needed.
- If no further measurements are required, the script will save the reference and DUT data.
- The instruments will be disconnected automatically.

---

## Sweep Configuration Parameters

File type: [JSON](https://www.json.org/json-en.html) <br>
File name: **last_scan_params.json**

### Example:
  ```json
  {
      "selected_chans": [
          ["0", "1"],
          ["0", "2"]
      ],
      "selected_ranges": [
          1,
          2
      ],
      "start_wavelength": 1500.0,
      "stop_wavelength": 1600.0,
      "sweep_step": 0.1,
      "sweep_speed": 50.0,
      "power": 0.0,
      "actual_step": 0.1
  }
  ```
### Customization Tips
**Channel Selection:** Adjust the selected_chans array to include any channels necessary for your analysis.
Each combination allows you to compare different configurations.

**Range Selection:** Modify selected_ranges to select specific ranges, according to your experimental design.
Ensure the indices match your available range options.

**Wavelength Settings:**
Change start_wavelength and stop_wavelength to define the spectral range of interest for your measurements.

**Sweep Parameters:**

**Step Size:** Tweak sweep_step for finer or coarser sampling; smaller steps yield more detailed data.
**Speed:** Adjust sweep_speed based on how quickly you need results versus the precision required.
**Power Adjustment:**
Set the power parameter based on your equipment's requirements and desired sensitivity during measurements.

**Actual Step:** The step size between two TSL triggers. This value is obtained after setting the TSL sweep parameters, refer to `set_sweep_parameters` of the `tsl_instrument_class`.

---

## About Santec Swept Test System

### What is STS IL PDL?
  The Swept Test System is the photonic solution by Santec Corporation,
  to perform Wavelength-Dependent Loss characterization of passive optical devices.
  It consists of:
  - A light source: Santec’s Tunable Semiconductor Laser, also known as TSL
  - A power meter: Santec’s Multi-port Power Meter, also known as MPM
   

### For more information on the Swept Test System [CLICK HERE](https://inst.santec.com/products/componenttesting/sts)


[^1]: [TSL]: Tunable Semiconductor Laser. This is the name of the laser (light source) we are manufacturing.
[^2]: [MPM]: Multiport Power Meter. It measures the light intensity.
[^3]: [WDL]: Wavelength-Dependent Loss. For further info, see IL.
[^4]: [IL]: Insertion Loss. It is the amount of light lost in a DUT. This is a relative measurement compared to a   Reference. It is measured in dB.
[^6]: [STS]: Swept Test System.
[^5]: NIDAQ Driver: also known as NI-DAS, is a driver used for Data Acquisition/

[//]: # (Below are the links to the Python scripts of the main IL_STS repo)
[main.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/stable/main.py>
[get_address.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/stable/santec/get_address.py>
[tsl_instrument_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/stable/santec/tsl_instrument_class.py>
[mpm_instrument_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/stable/santec/mpm_instrument_class.py>
[daq_device_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/stable/santec/daq_device_class.py>
[sts_process.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/stable/santec/sts_process.py>
[error_handling_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/stable/santec/error_handling_class.py>
[file_logging.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/stable/santec/file_logging.py>
