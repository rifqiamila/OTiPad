"""
app.py — Flask entry point.

Responsibilities
----------------
1. Ensure keys/ and storage/ directories exist.
2. Ensure keys/key_template.txt exists (generate on first run).
3. Register blueprints.
4. Run the dev server.
"""

from flask import Flask, jsonify

from config import ensure_dirs, TEMPLATE_KEY_LEN, TEMPLATE_KEY_PATH
from crypto.keygen import ensure_template_key

from routes.main_routes import main_bp
from routes.otp_routes  import otp_bp
from routes.key_routes  import key_bp


def create_app():
    app = Flask(__name__)

    # Reasonable cap for the request body; the file endpoint also checks
    # explicit byte count, but this stops mega-uploads earlier.
    # 5 MB file + 20 MB key text + slack.
    app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
    app.config['MAX_FORM_MEMORY_SIZE'] = 128 * 1024 * 1024
    app.config['MAX_FORM_PARTS'] = 50_000

    app.register_blueprint(main_bp)
    app.register_blueprint(otp_bp)
    app.register_blueprint(key_bp)

    # Friendly JSON on 413 too
    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({
            'ok': False,
            'error': 'FILE_TOO_LARGE',
            'message': 'Request body too large.',
        }), 413

    return app


def _bootstrap():
    ensure_dirs()
    created = ensure_template_key()
    if created:
        print(f"[+] Created template key "
              f"({TEMPLATE_KEY_LEN:,} letters) at {TEMPLATE_KEY_PATH}")
    else:
        print(f"[i] Template key already exists at {TEMPLATE_KEY_PATH}")

_bootstrap()
app = create_app()


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)