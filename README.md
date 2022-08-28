# Santec_IL_STS

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
