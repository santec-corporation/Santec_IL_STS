
<p align="right"> <a href="https://www.santec.com/jp/" target="_blank" rel="noreferrer"> <img src="https://www.santec.com/dcms_media/image/common_logo01.png" alt="santec" 
  width="250" height="45"/> </a> </p>

<h1 align="left"> Hey there 👋 </h1>

> [!WARNING]
> Critical content.

!The Swept Test System IL PDL Software is designed to function with:
- !TSL-550, TSL-710 and TSL-570 laser series 
- !MPM-210 and MPM210H power meter series 

<h1 align="left"> Santec_IL_STS </h1>
Script for the measurement of the WDL (Wavelength Dependenet Loss) of the STS (Swept Test System).   

<h3 align="left"> List of content </h3>

- #### What is this software about ?
    This is a python software for the measurement of the Wavelength Dependent Loss (WDL)[^3] of the Swept Test System (STS)[^6] in combinational of using a Tunable Laser (TSL)[^1] and a Power Meter (MPM)[^2].

- #### Main features 
    The Santec_IL_STS, is a python script designed to: 
    - Configure the Santec Swept Test System (Light source: TSL series, Power meter: MPM series) 
    -  Run a wavelength scan 
    -  Calculate/save the Wavelength Dependent Loss (WDL) data [Insertion Loss (IL)[^4] data].

- #### Tech Stack
  <p align="left"> <a href="https://www.python.org" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="python" 
  width="40" height="40"/> <br> Python </a> </p>

- #### Dependencies
  - [PyVISA] - is a package used to control all kinds of measurement devices.
  - [Pythonnet] - also known as python.NET, is a package for working with .NET (CLR).
  - [Nidaqmx] - is a package containing an API to interact with NIDAQ driver[^5].
 

- #### Core scripts (for more info on the scripts [click here](https://github.com/rpj17-iNSANE/demo-readme-for-IL_STS/blob/main/README.md#more-details-on-the-core-components))
    - [main.py]: Main script of the project
    - [Get_address.py]: Searches connected instrument via GPIB cable and DAQ board (connected via USB)
    - [sl_instr_class.py]: TSL device class
    - [mpm_instr_class.py]: MPM device class
    - [dev_instr_class.py]: DAQ board device class
    - [sts_process.py]: Swept Test System processing class
    - [error_handing_class.py]: Script returning errors related to InstrumentDLL.dll and STSProcess.dll
    - [file._logging.py]: Handles saving and loading reference data


- #### Precautions before running the script
    > [!IMPORTANT]
    > Crucial information necessary for users to succeed.

    - Make sure that the TSL LD diod is switched ON and warm up during 30min
    - It is recommended to perform a zeroing of the MPM (see MPM user manual)

    ![N|Solid](https://user-images.githubusercontent.com/103238519/187052163-7718c0ee-4fc7-44a3-9086-b7af40b0100a.png) 
    ![N|Solid](https://user-images.githubusercontent.com/103238519/187053147-8edf1644-5ba1-41ed-a1c1-1b900c923ea6.png) 


- #### Running the script
    - Run [main.py] script, and [Get_address.py] file will diplay the list of connected instruments.
    - Select the light source (TSL), the detector (MPM) and the DAQ board.
    - The script will try to find previously saved reference data. If not found, the script will record sweep conditions:
        - Start and stop wavelengths
        - Sweep speed
        - Sweep resolution (step)
        - Output power
        - MPM optical channels to be measured
        - Optical dynamic ranges
    - In case previously recorded data are present, the script will invite to upload the sweep parameters and reference data.
    - The script will invite to connecte each selected optical channel start measuring reference data (Connect the TSL to each optical port directly using a patch cord)
    - Connect the Device Under Test (DUT), enter the number of measurement repetitions then press ENTER to start the measurement
    - The script will display the Insertion Loss and propose to run a second measurement
    If no other measurement is required, the script will save the reference and DUT data and disconnects the instruments

- #### System Requirements
    OS: Windows 10 / 8 / 7.
    National Instruments drivers: NI-488.2 ver. 15 to 21.
    NI-DAQmx ver. 15 to 21.

    Please visit the National Instruments website to download and install the National Instruments drivers:  
    https://www.ni.com/en-us/support/downloads/drivers/download.ni-488-2.html  
    https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html   
    
#### What is STS IL PDL ?
The Swept Test System is the photonic solution by santec Corp. to perform Wavelength 
Dependent Loss characterization of passive optical devices.
It consists of:
- A light source: santec’s Tunable Semiconductor Laser (TSL);
- A power meter: santec’s Multi-port Power Meter (MPM);

#### More details on the core components 
- #### [main.py] :
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


## For more information on Swept Test System [CLICK HERE](https://inst.santec.com/products/componenttesting/sts)


[^1]: [TSL]: Tunable Semiconductor Laser. This is the name of the laser (light source) we are manufacturing.
[^2]: [MPM]: Multiport Power Meter. It measures the light intensity.
[^3]: [WDL]: Wavelength Dependent Loss. For further info, see IL.
[^4]: [IL]: Insertion Loss. It is the amount of light lost in a DUT. This is a relative measurement compared to a   Reference. It is measured in dB.
[^6]: [STS]: Swept Test System.
[^5]: NIDAQ Driver : also known as NI-DAS, is a driver used for Data Acquistion/

[//]: # (Below are the links to the python scripts of the main IL_STS repo)
[main.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/main.py>
[Get_address.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/Get_address.py>
[sl_instr_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/sl_instr_class.py>
[mpm_instr_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/mpm_instr_class.py>
[dev_instr_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/dev_instr_class.pyy>
[sts_process.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/sts_process.py>
[error_handing_class.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/error_handing_class.py>
[file._logging.py]: <https://github.com/santec-corporation/Santec_IL_STS/blob/main/file._logging.py>

[//]: # (Below are the links to the dependencies used in this repo)
[PyVISA]: <https://pyvisa.readthedocs.io/en/latest/index.html>
[Pythonnet]: <https://github.com/pythonnet/pythonnet/wiki/Installation>
[Nidaqmx]: <https://nidaqmx-python.readthedocs.io/en/latest/>
[Pyvera]: <https://pypi.org/project/pyvera/>
