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
__version__ = "2.7.8"
__author__ = "Chentir MT"
__organization__ = "Santec Holdings Corporation"
__description__ = "Program to measure the Insertion Loss using the Swept Test System"
__url__ = "https://github.com/santec-corporation/Santec_IL_STS"
__date__ = "2024-09-23"
__license__ = "GNU General Public License v3.0"
__copyright__ = f"Copyright 2022-{datetime.date.today().year}, {__organization__}"


# Date and time for logging
dt = datetime.datetime.now()
dt = dt.strftime("%Y%m%d")

PROJECT_NAME = "SANTEC_IL_STS"
OUTPUT_LOGGER_NAME = f"output_{dt}.log"


# Setup logging
def setup_logging(level=logging.DEBUG, file_write_mode='w'):
    """

    Parameters
    ----------
    level: int | Logging mode
    file_write_mode: str | Logging file write mode

    Returns
    -------
    setup_logger: Logger = logging.getLogger(PROJECT_NAME)
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
    """ Log to screen. """
    log_to_stream(None, level)


def log_to_stream(stream_output, level=logging.DEBUG) -> None:
    """ Log to stream. """
    logger.setLevel(level)
    ch = logging.StreamHandler(stream_output)
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


# Add the Santec DLL to the root.
ROOT = str(os.path.dirname(__file__)) + '\\DLL\\'
logger.info("Getting DLL path, root: %s", ROOT)
# print(ROOT)    # Uncomment in to check if the root was selected properly

PATH1 = 'InstrumentDLL'
PATH2 = 'STSProcess'
result1 = clr.AddReference(ROOT + PATH1)  # Add the Instrument DLL to the root
result2 = clr.AddReference(ROOT + PATH2)  # Add the STSProcess DLL to the root
logger.info("Adding Instrument DLL to the root, result: %s", result1)
logger.info("Adding STSProcess DLL to the root, result: %s", result2)
# print(result1, result2)     # Comment in to check if the DLLs were added.


# Import santec modules
from santec import file_logging
from .get_address import GetAddress
from .sts_process import StsProcess
from .daq_device_class import SpuDevice
from .mpm_instrument_class import MpmDevice
from .tsl_instrument_class import TslInstrument
from .error_handing_class import instrument_error_strings, sts_process_error_strings

__all__ = [
    "StsProcess",
    "TslInstrument",
    "MpmDevice",
    "SpuDevice",
    "GetAddress",
    "file_logging",
    "instrument_error_strings",
    "sts_process_error_strings",
    "logger"
]
