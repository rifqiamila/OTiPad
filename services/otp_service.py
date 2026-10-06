"""
services/otp_service.py — Business logic layer.

Bridges crypto/ (pure functions) and routes/ (HTTP handlers).
NO Flask imports here. Returns plain dicts.

Response contract
-----------------
    Success:
        {"ok": True, ...payload}

    Failure:
        {"ok": False, "error": "<CODE>", ...details}

Error codes
-----------
    EMPTY_INPUT      no A-Z letters in plaintext/ciphertext
    INVALID_KEY      key contains disallowed characters
    SHORT_KEY        key shorter than needed (extra: have, need, short_by)
    FILE_TOO_LARGE   uploaded file exceeds MAX_FILE_SIZE
    BAD_HEADER       .dat missing/malformed OTP header
    BAD_REQUEST      missing or malformed argument
    SERVER_ERROR     unexpected failure

Key source types (used by key_type argument)
--------------------------------------------
    "template"      -> use keys/key_template.txt (lazy loaded)
    "text"          -> user-pasted string, strictly validated
    "generated_id"  -> id of a file previously produced by generate_key()
"""

import os
import uuid

from config import (
    KEYS_DIR, TEMPLATE_KEY_PATH,
    MAX_FILE_SIZE, MAX_KEY_LENGTH, MAX_NAME_LEN,
    ENCRYPT_SUFFIX, DECRYPT_SUFFIX,
)
from crypto.otp import (
    otp_encrypt_ints, otp_decrypt_ints,
    otp_encrypt_bytes, otp_decrypt_bytes,
    ints_to_letters, group5, ALPHABET,
)
from crypto.keygen import fast_random_letters, load_key_from_file
from crypto.validators import extract_letters_to_ints, validate_key_text
from crypto.file_handler import build_header, parse_header


# Response helpers
def _ok(**payload):
    return {"ok": True, **payload}


def _err(code, **details):
    return {"ok": False, "error": code, **details}


# Internal: resolve key source to a list[int]
def _get_key_ints(key_type, key_value, needed):
    """
    Return (ok, key_ints) or (False, (error_code, reason)).

    Lazy-loads from disk when possible
    """
    if key_type == "template":
        if not os.path.isfile(TEMPLATE_KEY_PATH):
            return False, ("SERVER_ERROR", "template key is missing.")
        key = load_key_from_file(TEMPLATE_KEY_PATH, needed)
        return True, key

    if key_type == "text":
        if key_value is None:
            return False, ("BAD_REQUEST", "missing key text.")
        ok, res = validate_key_text(key_value, allow_trailing_newline=False)
        if not ok:
            return False, ("INVALID_KEY", res)
        return True, res

    if key_type == "generated_id":
        if not key_value:
            return False, ("BAD_REQUEST", "missing generated key id.")
        if not all(c.isalnum() for c in key_value):
            return False, ("BAD_REQUEST", "generated key id is malformed.")
        path = os.path.join(KEYS_DIR, f"generated_{key_value}.txt")
        if not os.path.isfile(path):
            return False, ("INVALID_KEY", "generated key file not found.")
        key = load_key_from_file(path, needed)
        return True, key

    return False, ("BAD_REQUEST", f"unknown key_type: {key_type!r}")


def _short_key_error(have, need):
    return _err(
        "SHORT_KEY",
        have=have,
        need=need,
        short_by=need - have,
        message=(
            f"Key has {have:,} letters, need {need:,}. "
            f"Add {need - have:,} more or change the key."
        ),
    )


# Text encryption / decryption
def encrypt_text(plaintext, key_type, key_value):
    plain_ints = extract_letters_to_ints(plaintext or "")
    if not plain_ints:
        return _err("EMPTY_INPUT",
                    message="No A-Z letters found in plaintext.")

    needed = len(plain_ints)
    ok, result = _get_key_ints(key_type, key_value, needed)
    if not ok:
        code, reason = result
        return _err(code, reason=reason)

    key_ints = result
    if len(key_ints) < needed:
        return _short_key_error(len(key_ints), needed)

    ct_ints = otp_encrypt_ints(plain_ints, key_ints)
    ct = ints_to_letters(ct_ints)

    return _ok(
        ciphertext=ct,
        grouped=group5(ct),
        plaintext_letter_count=needed,
    )


def decrypt_text(ciphertext, key_type, key_value):
    ct_ints = extract_letters_to_ints(ciphertext or "")
    if not ct_ints:
        return _err("EMPTY_INPUT",
                    message="No A-Z letters found in ciphertext.")

    needed = len(ct_ints)
    ok, result = _get_key_ints(key_type, key_value, needed)
    if not ok:
        code, reason = result
        return _err(code, reason=reason)

    key_ints = result
    if len(key_ints) < needed:
        return _short_key_error(len(key_ints), needed)

    pt_ints = otp_decrypt_ints(ct_ints, key_ints)
    pt = ints_to_letters(pt_ints)

    return _ok(
        plaintext=pt,
        grouped=group5(pt),
        ciphertext_letter_count=needed,
    )


