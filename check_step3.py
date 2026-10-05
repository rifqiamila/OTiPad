"""check_step3.py — end-to-end HTTP test using Flask's test client."""

import io
import os
from app import create_app
from config import ensure_dirs
from crypto.keygen import ensure_template_key


def jprint(label, resp):
    try:
        body = resp.get_json()
    except Exception:
        body = None
    print(f"[{label}] status={resp.status_code}", end="")
    if isinstance(body, dict):
        ok = body.get('ok')
        print(f" ok={ok}", end="")
        if not ok and 'error' in body:
            print(f" error={body['error']}", end="")
            if 'have' in body:
                print(f" have={body['have']} need={body['need']}", end="")
    else:
        # binary response (file download)
        cd = resp.headers.get('Content-Disposition', '')
        print(f" download={cd}", end="")
    print()


def main():
    ensure_dirs()
    ensure_template_key()
    app = create_app()
    c = app.test_client()

    # 1. Health
    jprint("GET /api/health", c.get('/api/health'))

    # 2. Text encrypt with template
    r = c.post('/api/encrypt/text',
               json={'plaintext': 'Hello, World! 123',
                     'key_type': 'template'})
    jprint("POST /api/encrypt/text (template)", r)
    assert r.status_code == 200 and r.get_json()['ok']
    ct = r.get_json()['ciphertext']

    # 3. Text decrypt round-trip
    r = c.post('/api/decrypt/text',
               json={'ciphertext': ct, 'key_type': 'template'})
    jprint("POST /api/decrypt/text (template)", r)
    assert r.status_code == 200 and r.get_json()['plaintext'] == 'HELLOWORLD'

    # 4. Short key -> 200 + SHORT_KEY
    r = c.post('/api/encrypt/text',
               json={'plaintext': 'HELLOWORLD',
                     'key_type': 'text', 'key_value': 'XMCKL'})
    jprint("POST /api/encrypt/text (short key)", r)
    assert r.status_code == 200 and r.get_json()['error'] == 'SHORT_KEY'
    assert r.get_json()['short_by'] == 5

    # 5. Bad key -> 400 INVALID_KEY
    r = c.post('/api/encrypt/text',
               json={'plaintext': 'HELLO',
                     'key_type': 'text', 'key_value': 'HELLO 123'})
    jprint("POST /api/encrypt/text (bad key)", r)
    assert r.status_code == 400 and r.get_json()['error'] == 'INVALID_KEY'

    # 6. File encrypt -> returns .dat download
    blob = b'\x89PNG\r\n\x1a\n' + b'FAKEIMAGE' * 4
    r = c.post('/api/encrypt/file',
               data={'key_type': 'template',
                     'file': (io.BytesIO(blob), 'photo.png')},
               content_type='multipart/form-data')
    jprint("POST /api/encrypt/file", r)
    assert r.status_code == 200
    assert 'photo_enc.dat' in r.headers.get('Content-Disposition', '')

    # 7. File decrypt round-trip
    dat = r.data
    r = c.post('/api/decrypt/file',
               data={'key_type': 'template',
                     'file': (io.BytesIO(dat), 'photo_enc.dat')},
               content_type='multipart/form-data')
    jprint("POST /api/decrypt/file", r)
    assert r.status_code == 200
    assert r.data == blob
    assert 'photo_dec.png' in r.headers.get('Content-Disposition', '')

    # 8. File too large -> 413
    big = b'A' * 6_000_000
    r = c.post('/api/encrypt/file',
               data={'key_type': 'template',
                     'file': (io.BytesIO(big), 'big.bin')},
               content_type='multipart/form-data')
    jprint("POST /api/encrypt/file (too big)", r)
    assert r.status_code == 413

    # 9. Bad header on decrypt -> 400 BAD_HEADER
    r = c.post('/api/decrypt/file',
               data={'key_type': 'template',
                     'file': (io.BytesIO(b'NOT_OTP_HEADER'),
                              'junk.dat')},
               content_type='multipart/form-data')
    jprint("POST /api/decrypt/file (bad header)", r)
    assert r.status_code == 400 and r.get_json()['error'] == 'BAD_HEADER'

    # 10. Key generate + download
    r = c.post('/api/key/generate', json={'length': 500_000})
    jprint("POST /api/key/generate", r)
    assert r.status_code == 200 and r.get_json()['ok']
    kid = r.get_json()['key_id']

    r = c.get(f'/api/key/download/{kid}')
    jprint(f"GET /api/key/download/{kid}", r)
    assert r.status_code == 200
    assert len(r.data) == 500_000

    # 11. Use generated key in a text encryption
    r = c.post('/api/encrypt/text',
               json={'plaintext': 'HELLOWORLD',
                     'key_type': 'generated_id', 'key_value': kid})
    jprint("POST /api/encrypt/text (gen key)", r)
    assert r.status_code == 200 and r.get_json()['ok']

    # 12. Key validate
    r = c.post('/api/key/validate', json={'key': 'XMCKL 123'})
    jprint("POST /api/key/validate (bad)", r)
    assert r.status_code == 400

    r = c.post('/api/key/validate', json={'key': 'XMCKL'})
    jprint("POST /api/key/validate (good)", r)
    assert r.status_code == 200 and r.get_json()['ok']

    # 13. Template key download
    r = c.get('/api/key/template')
    jprint("GET /api/key/template", r)
    assert r.status_code == 200
    assert 'key_template.txt' in r.headers.get('Content-Disposition', '')

    # cleanup generated key
    from services import otp_service as svc
    p = svc.get_generated_key_path(kid)
    if p and os.path.isfile(p):
        os.remove(p)
        print(f"[cleanup] removed {os.path.basename(p)}")

    print("\n[OK] all step-3 checks passed.")


if __name__ == '__main__':
    main()