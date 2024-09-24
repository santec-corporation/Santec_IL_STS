import logging
import datetime

# About
__version__ = "2.6.3"
__author__ = "Chentir MT"
__organization__ = "Santec Holdings Corporation"
__description__ = "Program to measure the Insertion Loss using the Swept Test System"
__url__ = "https://github.com/santec-corporation/Santec_IL_STS"
__date__ = "2024-09-23"
__license__ = "GNU General Public License v3.0"
__copyright__ = "Copyright 2022-{}, {}".format(datetime.date.today().year, __organization__)


# Date and time for logging
dt = datetime.datetime.now()
dt = dt.strftime("%Y%m%d")

PROJECT_NAME = "SANTEC_IL_STS"
OUTPUT_LOGGER_NAME = f"output_{dt}.log"


# Setup logging
def setup_logging(level=logging.DEBUG):
    setup_logger = logging.getLogger(PROJECT_NAME)
    setup_logger.setLevel(level)

    file_handler = logging.FileHandler(OUTPUT_LOGGER_NAME)
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
    log_to_stream(None, level)


def log_to_stream(stream_output, level=logging.DEBUG) -> None:
    logger.setLevel(level)
    ch = logging.StreamHandler(stream_output)
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)


import santec.sts_process as STS
from santec.get_address import GetAddress
import santec.file_logging as file_logging
from santec.daq_device_class import SpuDevice
from santec.mpm_instrument_class import MpmDevice
from santec.tsl_instrument_class import TslDevice
from santec.error_handing_class import instrument_error_strings, sts_process_error_strings

__all__ = [
    "STS",
    "TslDevice",
    "MpmDevice",
    "SpuDevice",
    "GetAddress",
    "file_logging",
    "instrument_error_strings",
    "sts_process_error_strings",
    "logger"
]
