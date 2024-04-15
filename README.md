
<p align="right"> <a href="https://www.santec.com/jp/" target="_blank" rel="noreferrer"> <img src="https://www.santec.com/dcms_media/image/common_logo01.png" alt="santec" 
  width="250" height="45"/> </a> </p>

> [!NOTE]
> If you have any [issues](https://github.com/santec-corporation/Santec_IL_STS/issues), create a new issue [HERE](https://github.com/santec-corporation/Santec_IL_STS/issues/new). 

<h1 align="left"> Santec_IL_STS </h1>
Script for the measurement of the IL (Insertion Loss) or WDL (Wavelength Dependent Loss) of the STS (Swept Test System).   
<br /> <br />

> [!WARNING]
> The Swept Test System IL PDL Software is designed to function with:
> - _TSL-550, TSL-710 and TSL-570 laser series_
> - _MPM-210 and MPM210H power meter series_


<h2 align="left">Table of contents </h2>

- ### What is this software about?
    This is a Python software for the measurement of the Wavelength Dependent Loss (WDL)[^3] of the Swept Test System (STS)[^6] in combination of using a Tunable Laser (TSL)[^1] and a Power Meter (MPM)[^2].

- ### Main features 
    The Santec_IL_STS is a Python script designed to: 
    - Configure the Santec Swept Test System (Light source: TSL series, Power meter: MPM series) 
    -  Run a wavelength scan 
    -  Calculate/save the Wavelength Dependent Loss (WDL) data [Insertion Loss (IL)[^4] data].

- ### System Requirements
    OS: Windows 10 / 8 / 7.
    National Instruments drivers: NI-488.2 ver. 15 to 21.
    NI-DAQmx ver. 15 to 21.

    Please visit the National Instruments website to download and install the National Instruments drivers:  
    https://www.ni.com/en-us/support/downloads/drivers/download.ni-488-2.html  
    https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html   

- ### Dependencies
  - [PyVISA] - is a package used to control all kinds of measurement devices.
  - [Pythonnet] - also known as python.NET, is a package for working with .NET (CLR).
  - [Nidaqmx] - is a package containing an API to interact with the NIDAQ driver[^5].
 

- ### Core scripts (for more info on the scripts [click here](https://github.com/rpj17-iNSANE/demo-readme-for-IL_STS/blob/main/README.md#more-details-on-the-core-components))
    - [main.py]: Main script of the project
    - [get_address.py]: Searches connected instrument via GPIB cable and DAQ board (connected via USB)
    - [tsl_instrument_class.py]: TSL device class
    - [mpm_instrument_class.py]: MPM device class
    - [daq_device_class.py]: DAQ board device class
    - [sts_process.py]: Swept Test System processing class
    - [error_handing_class.py]: Script returning errors related to InstrumentDLL.dll and STSProcess.dll
    - [file_logging.py]: Handles saving and loading reference data
<br />
  
> [!IMPORTANT]    
> Crucial information below.
> Precautions before running the script
> - Make sure that the TSL LD diode is switched ON and warm up during 30min
> - It is recommended to perform a zeroing of the MPM (see MPM user manual)

![N|Solid](https://user-images.githubusercontent.com/103238519/187052163-7718c0ee-4fc7-44a3-9086-b7af40b0100a.png) <br>
![N|Solid](https://user-images.githubusercontent.com/103238519/187053147-8edf1644-5ba1-41ed-a1c1-1b900c923ea6.png) 
<br>

<details>
<summary><h3>Running the script</h3></summary>
  
- Run [main.py] script, and [Get_address.py] file will display the list of connected instruments.
- Select the light source (TSL), the detector (MPM), and the DAQ board.
- The script will try to find previously saved reference data. If not found, the script will record sweep conditions:
    - Start and stop wavelengths
    - Sweep speed
    - Sweep resolution (step)
    - Output power
    - MPM optical channels to be measured
    - Optical dynamic ranges
- In case previously recorded data are present, the script will invite you to upload the sweep parameters and reference data.
- The script will invite you to connect each selected optical channel to start measuring reference data (Connect the TSL to each optical port directly using a patch cord)
- Connect the Device Under Test (DUT), enter the number of measurement repetitions then press ENTER to start the measurement
- The script will display the Insertion Loss and propose to run a second measurement
If no other measurement is required, the script will save the reference and DUT data and disconnect the instruments
</details>

<details>
<summary><h3>More details on the core components </h3></summary>

1) [main.py]

    This is the main script of the software, the script begins with import statements that bring in various Python modules and 
    custom-defined classes or functions from other files. Here are some of the notable imports:
      - os: The os module is used for interacting with the operating system.
      - json: The json module is used for reading and writing JSON data.
      - matplotlib.pyplot: This module is imported as plot and show, and it's used for creating plots and charts.
      - Several previously defined **modules and classes** are imported, including Initialize_Device_Addresses,         
        Get_Tsl_Address, Get_Mpm_Address, Get_Dev_Address, sts_process, file_logging, TslDevice, MpmDevice, and SpuDevice. These 
        modules/classes contain functions and classes related to data acquisition, instrument control, and data logging.
        
      **Functions**:
        The script defines several functions:
        
      - **setting_tsl_sweep_params(connected_tsl: TslDevice, previous_param_data)**: This function appears to set parameters 
         for a TSL (presumably a tunable laser source) device. It takes an instance of a TslDevice and previous parameter data 
         as arguments.
      
      - **prompt_and_get_previous_param_data(file_last_scan_params)**: This function prompts the user to load previous scan 
          parameters from a file if available.
      
      - **prompt_and_get_previous_reference_data()**: This function prompts the user to use the most recent reference data if 
          available.
      
      - **main()**: The main function, where the main logic of the script is executed. It initializes device addresses, 
          connects to devices (TSL, MPM, and DEV), sets TSL parameters, performs reference 
          measurements, performs sweeps, and saves measurement data and parameters to files.
        
      - **Main Execution**:
          The main() function is called at the end of the script, triggering the main functionality of the code. It initializes 
          and connects to devices, sets parameters, performs measurements, and saves data.
</details>

<details>
<summary><h3>About Santec Swept Test System</h3></summary>

### What is STS IL PDL?
  The Swept Test System is the photonic solution by Santec Corp. to perform Wavelength 
  Dependent Loss characterization of passive optical devices.
  It consists of:
  - A light source: Santec’s Tunable Semiconductor Laser (TSL);
  - A power meter: Santec’s Multi-port Power Meter (MPM);
   

### For more information on the Swept Test System [CLICK HERE](https://inst.santec.com/products/componenttesting/sts)
</details>

[^1]: [TSL]: Tunable Semiconductor Laser. This is the name of the laser (light source) we are manufacturing.
[^2]: [MPM]: Multiport Power Meter. It measures the light intensity.
[^3]: [WDL]: Wavelength Dependent Loss. For further info, see IL.
[^4]: [IL]: Insertion Loss. It is the amount of light lost in a DUT. This is a relative measurement compared to a   Reference. It is measured in dB.
[^6]: [STS]: Swept Test System.
[^5]: NIDAQ Driver: also known as NI-DAS, is a driver used for Data Acquisition/

[//]: # (Below are the links to the Python scripts of the main IL_STS repo)
[main.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/main.py>
[get_address.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/santec/get_address.py>
[tsl_instrument_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/santec/tsl_instrument_class.py>
[mpm_instrument_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/santec/mpm_instrument_class.py>
[daq_device_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/santec/daq_device_class.py>
[sts_process.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/santec/sts_process.py>
[error_handing_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/santec/error_handing_class.py>
[file_logging.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/santec/file_logging.py>

[//]: # (Below are the links to the dependencies used in this repo)
[PyVISA]: <https://pyvisa.readthedocs.io/en/latest/index.html>
[Pythonnet]: <https://github.com/pythonnet/pythonnet/wiki/Installation>
[Nidaqmx]: <https://nidaqmx-python.readthedocs.io/en/latest/>
[Pyvera]: <https://pypi.org/project/pyvera/>
