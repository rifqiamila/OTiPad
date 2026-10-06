"""
config.py — Central configuration for the OTP web app.
No Flask imports here. Safe to use from any module.
"""

import os

# ------------------------------------------------------------
# Project layout
# ------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
KEYS_DIR    = os.path.join(BASE_DIR, 'keys')
STORAGE_DIR = os.path.join(BASE_DIR, 'storage')
UPLOADS_DIR = os.path.join(STORAGE_DIR, 'uploads')
OUTPUTS_DIR = os.path.join(STORAGE_DIR, 'outputs')

TEMPLATE_KEY_PATH = os.path.join(KEYS_DIR, 'key_template.txt')


def ensure_dirs():
    """Create keys/ and storage/ folders if they don't exist."""
    for d in (KEYS_DIR, STORAGE_DIR, UPLOADS_DIR, OUTPUTS_DIR):
        os.makedirs(d, exist_ok=True)


# ------------------------------------------------------------
# OTP limits and sizes
# ------------------------------------------------------------
TEMPLATE_KEY_LEN  = 5_000_000       # 5M letters — matches MAX_FILE_SIZE
MAX_FILE_SIZE     = 5_000_000       # 5 MB decimal (bytes)
MAX_KEY_FILE_SIZE = 50_000_000       # reject huge uploaded key files    --- NIH
MAX_KEY_LENGTH    = 20_000_000      # upper bound for /api/key/generate  --- NIH
CHUNK_SIZE        = 65536           # lazy read chunk (64 KB)

# ------------------------------------------------------------
# File naming conventions
# ------------------------------------------------------------
ENCRYPT_SUFFIX = "_enc"             # photo.jpg     -> photo_enc.dat
DECRYPT_SUFFIX = "_dec"             # photo_enc.dat -> photo_dec.jpg

TEXT_ENC_OUT = "encrypt_result.txt"
TEXT_DEC_OUT = "decrypt_result.txt"

# ------------------------------------------------------------
# Ciphertext container format
# ------------------------------------------------------------
OTP_MAGIC    = b'OTP1'              # 4-byte magic header
MAX_NAME_LEN = 4096                 # sanity limit for stored filename