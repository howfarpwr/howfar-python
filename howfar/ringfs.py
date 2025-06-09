import collections
import struct
from typing import List, Callable, Iterator


class NamedTupleUnpackerMeta(type):
    """
    Static class constructor for BaseNamedTupleUnpacker.
    """

    def __new__(metacls, name, bases, dct):
        instance: NamedTupleUnpacker = super().__new__(metacls, name, bases, dct)  # noqa
        instance._struct = struct.Struct(instance.FORMAT)
        instance._namedtuple = collections.namedtuple(name, instance.FIELDS)
        instance.size = struct.calcsize(instance.FORMAT)
        return instance


class NamedTupleUnpacker(object, metaclass=NamedTupleUnpackerMeta):
    """
    This class allows declaring binary-packed C structures that unpack into named tuples. Usage:

    class PotatoHeader(BaseNamedTupleUnpacker):
        FORMAT = "<II"
        FIELDS = ["timestamp", "size"]

    record = PotatoHeader.unpack(b"...")
    """

    FORMAT: str = ""
    FIELDS: List[str] = []

    size: int
    _struct: struct.Struct
    _namedtuple: type

    @classmethod
    def unpack(cls, packed: bytes):
        return cls._namedtuple(*cls._struct.unpack(packed))

    @classmethod
    def unpack_from(cls, packed: bytes, offset: int):
        return cls._namedtuple(*cls._struct.unpack_from(packed, offset))


class RingFSRecordBase(NamedTupleUnpacker):
    """
    Base class for records stored on the filesystem. Subclasses should define the following:
    - FORMAT - on-disk format, `struct`-compatible
    - FIELDS - names for the values defined by FIELDS

    Subclasses may also optionally define the following:
    - interpret() - convert the raw namedtuple representation into a list human-readable of columns
    - columns() - list of columns returned by interpret(), if different from FIELDS
    """

    @classmethod
    def columns(cls) -> list[str]:
        return cls.FIELDS

    @classmethod
    def interpret(cls, record) -> tuple:
        return record


class RingFSSectorHeader(NamedTupleUnpacker):
    FORMAT = "<II"
    FIELDS = ["status", "version"]

    SECTOR_ERASED = 0xFFFFFFFF
    SECTOR_FREE = 0xFFFFFF00
    SECTOR_IN_USE = 0xFFFF0000
    SECTOR_ERASING = 0xFF000000
    SECTOR_FORMATTING = 0x00000000


class RingFSSlotHeader(NamedTupleUnpacker):
    FORMAT = "<I"
    FIELDS = ["status"]

    SLOT_ERASED = 0xFFFFFFFF
    SLOT_RESERVED = 0xFFFFFF00
    SLOT_VALID = 0xFFFF0000
    SLOT_GARBAGE = 0xFF000000


class RingFSFilesystemCorrupted(Exception):
    pass


class RingFSFilesystem(object):

    """
    Minimal read-only implementation of RingFS binary on-flash format.
    For use with HowFar only; makes too many assumptions and doesn't support full range of RingFS formats.
    """

    PAGE_SIZE = 256
    SECTOR_SIZE = 4096

    version: int
    flash_data: bytes
    n_sectors: int
    pages_per_sector: int
    records_per_slot: int

    def __init__(self, flash_data: bytes, version_record: dict[int, type[RingFSRecordBase]]):
        """
        Scan the flash image and determine the filesystem version.
        The scanning is simplified for read-only operation.
        """
        self.flash_data = flash_data
        self.n_sectors = len(self.flash_data) // self.SECTOR_SIZE
        self.pages_per_sector = self.SECTOR_SIZE // self.PAGE_SIZE

        # Find the last free sector...
        last_free_sector = None
        version = None
        for sector_id in range(self.n_sectors):
            sector_offset = sector_id * self.SECTOR_SIZE
            sector_header = RingFSSectorHeader.unpack_from(self.flash_data, sector_offset)

            if sector_header.status == RingFSSectorHeader.SECTOR_IN_USE:
                # make sure all sectors have the same version
                if version is not None:
                    if sector_header.version != version:
                        raise RingFSFilesystemCorrupted("filesystem has inconsistent header versions %d vs %d" %
                                                        (version, sector_header.version))
                else:
                    version = sector_header.version

            elif sector_header.status == RingFSSectorHeader.SECTOR_FREE:
                # record the location of the last free sector
                last_free_sector = sector_id

        # ...the first used sector is the one after that.
        self.first_sector_id = (last_free_sector + 1) % self.n_sectors
        self.version = version
        self.record_type = version_record[version]
        # calculate how many records fit per slot - this is filesystem version specific
        self.records_per_slot = (self.PAGE_SIZE - RingFSSlotHeader.size) // self.record_type.size

    def records(self) -> Iterator[tuple]:
        """
        Step through all the sectors and return all the records, one by one.
        """

        # iterate over the sectors in the order they were written
        for sector_index in range(self.n_sectors):
            sector_id = (self.first_sector_id + sector_index) % self.n_sectors
            sector_offset = sector_id * self.SECTOR_SIZE

            # make sure the sector actually contains valid data
            sector_header = RingFSSectorHeader.unpack_from(self.flash_data, sector_offset)
            if sector_header.status != RingFSSectorHeader.SECTOR_IN_USE:
                continue

            # iterate over each page in the sector, except the first (which only contains metadata)
            # we operate RingFS in "one slot per page" mode which makes this somewhat easier
            for slot_id in range(1, self.pages_per_sector):
                slot_offset = sector_offset + slot_id * self.PAGE_SIZE
                slot_header = RingFSSlotHeader.unpack_from(self.flash_data, slot_offset)
                if slot_header.status != RingFSSlotHeader.SLOT_VALID:
                    continue
                slot_data_offset = slot_offset + RingFSSlotHeader.size

                # found a valid slot - iterate over it and pass each record to the caller
                for record_id in range(self.records_per_slot):
                    # extract raw record bytes
                    record_offset = slot_data_offset + record_id * self.record_type.size
                    record_bytes = self.flash_data[record_offset:record_offset+self.record_type.size]
                    # skip empty records - side effect of our array packing
                    if all(byte == 0xff for byte in record_bytes):
                        continue
                    # unpack and interpret record bytes
                    record_struct = self.record_type.unpack(record_bytes)
                    record_dict = self.record_type.interpret(record_struct)
                    yield record_dict
