"""routes/main_routes.py — page rendering + health."""

from flask import Blueprint, render_template, jsonify
from services import otp_service as svc

main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET'])
def index():
    """Render the OTP web app."""
    return render_template('index.html')


@main_bp.route('/api/health', methods=['GET'])
def health():
    """Small JSON endpoint so you can sanity-check the server."""
    t = svc.get_template_info()
    return jsonify({
        'ok': True,
        'service': 'otp-web',
        'template_key': t,
    })