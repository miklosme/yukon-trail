"""Bounded, byte-preserving original .GAM container. No state defaults or migration.

Observed source transfer sizes: NE1:974a read /97ec write; save blocks remain
opaque except already recovered state-word locations. OS/dialog/session restore
behavior is separate from this container parser.
"""
from dataclasses import dataclass
import struct

SIZE = 11221
STATE_OFFSET = 79
STATE_SIZE = 0x386
JOURNAL_OFFSET = STATE_OFFSET + STATE_SIZE
JOURNAL_SIZE = 0x2800

class SaveError(ValueError):
    pass

@dataclass(frozen=True)
class OriginalSave:
    signature: bytes
    title: bytes
    version: bytes
    state: bytes
    journal: bytes

    def bytes(self):
        blocks = (self.signature,self.title,self.version,self.state,self.journal)
        if any(not isinstance(v,bytes) for v in blocks) or tuple(map(len,blocks)) != (5,64,10,STATE_SIZE,JOURNAL_SIZE):
            raise SaveError('Original fixed save block lengths required')
        return b''.join(blocks)

    def word(self, offset):
        if not isinstance(offset,int) or offset<0 or offset+2>STATE_SIZE:
            raise SaveError('State word outside original buffer')
        return struct.unpack_from('<H',self.state,offset)[0]

    def journal_text(self):
        if b'\0' not in self.journal: raise SaveError('Unterminated original journal buffer')
        return self.journal.split(b'\0',1)[0]


def read_save(data):
    if not isinstance(data,bytes) or len(data)!=SIZE:
        raise SaveError('Only exact11221byte original save containers supported')
    # Match the recovered current-version branch. Older-version warnings/migration
    # are intentionally unsupported; ignored fifth signature and post-NUL field
    # bytes remain byte-preserved rather than imposing an invented padding rule.
    if header_status(data[:79]) != 0:
        raise SaveError('Unsupported original save signature/title/version status')
    return OriginalSave(data[:5],data[5:69],data[69:79],data[79:981],data[981:])


def header_status(header):
    """Original bounded status before UI:0 equal,1 older,-1/-2/-3 invalid.

    Bounded NUL-aware byte comparison, not numerical version interpretation.
    This exposes status only; original warning/error actions remain separate.
    """
    if not isinstance(header,bytes) or len(header)!=79:
        raise SaveError('Exact79byte original header required')
    def compare(actual,expected,count):
        end=actual.find(b'\0',0,count)
        size=count if end<0 else end+1
        first=actual[:size];second=expected[:size]
        return (first>second)-(first<second)
    if compare(header[:5],b'MECC\0',4):return -1
    if compare(header[5:69],b'The Yukon Trail\0'.ljust(64,b'\0'),64):return -2
    status=compare(header[69:79],b'0.1\0'.ljust(10,b'\0'),10)
    return 1 if status<0 else -3 if status>0 else 0
