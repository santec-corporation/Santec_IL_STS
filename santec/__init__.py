# -*- coding: utf-8 -*-

"""
Santec IL STS process.

@organization: Santec Holdings Corp.
"""

import os
import logging
import datetime
import clr

# About
__version__ = "2.7.70"
__author__ = "Chentir MT"
__organization__ = "Santec Holdings Corporation"
__description__ = "Program to measure the Insertion Loss using the Swept Test System"
__url__ = "https://github.com/santec-corporation/Santec_IL_STS"
__date__ = "2024-10-01"
__license__ = "GNU General Public License v3.0"
__copyright__ = f"Copyright 2021-{datetime.date.today().year}, {__organization__}"


# Date and time for logging
dt = datetime.datetime.now()
dt = dt.strftime("%Y%m%d")

# Logger details
PROJECT_NAME = "SANTEC_IL_STS"
OUTPUT_LOGGER_NAME = f"output_{dt}.log"


def setup_logging(level=logging.DEBUG, file_write_mode='w'):
    """
    Set up logging for the application.

    Parameters:
        level (int): The logging level to use.
        file_write_mode (str): The mode for writing to the log file ('w' or 'a').

    Returns:
        Logger: The configured logger instance.
    """
    setup_logger = logging.getLogger(PROJECT_NAME)
    setup_logger.setLevel(level)

    file_handler = logging.FileHandler(OUTPUT_LOGGER_NAME, mode=file_write_mode)
    file_handler.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    if setup_logger.hasHandlers():
        setup_logger.handlers.clear()

    setup_logger.addHandler(file_handler)
    return setup_logger


logger = setup_logging()
logger.addHandler(logging.NullHandler())


def log_to_screen(level=logging.DEBUG) -> None:
    """ Log messages to the console at the specified level.

    Parameters:
        level (int): The logging level for console output.
    """
    log_to_stream(None, level)


def log_to_stream(stream_output, level=logging.DEBUG) -> None:
    """ Log messages to a specified output stream.

    Parameters:
        stream_output: The output stream for logging (e.g., console).
        level (int): The logging level for the stream output.
    """
    logger.setLevel(level)
    ch = logging.StreamHandler(stream_output)
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


# Add the Santec DLLs to the root.
ROOT = str(os.path.dirname(__file__)) + '\\DLL\\'
logger.info("Getting DLL path, root: %s", ROOT)
# print(ROOT)    # Uncomment in to check if the root was selected properly

DLL1 = 'InstrumentDLL'
DLL2 = 'STSProcess'
result1 = clr.AddReference(ROOT + DLL1)  # Add the Instrument DLL to the root
result2 = clr.AddReference(ROOT + DLL2)  # Add the STSProcess DLL to the root
logger.info("Adding Instrument DLL to the root, result: %s", result1)
logger.info("Adding STSProcess DLL to the root, result: %s", result2)
# print(result1, result2)     # Comment in to check if the DLLs were added.


# Import santec modules
from santec import file_logging
from .get_address import GetAddress
from .sts_process import StsProcess
from .daq_device_class import SpuDevice
from .tsl_instrument_class import TslInstrument
from .mpm_instrument_class import MpmInstrument

__all__ = [
    "StsProcess",
    "TslInstrument",
    "MpmInstrument",
    "SpuDevice",
    "GetAddress",
    "file_logging",
    "log_to_screen"
]
