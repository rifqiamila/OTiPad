"""check_step1.py — quick self-test for the crypto layer."""

import os
from config import ensure_dirs, TEMPLATE_KEY_PATH
from crypto.otp import (
    otp_encrypt_ints, otp_decrypt_ints,
    otp_encrypt_bytes, otp_decrypt_bytes,
    ints_to_letters, group5,
)
from crypto.keygen import fast_random_letters, ensure_template_key, load_key_from_file
from crypto.validators import extract_letters_to_ints, validate_key_text
from crypto.file_handler import build_header, parse_header


def main():
    ensure_dirs()

    # --- 1. fast_random_letters ---
    letters = fast_random_letters(20)
    assert len(letters) == 20 and letters.isalpha() and letters.isupper()
    print(f"[1] fast_random_letters(20)  -> {letters}")

    # --- 2. template key (create once, then lazy-load a slice) ---
    created = ensure_template_key()
    print(f"[2] ensure_template_key      -> {'created' if created else 'exists'}")
    key_slice = load_key_from_file(TEMPLATE_KEY_PATH, needed=10)
    assert len(key_slice) == 10
    print(f"[2] lazy load 10 letters     -> {key_slice}")

    # --- 3. text encrypt / decrypt round trip ---
    plain_ints = extract_letters_to_ints("Hello, World! 123")
    key = load_key_from_file(TEMPLATE_KEY_PATH, needed=len(plain_ints))
    ct_ints = otp_encrypt_ints(plain_ints, key)
    pt_ints = otp_decrypt_ints(ct_ints, key)
    assert pt_ints == plain_ints
    print(f"[3] plaintext  -> {ints_to_letters(plain_ints)}")
    print(f"[3] ciphertext -> {group5(ints_to_letters(ct_ints))}")
    print(f"[3] decrypted  -> {ints_to_letters(pt_ints)}")

    # --- 4. strict key validation ---
    ok, res = validate_key_text("XMCKLXMCKL")
    print(f"[4] valid key   -> ok={ok}, {len(res)} letters")
    ok, res = validate_key_text("XMCKL 123!", allow_trailing_newline=False)
    print(f"[4] invalid key -> ok={ok}, reason={res!r}")

    # --- 5. byte encrypt / decrypt round trip ---
    plain_bytes = b"\x89PNG\r\n\x1a\nFAKEIMAGEHEADER"
    key = load_key_from_file(TEMPLATE_KEY_PATH, needed=len(plain_bytes))
    ct = otp_encrypt_bytes(plain_bytes, key)
    pt = otp_decrypt_bytes(ct, key)
    assert pt == plain_bytes
    print(f"[5] bytes round-trip -> {len(plain_bytes)} bytes OK")

    # --- 6. header pack / parse ---
    header = build_header("laporan.docx")
    blob   = header + ct
    name, payload = parse_header(blob)
    assert name == "laporan.docx"
    assert payload == ct
    print(f"[6] header round-trip -> original name = {name!r}")

    print("\n[OK] all step-1 checks passed.")


if __name__ == "__main__":
    main()