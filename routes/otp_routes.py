"""
routes/otp_routes.py — encrypt / decrypt endpoints.

Design notes
------------
* Text endpoints    -> accept JSON (from JS) or form-encoded (from curl).
                       Return JSON.
* File endpoints    -> accept multipart/form-data.
                       Return the ciphertext / plaintext file directly,
                       with Content-Disposition: attachment, so the browser
                       saves it to the user's Downloads folder.

Key source is passed as two fields:
    key_type   : "template" | "text" | "generated_id"
    key_value  : the text key, or the generated-key id (ignored for template)

Error mapping is centralised in _http_status_for().
"""

from flask import Blueprint, request, jsonify, send_file
from io import BytesIO

from config import MAX_FILE_SIZE
from services import otp_service as svc

otp_bp = Blueprint('otp', __name__)


# ------------------------------------------------------------
# Error code -> HTTP status
# ------------------------------------------------------------
_STATUS = {
    'EMPTY_INPUT':    400,
    'INVALID_KEY':    400,
    'SHORT_KEY':      200,   # expected condition, not a transport error
    'FILE_TOO_LARGE': 413,
    'BAD_HEADER':     400,
    'BAD_REQUEST':    400,
    'SERVER_ERROR':   500,
}


def _status_for(result):
    if result.get('ok'):
        return 200
    return _STATUS.get(result.get('error'), 400)

def _read_key_fields():
    """Extract key_type / key_value from JSON or form data."""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        return data.get('key_type', 'template'), data.get('key_value')
    return request.form.get('key_type', 'template'), request.form.get('key_value')


# ------------------------------------------------------------
# Text mode
# ------------------------------------------------------------
@otp_bp.route('/api/encrypt/text', methods=['POST'])
def encrypt_text():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    plaintext = data.get('plaintext', '')
    key_type, key_value = _read_key_fields()

    result = svc.encrypt_text(plaintext, key_type, key_value)
    return jsonify(result), _status_for(result)


@otp_bp.route('/api/decrypt/text', methods=['POST'])
def decrypt_text():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    ciphertext = data.get('ciphertext', '')
    key_type, key_value = _read_key_fields()

    result = svc.decrypt_text(ciphertext, key_type, key_value)
    return jsonify(result), _status_for(result)


# ------------------------------------------------------------
# File mode
# ------------------------------------------------------------
@otp_bp.route('/api/encrypt/file', methods=['POST'])
def encrypt_file():
    upload = request.files.get('file')
    if upload is None or upload.filename == '':
        return jsonify({'ok': False,
                        'error': 'BAD_REQUEST',
                        'reason': 'no file was uploaded.'}), 400

    # Peek at size before reading everything into memory
    upload.stream.seek(0, 2)
    size = upload.stream.tell()
    upload.stream.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({
            'ok': False,
            'error': 'FILE_TOO_LARGE',
            'size': size,
            'max': MAX_FILE_SIZE,
            'message': f'File is {size:,} bytes, max is {MAX_FILE_SIZE:,}.',
        }), 413

    data = upload.read()
    key_type, key_value = _read_key_fields()

    result = svc.encrypt_file(data, upload.filename, key_type, key_value)
    if not result['ok']:
        return jsonify(result), _status_for(result)

    # Send the .dat file directly as a download
    return send_file(
        BytesIO(result['data']),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=result['filename'],
    )


@otp_bp.route('/api/decrypt/file', methods=['POST'])
def decrypt_file():
    upload = request.files.get('file')
    if upload is None or upload.filename == '':
        return jsonify({'ok': False,
                        'error': 'BAD_REQUEST',
                        'reason': 'no file was uploaded.'}), 400

    data = upload.read()
    key_type, key_value = _read_key_fields()

    result = svc.decrypt_file(data, key_type, key_value)
    if not result['ok']:
        return jsonify(result), _status_for(result)

    return send_file(
        BytesIO(result['data']),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=result['filename'],
    )