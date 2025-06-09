# This code is adapted from Microsoft UF2:
# https://github.com/Microsoft/uf2/blob/master/utils/uf2conv.py
#
# Microsoft UF2
#
# The MIT License (MIT)
#
# Copyright (c) Microsoft Corporation
#
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import struct

UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
familyid = 0xbabbba4e


# noinspection SpellCheckingInspection
def convert_from_uf2(buf: bytes):
    appstartaddr = None
    numblocks = len(buf) // 512
    curraddr = None
    currfamilyid = None
    families_found = {}
    prev_flag = None
    all_flags_same = True
    outp = []
    for blockno in range(numblocks):
        ptr = blockno * 512
        block = buf[ptr:ptr + 512]
        hd = struct.unpack(b"<IIIIIIII", block[0:32])
        if hd[0] != UF2_MAGIC_START0 or hd[1] != UF2_MAGIC_START1:
            print("Skipping block at " + str(ptr) + "; bad magic")
            continue
        if hd[2] & 1:
            # NO-flash flag set; skip block
            continue
        datalen = hd[4]
        if datalen > 476:
            assert False, "Invalid UF2 data size at " + str(ptr)
        newaddr = hd[3]
        if (hd[2] & 0x2000) and (currfamilyid is None):
            currfamilyid = hd[7]
        if curraddr is None or ((hd[2] & 0x2000) and hd[7] != currfamilyid):
            currfamilyid = hd[7]
            curraddr = newaddr
            if familyid == 0x0 or familyid == hd[7]:
                appstartaddr = newaddr
        padding = newaddr - curraddr
        if padding < 0:
            assert False, "Block out of order at " + str(ptr)
        if padding > 10*1024*1024:
            assert False, "More than 10M of padding needed at " + str(ptr)
        if padding % 4 != 0:
            assert False, "Non-word padding size at " + str(ptr)
        while padding > 0:
            padding -= 4
            outp.append(b"\x00\x00\x00\x00")
        if familyid == 0x0 or ((hd[2] & 0x2000) and familyid == hd[7]):
            outp.append(block[32 : 32 + datalen])
        curraddr = newaddr + datalen
        if hd[2] & 0x2000:
            if hd[7] in families_found.keys():
                if families_found[hd[7]] > newaddr:
                    families_found[hd[7]] = newaddr
            else:
                families_found[hd[7]] = newaddr
        if prev_flag is None:
            prev_flag = hd[2]
        if prev_flag != hd[2]:
            all_flags_same = False
    if not all_flags_same:
        raise RuntimeError("flag mismatch - corrupted file?")
    return b"".join(outp)


# noinspection SpellCheckingInspection
def convert_to_uf2(file_content: bytes) -> bytes:
    appstartaddr = 0
    datapadding = b""
    while len(datapadding) < 512 - 256 - 32 - 4:
        datapadding += b"\x00\x00\x00\x00"
    numblocks = (len(file_content) + 255) // 256
    outp = []
    for blockno in range(numblocks):
        ptr = 256 * blockno
        chunk = file_content[ptr:ptr + 256]
        flags = 0x0
        if familyid:
            flags |= 0x2000
        hd = struct.pack(b"<IIIIIIII",
            UF2_MAGIC_START0, UF2_MAGIC_START1,
            flags, ptr + appstartaddr, 256, blockno, numblocks, familyid)
        while len(chunk) < 256:
            chunk += b"\x00"
        block = hd + chunk + datapadding + struct.pack(b"<I", UF2_MAGIC_END)
        assert len(block) == 512
        outp.append(block)
    return b"".join(outp)
