# -*- coding: utf-8 -*-

"""
Created on Wed 05 17:17:26 2024

@author: chentir
@organization: santec holdings corp.
"""

# Importing high level santec package and its modules
from santec import TslInstrument, MpmInstrument, GetAddress

# Initializing get instrument address class
device_address = GetAddress()


def main():
    """ Main method of this project """

    tsl = None
    mpm = None

    device_address.initialize_instrument_addresses()
    tsl_address = device_address.get_tsl_address()
    mpm_address = device_address.get_mpm_address()
    interface = 'GPIB'

    # Only connect to the devices that the user wants to connect
    if tsl_address is not None:
        tsl = TslInstrument(interface, tsl_address)
        tsl.connect()
    else:
        raise Exception("There must be a TSL connected")

    if mpm_address is not None:
        mpm = MpmInstrument(interface, mpm_address)
        mpm.connect()

    # TSL Query / Write example
    # Write to TSL
    status = tsl.write_tsl('POW 5')       # Sets TSL output power to 5
    print(status)               # Prints 0 if write was successful

    # Query TSL
    status, response = tsl.query_tsl('POW?')        # Gets TSL output power
    print(status)             # Prints status 0 if query was successful
    print(response)           # Prints query response

    # MPM Query / Write example
    # Write to MPM
    status = mpm.write_mpm('AVG 5')    # Sets MPM averaging time to 5
    print(status)  # Prints 0 if write was successful

    # Query MPM
    status, response = mpm.query_mpm('AVG?')  # Gets MPM averaging time
    print(status)  # Prints status 0 if query was successful
    print(response)  # Prints query response


if __name__ == '__main__':
    main()
