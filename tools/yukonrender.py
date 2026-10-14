"""Explicit derived Windows display-index transforms; lossless decoder stays separate."""
# Observed NE0002:47c4..47dd postdecode normalization, YUKON.EXE SHA-256
# 9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06.
# Index zero is preserved; this transform implies no alpha or drawing mode.
WINDOWS_DISPLAY_INDEX_TABLE = bytes(120 if 1 <= i <= 9 or 245 <= i <= 255 else i for i in range(256))


def windows_display_indices(indices: bytes) -> bytes:
    """Return derived display indices without changing input or assigning alpha."""
    return indices.translate(WINDOWS_DISPLAY_INDEX_TABLE)
