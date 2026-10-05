import os
import string
import secrets

ALPHABET = string.ascii_uppercase
A2I = {c: i for i, c in enumerate(ALPHABET)}
I2A = {i: c for i, c in enumerate(ALPHABET)}

# ------------------------------------------------------------
# Key generation and loading
# ------------------------------------------------------------
def generate_key_file(path, length=100000):
    """Generate a key file containing random A-Z letters."""
    letters = ''.join(secrets.choice(ALPHABET) for _ in range(length))
    with open(path, 'w', encoding='ascii') as f:
        f.write(letters)
    print(f"[+] Generated {length} random letters in {path}")

def load_key_ints(path):
    """Read a key file and return a list of integers 0-25 from A-Z letters."""
    with open(path, 'r', encoding='ascii', errors='ignore') as f:
        data = f.read()
    key = [A2I[c] for c in data.upper() if c in ALPHABET]
    if not key:
        raise ValueError("Key file contains no A-Z letters.")
    return key

# ------------------------------------------------------------
# Text mode (only A-Z letters are encrypted)
# ------------------------------------------------------------
def text_encrypt(plaintext, key_ints):
    # Keep only A-Z, convert to uppercase
    pt = [c for c in plaintext.upper() if c in ALPHABET]
    # NIH BELUM CEK KALAU KEY NYA BAKAL CUKUP ATAU NGGAK
    if len(pt) > len(key_ints):
        raise ValueError(f"Key too short: need {len(pt)} letters, have {len(key_ints)}.")
    ct_chars = []
    for i, ch in enumerate(pt):
        p = A2I[ch]
        k = key_ints[i]
        c = (p + k) % 26
        ct_chars.append(I2A[c])
    return ''.join(ct_chars)

def text_decrypt(ciphertext, key_ints):
    ct = [c for c in ciphertext.upper() if c in ALPHABET]
    if len(ct) > len(key_ints):
        raise ValueError(f"Key too short: need {len(ct)} letters, have {len(key_ints)}.")
    pt_chars = []
    for i, ch in enumerate(ct):
        c = A2I[ch]
        k = key_ints[i]
        p = (c - k) % 26
        pt_chars.append(I2A[p])
    return ''.join(pt_chars)

def group5(s):
    """Group a string into blocks of 5 letters."""
    return ' '.join(s[i:i+5] for i in range(0, len(s), 5))

# ------------------------------------------------------------
# File mode (all bytes are encrypted)
# ------------------------------------------------------------
def file_encrypt(in_path, key_path, out_path):
    with open(in_path, 'rb') as f:
        plain = f.read()

    key = load_key_ints(key_path)
    if len(plain) > len(key):
        raise ValueError(f"Key too short: need {len(plain)} bytes, have {len(key)} letters.")

    # Encrypt every byte: c = (p + k) mod 256
    cipher = bytes((p + key[i]) % 256 for i, p in enumerate(plain))

    # Store original filename in a small header (not encrypted)
    filename = os.path.basename(in_path)
    filename_bytes = filename.encode('utf-8')
    header = b'OTP1' + len(filename_bytes).to_bytes(4, 'big') + filename_bytes

    with open(out_path, 'wb') as f:
        f.write(header)
        f.write(cipher)

    print(f"[+] Encrypted {in_path} -> {out_path}")

def file_decrypt(in_path, key_path, out_path=None):
    with open(in_path, 'rb') as f:
        data = f.read()

    if not data.startswith(b'OTP1'):
        raise ValueError("Invalid ciphertext file format.")

    pos = 4
    name_len = int.from_bytes(data[pos:pos+4], 'big')
    pos += 4
    orig_name = data[pos:pos+name_len].decode('utf-8')
    pos += name_len
    cipher = data[pos:]

    key = load_key_ints(key_path)
    if len(cipher) > len(key):
        raise ValueError(f"Key too short: need {len(cipher)} bytes, have {len(key)} letters.")

    # Decrypt every byte: p = (c - k) mod 256
    plain = bytes((c - key[i]) % 256 for i, c in enumerate(cipher))

    if out_path is None:
        out_path = orig_name

    with open(out_path, 'wb') as f:
        f.write(plain)

    print(f"[+] Decrypted {in_path} -> {out_path} (original name: {orig_name})")

# ------------------------------------------------------------
# Terminal menu
# ------------------------------------------------------------
def main():
    while True:
        print("\n=== OTP Terminal Test ===")
        print("1. Generate key file")
        print("2. Encrypt text")
        print("3. Decrypt text")
        print("4. Encrypt file")
        print("5. Decrypt file")
        print("0. Exit")
        choice = input("Choose: ").strip()

        if choice == '1':
            path = input("Key file path (e.g. key.txt): ").strip()
            length = input("Length (default 100000): ").strip()
            length = int(length) if length else 100000
            generate_key_file(path, length)

        elif choice == '2':
            key_path = input("Key file path: ").strip()
            key = load_key_ints(key_path)
            plaintext = input("Plaintext: ")
            ct = text_encrypt(plaintext, key)
            print("Ciphertext (no spaces):", ct)
            print("Ciphertext (5-letter groups):", group5(ct))
            save = input("Save ciphertext to file? (y/n): ").strip().lower()
            if save == 'y':
                out = input("Output file path: ").strip()
                with open(out, 'w', encoding='ascii') as f:
                    f.write(ct)   # save without spaces
                print("[+] Saved.")

        elif choice == '3':
            key_path = input("Key file path: ").strip()
            key = load_key_ints(key_path)
            ct = input("Ciphertext: ")
            pt = text_decrypt(ct, key)
            print("Plaintext (letters only):", pt)

        elif choice == '4':
            in_path = input("Input file path: ").strip()
            key_path = input("Key file path: ").strip()
            out_path = input("Output cipher file path (e.g. out.dat): ").strip()
            file_encrypt(in_path, key_path, out_path)

        elif choice == '5':
            in_path = input("Input cipher file path: ").strip()
            key_path = input("Key file path: ").strip()
            out_path = input("Output file path (blank = original name): ").strip() or None
            file_decrypt(in_path, key_path, out_path)

        elif choice == '0':
            print("Bye.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()