# File encryption / decryption
def encrypt_file(file_bytes, original_filename, key_type, key_value):
    if not file_bytes:
        return _err("EMPTY_INPUT", message="Uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        return _err(
            "FILE_TOO_LARGE",
            size=len(file_bytes),
            max=MAX_FILE_SIZE,
            message=f"File is {len(file_bytes):,} bytes, max is {MAX_FILE_SIZE:,}.",
        )

    if not original_filename:
        original_filename = "unnamed.bin"

    needed = len(file_bytes)
    ok, result = _get_key_ints(key_type, key_value, needed)
    if not ok:
        code, reason = result
        return _err(code, reason=reason)

    key_ints = result
    if len(key_ints) < needed:
        return _short_key_error(len(key_ints), needed)

    ct_bytes = otp_encrypt_bytes(file_bytes, key_ints)
    header = build_header(original_filename)
    blob = header + ct_bytes

    stem, _ = os.path.splitext(original_filename)
    out_name = f"{stem}{ENCRYPT_SUFFIX}.dat"

    return _ok(
        data=blob,
        filename=out_name,
        original_filename=original_filename,
        byte_count=needed,
    )


def decrypt_file(dat_bytes, key_type, key_value):
    if not dat_bytes:
        return _err("EMPTY_INPUT", message="Uploaded file is empty.")

    # The .dat file is slightly larger than the plaintext (header overhead).
    hard_cap = MAX_FILE_SIZE + MAX_NAME_LEN + 16
    if len(dat_bytes) > hard_cap:
        return _err(
            "FILE_TOO_LARGE",
            size=len(dat_bytes),
            max=hard_cap,
            message=f"Ciphertext file exceeds {hard_cap:,} bytes.",
        )

    try:
        orig_name, cipher_bytes = parse_header(dat_bytes)
    except ValueError as e:
        return _err("BAD_HEADER", reason=str(e))

    if not cipher_bytes:
        return _err("EMPTY_INPUT", message="Cipher payload is empty.")

    needed = len(cipher_bytes)
    ok, result = _get_key_ints(key_type, key_value, needed)
    if not ok:
        code, reason = result
        return _err(code, reason=reason)

    key_ints = result
    if len(key_ints) < needed:
        return _short_key_error(len(key_ints), needed)

    pt_bytes = otp_decrypt_bytes(cipher_bytes, key_ints)

    stem, ext = os.path.splitext(orig_name)
    out_name = f"{stem}{DECRYPT_SUFFIX}{ext}"

    return _ok(
        data=pt_bytes,
        filename=out_name,
        original_filename=orig_name,
        byte_count=needed,
    )


# Key generation and validation
def generate_key(length):
    """Generate and persist a fresh random key. Returns download metadata."""
    if not isinstance(length, int) or length <= 0:
        return _err("BAD_REQUEST", reason="length must be a positive integer.")

    if length > MAX_KEY_LENGTH:
        return _err(
            "BAD_REQUEST",
            reason=f"length exceeds {MAX_KEY_LENGTH:,} letters.",
        )

    gen_id = uuid.uuid4().hex[:12]
    path = os.path.join(KEYS_DIR, f"generated_{gen_id}.txt")
    letters = fast_random_letters(length)

    with open(path, 'w', encoding='ascii') as f:
        f.write(letters)

    preview = letters[:80] + ("..." if length > 80 else "")

    return _ok(
        key_id=gen_id,
        length=length,
        preview=preview,
        download_filename=f"generated_key_{gen_id}.txt",
    )


def get_generated_key_path(key_id):
    """Return absolute path to a generated key file, or None."""
    if not key_id or not all(c.isalnum() for c in key_id):
        return None
    path = os.path.join(KEYS_DIR, f"generated_{key_id}.txt")
    return path if os.path.isfile(path) else None


def check_key_text(text):
    """Strictly validate a user-typed key. Used by POST /api/key/validate."""
    if text is None:
        return _err("BAD_REQUEST", reason="missing key text.")

    ok, res = validate_key_text(text, allow_trailing_newline=False)
    if not ok:
        return _err("INVALID_KEY", reason=res)

    return _ok(letter_count=len(res))


def get_template_info():
    """Small metadata block about the template key."""
    if not os.path.isfile(TEMPLATE_KEY_PATH):
        return _err("SERVER_ERROR", message="template key missing.")

    size = os.path.getsize(TEMPLATE_KEY_PATH)
    with open(TEMPLATE_KEY_PATH, 'r', encoding='ascii') as f:
        head = f.read(160)
    preview_letters = [c for c in head.upper() if c in ALPHABET][:80]
    preview = ''.join(preview_letters) + ("..." if size > 80 else "")

    return _ok(
        length=size,
        preview=preview,
        filename=os.path.basename(TEMPLATE_KEY_PATH),
    )