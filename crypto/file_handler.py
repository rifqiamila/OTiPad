"""
crypto/file_handler.py — Ciphertext container format.

Layout of an encrypted file on disk:

    ┌────────┬──────────────────┬──────────────────┬─────────────────────┐
    │ "OTP1" │ 4-byte name_len  │ original filename│ encrypted payload   │
    │ 4 B    │ big-endian       │ UTF-8            │ rest of the file    │
    └────────┴──────────────────┴──────────────────┴─────────────────────┘

The header is unencrypted so decrypt can identify the file and restore
the original filename / extension automatically.
"""

from config import OTP_MAGIC, MAX_NAME_LEN


def build_header(original_filename):
    """
    Pack the original filename into a bytes header.
    Returns: OTP_MAGIC + name_len(4) + name_bytes
    """
    name_bytes = original_filename.encode('utf-8')
    if len(name_bytes) == 0:
        raise ValueError("original filename is empty.")
    if len(name_bytes) > MAX_NAME_LEN:
        raise ValueError(
            f"original filename too long ({len(name_bytes)} bytes, "
            f"max {MAX_NAME_LEN})."
        )
    return OTP_MAGIC + len(name_bytes).to_bytes(4, 'big') + name_bytes


def parse_header(data):
    """
    Split a ciphertext blob into (original_filename, cipher_bytes).
    Raises ValueError if the magic or length looks wrong.
    """
    if not data.startswith(OTP_MAGIC):
        raise ValueError("Not a valid OTP ciphertext file (missing magic).")

    pos = len(OTP_MAGIC)
    if len(data) < pos + 4:
        raise ValueError("Truncated header (no filename length).")

    name_len = int.from_bytes(data[pos:pos + 4], 'big')
    pos += 4

    if name_len <= 0 or name_len > MAX_NAME_LEN:
        raise ValueError(f"Invalid header: bad filename length ({name_len}).")

    if len(data) < pos + name_len:
        raise ValueError("Truncated header (filename incomplete).")

    orig_name = data[pos:pos + name_len].decode('utf-8')
    pos += name_len

    return orig_name, data[pos:]