import datetime
import santec.sts_process as STS
from santec.get_address import GetAddress
import santec.file_logging as file_logging
from santec.daq_device_class import SpuDevice
from santec.mpm_instrument_class import MpmDevice
from santec.tsl_instrument_class import TslDevice
from santec.error_handing_class import instrument_error_strings, sts_process_error_strings


# About
__version__ = "2.6.2"
__author__ = "Chentir MT"
__organization__ = "Santec Holdings Corporation"
__description__ = "Program to measure the Insertion Loss using the Swept Test System"
__url__ = "https://github.com/santec-corporation/Santec_IL_STS"
__date__ = "2024-09-23"
__license__ = "GNU General Public License v3.0"
__copyright__ = "Copyright 2022-{}, {}".format(datetime.date.today().year, __organization__)


__all__ = [
    "STS",
    "TslDevice",
    "MpmDevice",
    "SpuDevice",
    "GetAddress",
    "file_logging",
    "instrument_error_strings",
    "sts_process_error_strings"
]
