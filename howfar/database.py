from datetime import datetime
from typing import Iterator

from .dataconv import opt3004_code_to_lx
from .ringfs import RingFSRecordBase, RingFSFilesystem
from .uf2 import convert_from_uf2


class HowFarRecord2024091501(RingFSRecordBase):
    FORMAT = "<IHH"
    FIELDS = ["timestamp", "als_code", "tof_distance"]

    @classmethod
    def columns(cls) -> list[str]:
        return ["datetime", "timestamp", "alx_lx", "tof_distance_mm"]

    @classmethod
    def interpret(cls, record) -> tuple:
        return (
            datetime.fromtimestamp(record.timestamp).isoformat(),
            record.timestamp,
            opt3004_code_to_lx(record.als_code),
            record.tof_distance,
        )


# Record version database - add new versions here whenever they are introduced during firmware development.
version_record = {
    2024091501: HowFarRecord2024091501,
}


class HowFarDatabase(object):
    """
    High-level access to of a UF2 database file.
    """

    filesystem: RingFSFilesystem

    def __init__(self, uf2_data: bytes):
        flash_data = convert_from_uf2(uf2_data)
        # not strictly necessary but will help us catch egregious data conversion errors
        assert len(uf2_data) == 2 * len(flash_data)
        self.filesystem = RingFSFilesystem(flash_data, version_record)

    def columns(self) -> list[str]:
        return self.filesystem.record_type.columns()

    def records(self) -> Iterator[tuple]:
        yield from self.filesystem.records()


__all__ = [
    "HowFarDatabase",
]
