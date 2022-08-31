# Santec_IL_STS
Python script for Wavelength Dependent Loss measurement using Santec STS
Introduction
============

  Santec IL STS is a python script designed to:
    - Configure the Santec Swept Test System (Light source: TSL series, Power meter: MPM series) 
    - Run a wavelength scan
    - Calculate/save the Wavelength Dependent Loss (WDL) data [Insertion Loss (IL) data].
    
Dependencies
============

  - Pythonnet (https://github.com/pythonnet/pythonnet/wiki/Installation)
  - Pyvisa    (https://pyvisa.readthedocs.io/en/latest/index.html)
  - Nidaqmx   (https://nidaqmx-python.readthedocs.io/en/latest/)
  - DLL folder (contains all essential libraries)

Precautions before running the script
-------------------------------------

  - Make sure all instruments are connected as shown on the following schematic:
  ![image](https://user-images.githubusercontent.com/103238519/187052163-7718c0ee-4fc7-44a3-9086-b7af40b0100a.png)
  ![image](https://user-images.githubusercontent.com/103238519/187053147-8edf1644-5ba1-41ed-a1c1-1b900c923ea6.png)

  - Make sure that the TSL LD diod is switched ON and warm up during 30min
  - It is recommended to perform a zeroing of the MPM (see MPM user manual)

Core components
===============

  - main.py:                Main script of the project
  - Get_address.py:         Searches connected instrument via GPIB cable and DAQ board (connected via USB)
  - tsl_instr_class.py:     TSL device class
  - mpm_instr_class.py:     MPM device class
  - dev_instr_class.py:     DAQ board device class
  - sts_process.py:         Swept Test System processing class
  - error_handing_class.py: Script returning errors related to InstrumentDLL.dll and STSProcess.dll
  - file._logging.py:       Handles saving and loading reference data

Running the script
==================

  - Run main.py script, and Get_address.py file will diplay the list of connected instruments.
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
  - If no other measurement is required, the script will save the reference and DUT data and disconnects the instruments
  
