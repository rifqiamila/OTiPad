"""
crypto/otp.py — One-Time Pad core math.

Text mode:  letters A-Z mapped to 0-25,   C = (P + K) mod 26
File mode:  raw bytes 0-255,             C = (P + K) mod 256

This module is pure Python — no I/O, no Flask. Fully unit-testable.
"""

import string

ALPHABET = string.ascii_uppercase
A2I = {c: i for i, c in enumerate(ALPHABET)}
I2A = {i: c for i, c in enumerate(ALPHABET)}


# ------------------------------------------------------------
# Integer (text) mode
# ------------------------------------------------------------
def otp_encrypt_ints(plain_ints, key_ints):
    """Encrypt list[int] with list[int], mod 26. Assumes equal length."""
    return [(p + k) % 26 for p, k in zip(plain_ints, key_ints)]


def otp_decrypt_ints(cipher_ints, key_ints):
    """Decrypt list[int] with list[int], mod 26. Assumes equal length."""
    return [(c - k) % 26 for c, k in zip(cipher_ints, key_ints)]


def ints_to_letters(ints):
    """[7, 4, 11, 11, 14] -> 'HELLO'"""
    return ''.join(I2A[i] for i in ints)


def group5(s):
    """'HELLOWORLD' -> 'HELLO WORLD'"""
    return ' '.join(s[i:i + 5] for i in range(0, len(s), 5))


# ------------------------------------------------------------
# Byte (file) mode
# ------------------------------------------------------------
def otp_encrypt_bytes(plain_bytes, key_ints):
    """Encrypt bytes with list[int] (each int 0-25), mod 256."""
    return bytes((p + k) % 256 for p, k in zip(plain_bytes, key_ints))


def otp_decrypt_bytes(cipher_bytes, key_ints):
    """Decrypt bytes with list[int] (each int 0-25), mod 256."""
    return bytes((c - k) % 256 for c, k in zip(cipher_bytes, key_ints))