"""check_step2.py — self-test for services/otp_service.py."""

import os
from config import ensure_dirs
from crypto.keygen import ensure_template_key
from services import otp_service as svc


def show(label, result):
    ok = result.get("ok")
    print(f"[{label}] ok={ok}", end="")
    if ok:
        if "ciphertext" in result:
            print(f" | ct={result['ciphertext'][:20]}...", end="")
        if "plaintext" in result:
            print(f" | pt={result['plaintext'][:20]}", end="")
        if "filename" in result:
            print(f" | file={result['filename']}", end="")
        if "byte_count" in result:
            print(f" | bytes={result['byte_count']}", end="")
        if "length" in result:
            print(f" | len={result['length']}", end="")
    else:
        print(f" | error={result['error']}", end="")
        if "reason" in result:
            print(f" | reason={result['reason']!r}", end="")
        if "have" in result:
            print(f" | have={result['have']} need={result['need']}", end="")
    print()


def main():
    ensure_dirs()
    ensure_template_key()

    # 1. Text encrypt / decrypt with template key
    r = svc.encrypt_text("Hello, World! 123", "template", None)
    show("encrypt_text/template", r)
    assert r["ok"]
    ct = r["ciphertext"]

    r2 = svc.decrypt_text(ct, "template", None)
    show("decrypt_text/template", r2)
    assert r2["ok"] and r2["plaintext"] == "HELLOWORLD"

    # 2. Short key -> SHORT_KEY error
    r = svc.encrypt_text("HELLOWORLD", "text", "XMCKL")
    show("encrypt_text/short", r)
    assert not r["ok"] and r["error"] == "SHORT_KEY"
    assert r["have"] == 5 and r["need"] == 10 and r["short_by"] == 5

    # 3. Enough text key
    r = svc.encrypt_text("HELLOWORLD", "text", "XMCKLXMCKL")
    show("encrypt_text/text_key", r)
    assert r["ok"]

    # 4. Invalid key characters
    r = svc.encrypt_text("HELLO", "text", "HELLO123")
    show("encrypt_text/bad_key", r)
    assert not r["ok"] and r["error"] == "INVALID_KEY"

    # 5. Empty plaintext
    r = svc.encrypt_text("!!! 123 ...", "template", None)
    show("encrypt_text/empty", r)
    assert not r["ok"] and r["error"] == "EMPTY_INPUT"

    # 6. File encrypt / decrypt round trip
    blob = b"\x89PNG\r\n\x1a\nFAKEIMAGE" * 4
    r = svc.encrypt_file(blob, "photo.png", "template", None)
    show("encrypt_file/template", r)
    assert r["ok"]
    dat = r["data"]

    r2 = svc.decrypt_file(dat, "template", None)
    show("decrypt_file/template", r2)
    assert r2["ok"] and r2["data"] == blob and r2["filename"] == "photo_dec.png"

    # 7. File too large
    big = b"A" * 6_000_000
    r = svc.encrypt_file(big, "big.bin", "template", None)
    show("encrypt_file/too_big", r)
    assert not r["ok"] and r["error"] == "FILE_TOO_LARGE"

    # 8. Bad header on decrypt
    r = svc.decrypt_file(b"NOT_OTP_HEADER", "template", None)
    show("decrypt_file/bad_header", r)
    assert not r["ok"] and r["error"] == "BAD_HEADER"

    # 9. Key generation
    r = svc.generate_key(1_000_000)
    show("generate_key/1M", r)
    assert r["ok"] and r["length"] == 1_000_000
    kid = r["key_id"]

    # 10. Use the generated key
    r2 = svc.encrypt_text("HELLOWORLD", "generated_id", kid)
    show("encrypt_text/gen_key", r2)
    assert r2["ok"]

    # 11. Path lookup + cleanup of generated file
    p = svc.get_generated_key_path(kid)
    assert p and os.path.isfile(p)
    os.remove(p)
    print(f"[cleanup] removed {os.path.basename(p)}")

    # 12. Key validation endpoint helper
    r = svc.check_key_text("XMCKL 123")
    show("check_key/bad", r)
    assert not r["ok"]
    r = svc.check_key_text("XMCKL")
    show("check_key/good", r)
    assert r["ok"] and r["letter_count"] == 5

    # 13. Template info
    r = svc.get_template_info()
    show("template_info", r)
    assert r["ok"] and r["length"] > 0

    print("\n[OK] all step-2 checks passed.")


if __name__ == "__main__":
    main()