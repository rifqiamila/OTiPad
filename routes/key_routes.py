"""
routes/key_routes.py — key management endpoints.

Endpoints
---------
    POST /api/key/generate    {length}      -> create a new random key file
    POST /api/key/validate    {key}         -> strict validation check
    GET  /api/key/template                  -> download the template key
    GET  /api/key/download/<id>             -> download a generated key
"""

from flask import Blueprint, request, jsonify, send_file

from config import TEMPLATE_KEY_PATH
from services import otp_service as svc

key_bp = Blueprint('key', __name__)


# ------------------------------------------------------------
# Generate a fresh random key
# ------------------------------------------------------------
@key_bp.route('/api/key/generate', methods=['POST'])
def generate():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    length_raw = data.get('length', 5_000_000)
    try:
        length = int(length_raw)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'BAD_REQUEST',
                        'reason': 'length must be an integer.'}), 400

    result = svc.generate_key(length)
    status = 200 if result['ok'] else 400
    return jsonify(result), status


# ------------------------------------------------------------
# Validate user-typed key
# ------------------------------------------------------------
@key_bp.route('/api/key/validate', methods=['POST'])
def validate():
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form

    key = data.get('key', '')
    result = svc.check_key_text(key)
    status = 200 if result['ok'] else 400
    return jsonify(result), status


# ------------------------------------------------------------
# Template key download
# ------------------------------------------------------------
@key_bp.route('/api/key/template', methods=['GET'])
def download_template():
    if not TEMPLATE_KEY_PATH:
        return jsonify({'ok': False, 'error': 'SERVER_ERROR'}), 500

    return send_file(
        TEMPLATE_KEY_PATH,
        mimetype='text/plain',
        as_attachment=True,
        download_name='key_template.txt',
    )


# ------------------------------------------------------------
# Generated key download
# ------------------------------------------------------------
@key_bp.route('/api/key/download/<key_id>', methods=['GET'])
def download_generated(key_id):
    path = svc.get_generated_key_path(key_id)
    if path is None:
        return jsonify({'ok': False, 'error': 'BAD_REQUEST',
                        'reason': 'unknown key id.'}), 404

    return send_file(
        path,
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'generated_key_{key_id}.txt',
    )