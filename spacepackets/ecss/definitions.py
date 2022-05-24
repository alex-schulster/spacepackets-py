import enum
from typing import Final


DEFAULT_MAX_TC_DATA_SIZE: Final = 1004


class PusServices(enum.IntEnum):
    S1_VERIFICATION = 1
    S2_RAW_CMD = 2
    S3_HOUSEKEEPING = 3
    S5_EVENT = 5
    S6_MEMORY_MGMT = 6
    S8_FUNC_CMD = 8
    S9_TIME_MGMT = 9
    S11_TC_SCHED = 11
    S17_TEST = 17
    S20_PARAMETER = 20
    S23_FILE_MGMT = 23
