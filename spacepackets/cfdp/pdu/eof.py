from __future__ import annotations
import struct
import copy
from typing import Optional

from spacepackets.cfdp.pdu import PduHeader
from spacepackets.cfdp.pdu.file_directive import (
    FileDirectivePduBase,
    DirectiveType,
    AbstractFileDirectiveBase,
)
from spacepackets.cfdp.defs import ConditionCode, CrcFlag, Direction
from spacepackets.cfdp.conf import PduConfig
from spacepackets.cfdp.tlv import EntityIdTlv
from spacepackets.crc import CRC16_CCITT_FUNC
from spacepackets.exceptions import BytesTooShortError


class EofPdu(AbstractFileDirectiveBase):
    """Encapsulates the EOF file directive PDU, see CCSDS 727.0-B-5 p.79"""

    def __init__(
        self,
        pdu_conf: PduConfig,
        file_checksum: bytes,
        file_size: int,
        fault_location: Optional[EntityIdTlv] = None,
        condition_code: ConditionCode = ConditionCode.NO_ERROR,
    ):
        """Constructor for an EOF PDU.

        Parameters
        -------------

        pdu_conf
            PDU Configuration.
        file_checksum
            4 byte checksum.
        file_size
            File Size
        fault_location
            Optional fault location TLV.
        condition_code
            Optional Condition Code

        Raises
        --------

        ValueError
            Invalid input, file checksum not 4 bytes long.
        """
        pdu_conf = copy.copy(pdu_conf)
        if len(file_checksum) != 4:
            raise ValueError
        self.condition_code = condition_code
        self.file_checksum = file_checksum
        pdu_conf.direction = Direction.TOWARDS_RECEIVER
        self.pdu_file_directive = FileDirectivePduBase(
            directive_code=DirectiveType.EOF_PDU,
            pdu_conf=pdu_conf,
            directive_param_field_len=0,
        )
        self.file_size = file_size
        self._fault_location = fault_location
        self._calculate_directive_param_field_len()

    @property
    def directive_type(self) -> DirectiveType:
        return self.pdu_file_directive.directive_type

    @property
    def pdu_header(self) -> PduHeader:
        return self.pdu_file_directive.pdu_header

    @property
    def packet_len(self) -> int:
        return self.pdu_file_directive.packet_len

    @property
    def fault_location(self):
        return self._fault_location

    @fault_location.setter
    def fault_location(self, fault_location: Optional[EntityIdTlv]):
        self._fault_location = fault_location
        self._calculate_directive_param_field_len()

    def _calculate_directive_param_field_len(self):
        directive_param_field_len = 9
        if self.pdu_file_directive.pdu_header.large_file_flag_set:
            directive_param_field_len = 13
        if self._fault_location is not None:
            directive_param_field_len += self._fault_location.packet_len
        if self.pdu_file_directive.pdu_conf.crc_flag == CrcFlag.WITH_CRC:
            directive_param_field_len += 2
        self.pdu_file_directive.directive_param_field_len = directive_param_field_len

    @classmethod
    def __empty(cls) -> EofPdu:
        empty_conf = PduConfig.empty()
        return cls(
            file_checksum=bytes([0x00, 0x00, 0x00, 0x00]),
            file_size=0,
            pdu_conf=empty_conf,
        )

    def pack(self) -> bytearray:
        eof_pdu = self.pdu_file_directive.pack()
        eof_pdu.append(self.condition_code << 4)
        eof_pdu.extend(self.file_checksum)
        if self.pdu_file_directive.pdu_header.large_file_flag_set:
            eof_pdu.extend(struct.pack("!Q", self.file_size))
        else:
            eof_pdu.extend(struct.pack("!I", self.file_size))
        if self.fault_location is not None:
            eof_pdu.extend(self.fault_location.pack())
        if self.pdu_file_directive.pdu_conf.crc_flag == CrcFlag.WITH_CRC:
            eof_pdu.extend(struct.pack("!H", CRC16_CCITT_FUNC(eof_pdu)))
        return eof_pdu

    @classmethod
    def unpack(cls, data: bytes) -> EofPdu:
        """Generate an object instance from raw data. Care should be taken to check whether
        the raw bytestream really contains an EOF PDU.

        Raises
        --------

        BytesTooShortError
            Raw data too short for expected object.
        ValueError
            Invalid directive type or data format.
        InvalidCrc
            PDU has a 16 bit CRC and the CRC check failed.
        """
        eof_pdu = cls.__empty()
        eof_pdu.pdu_file_directive = FileDirectivePduBase.unpack(raw_packet=data)
        eof_pdu.pdu_file_directive.verify_length_and_checksum(data)
        expected_min_len = eof_pdu.pdu_file_directive.header_len + 9
        if expected_min_len > len(data):
            raise BytesTooShortError(expected_min_len, len(data))
        current_idx = eof_pdu.pdu_file_directive.header_len
        eof_pdu.condition_code = data[current_idx] & 0xF0
        current_idx += 1
        eof_pdu.file_checksum = data[current_idx : current_idx + 4]
        current_idx += 4
        current_idx, eof_pdu.file_size = eof_pdu.pdu_file_directive.parse_fss_field(
            raw_packet=data, current_idx=current_idx
        )
        if len(data) > current_idx:
            eof_pdu.fault_location = EntityIdTlv.unpack(data=data[current_idx:])
        return eof_pdu

    def __eq__(self, other: EofPdu):
        return (
            self.pdu_file_directive == other.pdu_file_directive
            and self.condition_code == other.condition_code
            and self.file_checksum == other.file_checksum
            and self.file_size == other.file_size
            and self._fault_location == other._fault_location
        )

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(file_checksum={self.file_checksum!r},"
            f"file_size={self.file_size!r},"
            f" pdu_conf={self.pdu_file_directive.pdu_conf},"
            f"fault_location={self.fault_location!r},"
            f"condition_code={self.condition_code})"
        )
