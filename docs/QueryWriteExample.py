# -*- coding: utf-8 -*-

"""
Created on Fri Jan 21 17:17:26 2022

@author: chentir
@organization: santec holdings corp.
"""

# Importing high level santec package and its modules
from santec import TslDevice, MpmDevice, GetAddress

# Initializing get instrument address class
device_address = GetAddress()


def main():
    """ Main method of this project """

    tsl = None
    mpm = None

    device_address.Initialize_Device_Addresses()
    tsl_address = device_address.Get_Tsl_Address()
    mpm_address = device_address.Get_Mpm_Address()
    interface = 'GPIB'

    # Only connect to the devices that the user wants to connect
    if tsl_address is not None:
        tsl = TslDevice(interface, tsl_address)
        tsl.ConnectTSL()
    else:
        raise Exception("There must be a TSL connected")

    if mpm_address is not None:
        mpm = MpmDevice(interface, mpm_address)
        mpm.connect_mpm()

    # TSL Query / Write example
    # Write to TSL
    status = tsl.WriteTSL('POW 5')       # Sets TSL output power to 5
    print(status)               # Prints 0 if write was successful

    # Query TSL
    status, response = tsl.QueryTSL('POW?')        # Gets TSL output power
    print(status)             # Prints status 0 if query was successful
    print(response)           # Prints query response

    # MPM Query / Write example
    # Write to MPM
    status = mpm.WriteMPM('AVG 5')    # Sets MPM averaging time to 5
    print(status)  # Prints 0 if write was successful

    # Query MPM
    status, response = mpm.QueryMPM('AVG?')  # Gets MPM averaging time
    print(status)  # Prints status 0 if query was successful
    print(response)  # Prints query response


if __name__ == '__main__':
    main()
