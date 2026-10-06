"""
crypto/keygen.py — Random key generation and lazy loading.

Three public functions:
    fast_random_letters(n)               -> str of n random A-Z
    ensure_template_key()                -> creates key_template.txt if missing
    load_key_from_file(path, needed)     -> list[int], reads at most `needed`
"""

import os
import secrets

from .otp import ALPHABET, A2I
from config import TEMPLATE_KEY_PATH, TEMPLATE_KEY_LEN, CHUNK_SIZE

# Random generation (unbiased via rejection sampling)
def fast_random_letters(n):
    """
    Return a string of n cryptographically random A-Z letters.
    Uses rejection sampling to avoid modulo bias.
    """
    out = []
    while len(out) < n:
        need = n - len(out)
        raw = secrets.token_bytes(min(need * 2 + 1024, 1_000_000))
        for b in raw:
            if b < 234:                     # 234 = 26 * 9  -> no bias
                out.append(ALPHABET[b % 26])
                if len(out) >= n:
                    break
    return ''.join(out)


# Template key
def ensure_template_key():
    """
    Create the template key file if it does not exist.
    Called once at app startup.
    Returns True if a new file was created, False if it already existed.
    """
    if os.path.exists(TEMPLATE_KEY_PATH):
        return False
    letters = fast_random_letters(TEMPLATE_KEY_LEN)
    with open(TEMPLATE_KEY_PATH, 'w', encoding='ascii') as f:
        f.write(letters)
    return True

# Lazy loading
def load_key_from_file(path, needed=None):
    key = []
    with open(path, 'r', encoding='ascii', errors='ignore') as f:
        while True:
            if needed is not None and len(key) >= needed:
                break
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            for ch in chunk:
                cu = ch.upper()
                if cu in ALPHABET:
                    key.append(A2I[cu])
                    if needed is not None and len(key) >= needed:
                        break
    return key