# -*- coding: utf-8 -*-

"""
Created on Thu Mar 17 19:51:35 2022

@author: chentir
@organization: santec holdings corp.
"""


def instrument_error_strings(errorcode):
    """
    return  InstrumentDLL Error string

    Parameters
    ----------
    errorcode : int
        passed by DLL.

    Returns
    -------
    str
        Error description.

    """
    instrument_error = {
        '-2147483648': "Unknown",
        '-40': "InUseError",
        '-30': "ParameterError",
        '-20': "DeviceError",
        '-14': "CommunicationFailure",
        '-13': "UnauthorizedAccess",
        '-12': "IOException",
        '-11': "NotConnected",
        '-10': "Uninitialized",
        '-2': "TimeOut",
        '-1': "Failure",
        '-5': "CountMismatch",
        '0': "Success",
        '11': "AlreadyConnected",
        '10': "Stopped"
    }
    if str(errorcode) in instrument_error.keys():
        return instrument_error[str(errorcode)]
    else:
        return 'Unknown Error'


def sts_process_error_strings(errorcode):
    """
    return STSProcess DLL Error string

    Parameters
    ----------
    errorcode : int
        passed by DLL.

    Returns
    -------
    str
        Error description.

    """
    process_error = {
        '-2147483648': "Unknown",
        '-1115': "MeasureNotMatch",
        '-1114': "MeasureNotRescaling",
        '-1113': "MeasureNotExist",
        '-1112': "ReferenceNotMatch",
        '-1111': "ReferenceNotRescaling",
        '-1110': "ReferenceNotExist",
        '-1000': "NoCalculated",
        '-30': "ParameterError",
        '-1': "Failure",
        '0': "Success"
    }
    if str(errorcode) in process_error.keys():
        return process_error[str(errorcode)]
    else:
        return 'Unknown Error'
