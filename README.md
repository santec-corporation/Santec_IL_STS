
<p align="right"> <a href="https://www.santec.com/jp/" target="_blank" rel="noreferrer"> <img src="https://www.santec.com/dcms_media/image/common_logo01.png" alt="santec" 
  width="250" height="45"/> </a> </p>

<h1 align="left"> Santec IL STS </h1>

Program to measure Insertion Loss using the Santec's Swept Test System. <br> <br>

## Overview

The **Santec_IL_STS** is designed to configure and operate the Santec Swept Test System (STS), allowing users to perform Wavelength-Dependent Loss (WDL) characterization of passive optical devices. This tool facilitates the measurement of Insertion Loss (IL) using Santec's TSL and MPM series instruments.

---

## Key Features

- Configure the Santec Swept Test System (Light source: TSL series, Power meter: MPM series, DAQ board)
- Perform wavelength scans
- Record reference and measurement scan power
- Calculate and save Insertion Loss (IL) data
- Re-use previous scan parameters and reference data

---

## Getting Started

### System Requirements

- **OS:** Windows 10 / 8 / 7
- **Python:** Any version (Latest version 3.12 recommended)
- **Drivers:** 
  - NI-488.2: [Version 20](https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#345631)
  - NI-DAQmx: [Version 20](https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#346240)
  - NI-VISA: [Version 20](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html#346210)

### Dependencies

- [pythonnet](https://pythonnet.github.io/) : Also known as `clr`, for .NET interoperability
- [pyvisa](https://pyvisa.readthedocs.io/en/latest/index.html) : For controlling measurement devices
- [nidaqmx](https://nidaqmx-python.readthedocs.io/en/latest/) : API for NIDAQ driver interaction

### Supported Instruments
The Swept Test System IL PDL Software is designed to function with:
- _TSL-550, TSL-710 and TSL-570 laser series_
- _MPM-210 and MPM210H power meter series_

---

## Installation

### Cloning the Repository

To clone the repository, use the following command in your terminal:

```bash
git clone https://github.com/santec-corporation/Santec_IL_STS.git
```


### Downloading the Latest Release,
You can download the latest release directly from the [Releases](https://github.com/santec-corporation/Santec_IL_STS/releases) page.

### Python Installation

1. **Download and Install Python:**
   - Go to the [Python Downloads](https://www.python.org/downloads/) page.
   - Download the latest version (3.12 recommended).
   - Follow the installation instructions for your operating system.

2. **Upgrade Python Package:**
   - Open your command line and execute:
     ```bash
     pip install --upgrade python
     ```

### Install Dependencies

- **Install pythonnet:**
  ```bash
  pip install pythonnet
  ```
    - **Upgrade:**
    ```bash
    pip install --upgrade pythonnet
    ```

- **Install pyvisa:**
  ```bash
  pip install pyvisa
  ```
  - **Upgrade:**
    ```bash
    pip install --upgrade pyvisa
    ```
  
- **Install nidaqmx:**
  ```bash
  pip install nidaqmx
  ```
  - **Upgrade:**
    ```bash
    pip install --upgrade nidaqmx
    ```

<br/>

### For more information about the project, read the detailed readme [here](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/README-detailed.md).
