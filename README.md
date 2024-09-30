
<p align="right"> <a href="https://www.santec.com/jp/" target="_blank" rel="noreferrer"> <img src="https://www.santec.com/dcms_media/image/common_logo01.png" alt="santec" 
  width="250" height="45"/> </a> </p>

<h1 align="left"> Santec IL STS </h1>

Program to measure Insertion Loss using the Santec's Swept Test System. <br> <br>

## Overview

The **Santec_IL_STS** is designed to configure and operate the Santec Swept Test System (STS), allowing users to perform Wavelength-Dependent Loss (WDL) characterization of passive optical devices. <br/>
This tool facilitates the measurement of Insertion Loss (IL) using Santec's TSL and MPM series instruments.

---

## Key Features

- Configure the Santec Swept Test System (Light source: TSL series, Power meter: MPM series)
- Perform wavelength scans
- Calculate and save Wavelength-Dependent Loss (WDL) data

---

## Getting Started

### System Requirements

- **OS:** Windows 10 / 8 / 7
- **Drivers:** 
  - NI-488.2 (ver. 15 to 21)
  - NI-DAQmx (ver. 15 to 21)

### Dependencies

- [pythonnet](https://github.com/pythonnet/pythonnet/wiki/Installation) : For .NET interoperability.
- [pyvisa](https://pyvisa.readthedocs.io/en/latest/index.html) : For controlling measurement devices.
- [nidaqmx](https://nidaqmx-python.readthedocs.io/en/latest/) : API for NIDAQ driver interaction.

---

## Installation

### Cloning the Repository

To clone the repository, use the following command in your terminal:

```bash
git clone https://github.com/santec-corporation/Santec_IL_STS.git
```


### Downloading the Latest Release,
You can download the latest release directly from the [Releases](https://github.com/santec-corporation/Santec_IL_STS/releases) page.

<br/>

### For more information about the project, read the detailed readme [here](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/README-detailed.md).
