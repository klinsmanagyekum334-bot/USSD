from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename
import json
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-this-to-a-random-secret-key-later'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

CONTENT_FILE = 'content.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}

# ---------- ADMIN LOGINS (plain for now) ----------
ADMINS = {
    'DrIsaak': 'Frimpong',
    'Ophyser': 'Klinsman@ophyser1',
}

# ---------- LOCKED FIELDS (cannot be edited) ----------
LOCKED_KEYS = ['dev_credit']  # "Developed by Ophyser" — protected


# ---------- CONTENT HELPERS ----------
def load_content():
    """Load content.json or return empty dict."""
    if not os.path.exists(CONTENT_FILE):
        return {}
    try:
        with open(CONTENT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_content(data):
    """Save content dict to content.json."""
    with open(CONTENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get(key, default=''):
    """Fetch a content value by key, or fall back to default."""
    return load_content().get(key, default)


def allowed_file(filename):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# Make get() and content available in every template
@app.context_processor
def inject_content():
    return {
        'c': load_content(),
        'get': get,
    }


# ---------- PUBLIC ROUTES ----------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/services')
def services():
    return render_template('services.html')


@app.route('/books')
def books():
    return render_template('books.html')


# ---------- ADMIN ROUTES ----------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_user'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if username in ADMINS and ADMINS[username] == password:
            session['admin_user'] = username
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_user', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_user'):
        return redirect(url_for('admin_login'))

    content = load_content()
    return render_template(
        'admin_dashboard.html',
        content=content,
        locked=LOCKED_KEYS,
        user=session.get('admin_user'),
    )


@app.route('/admin/save', methods=['POST'])
def admin_save():
    if not session.get('admin_user'):
        return jsonify({'ok': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'ok': False, 'error': 'Invalid data'}), 400

    current = load_content()

    # Update only editable (non-locked) fields
    for key, value in data.items():
        if key in LOCKED_KEYS:
            continue
        current[key] = value

    save_content(current)
    return jsonify({'ok': True})


@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    if not session.get('admin_user'):
        return jsonify({'ok': False, 'error': 'Not logged in'}), 401

    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'ok': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'ok': False, 'error': 'File type not allowed'}), 400

    # Save file with a unique name
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f'{uuid.uuid4().hex}.{ext}'
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(save_path)

    url = url_for('static', filename=f'uploads/{unique_name}')
    return jsonify({'ok': True, 'url': url})


# ---------- RUN ----------
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)