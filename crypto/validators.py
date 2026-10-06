"""
crypto/validators.py — Input validation.

Two kinds of validation, intentionally separated:

    extract_letters_to_ints(text)
        PERMISSIVE. For plaintext / ciphertext.
        Silently drops anything that isn't A-Z.

    validate_key_text(raw, allow_trailing_newline=False)
        STRICT. For user-supplied keys.
        Rejects any non-letter character with a descriptive reason.

Return conventions:
    validate_key_text -> (ok: bool, result)
        result is list[int] when ok=True
        result is a human-readable reason str when ok=False
"""

from .otp import ALPHABET, A2I


# Permissive (text input)
def extract_letters_to_ints(text):
    """
    Return list[int] (0-25) keeping only A-Z / a-z.
    Numbers, spaces, punctuation, newlines are dropped.
    Used for plaintext and ciphertext.
    """
    return [A2I[ch] for ch in text.upper() if ch in ALPHABET]


# Strict (key input)
def validate_key_text(raw, allow_trailing_newline=False):
    """
    Strictly validate a user-supplied key string.

    Rules:
      - Only A-Z / a-z allowed.
      - If `allow_trailing_newline` is True, any number of trailing
        \\r / \\n chars are tolerated (text editors add them).
      - Empty key -> rejected.
      - Any other character -> rejected

    Returns:
      (True, list[int])   if valid
      (False, str)        if invalid — str explains why
    """
    s = raw
    if allow_trailing_newline:
        s = s.rstrip('\r\n')

    if not s:
        return False, "key is empty."

    bad = []
    seen = set()
    for ch in s:
        if ('A' <= ch <= 'Z') or ('a' <= ch <= 'z'):
            continue
        if ch not in seen:
            seen.add(ch)
            bad.append(ch)
            if len(bad) >= 5:
                break

    if bad:
        shown = ', '.join(repr(c) for c in bad)
        return False, f"contains invalid character(s): {shown}. Only A-Z / a-z allowed."

    return True, [A2I[ch.upper()] for ch in s]