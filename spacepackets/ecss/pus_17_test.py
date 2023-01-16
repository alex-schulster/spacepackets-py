from __future__ import annotations
import enum
from typing import Optional

from spacepackets import SpacePacketHeader
from spacepackets.ccsds.time import CcsdsTimeProvider
from spacepackets.ecss.defs import PusService
from spacepackets.ecss.tm import PusVersion, PusTelemetry, AbstractPusTm


class Subservices(enum.IntEnum):
    TC_PING = 1
    TM_REPLY = 2


class Service17Tm(AbstractPusTm):
    def __init__(
        self,
        subservice: int,
        time_provider: Optional[CcsdsTimeProvider] = None,
        ssc: int = 0,
        source_data: bytearray = bytearray([]),
        apid: int = -1,
        packet_version: int = 0b000,
        space_time_ref: int = 0b0000,
        destination_id: int = 0,
    ):
        self.pus_tm = PusTelemetry(
            service=PusService.S17_TEST,
            subservice=subservice,
            time_provider=time_provider,
            seq_count=ssc,
            source_data=source_data,
            apid=apid,
            packet_version=packet_version,
            space_time_ref=space_time_ref,
            destination_id=destination_id,
        )

    def get_sp_header(self) -> SpacePacketHeader:
        return self.pus_tm.get_sp_header()

    @property
    def service(self) -> int:
        return self.pus_tm.service

    @property
    def subservice(self) -> int:
        return self.pus_tm.subservice

    @property
    def source_data(self) -> bytes:
        return self.pus_tm.source_data

    def pack(self) -> bytearray:
        return self.pus_tm.pack()

    @classmethod
    def __empty(cls) -> Service17Tm:
        return cls(subservice=0)

    @classmethod
    def unpack(
        cls,
        raw_telemetry: bytes,
        time_reader: Optional[CcsdsTimeProvider],
        pus_version: PusVersion = PusVersion.GLOBAL_CONFIG,
    ) -> Service17Tm:
        service_17_tm = cls.__empty()
        service_17_tm.pus_tm = PusTelemetry.unpack(
            raw_telemetry=raw_telemetry, time_reader=time_reader
        )
        return service_17_tm
