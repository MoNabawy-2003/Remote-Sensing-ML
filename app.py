import os
import sys
import time
import subprocess
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='public', static_url_path='')

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


@app.route('/output/<path:filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)


@app.route('/upload', methods=['POST'])
def upload():
    hdr_file = request.files.get('hdr')
    dat_file = request.files.get('dat')

    if not hdr_file or not dat_file:
        return jsonify({
            'success': False,
            'error': 'Both files are required.',
        }), 400

    upload_dir = 'uploads'
    os.makedirs(upload_dir, exist_ok=True)

    hdr_path = os.path.join(upload_dir, hdr_file.filename)
    dat_path = os.path.join(upload_dir, dat_file.filename)
    hdr_file.save(hdr_path)
    dat_file.save(dat_path)

    out_name = f'final_{int(time.time() * 1000)}.png'
    out_path = os.path.join(OUTPUT_DIR, out_name)

    try:
        subprocess.run(
            [sys.executable, 'classify.py', hdr_path, dat_path, out_path],
            check=True,
            cwd=ROOT,
        )
    except subprocess.CalledProcessError as e:
        return jsonify({
            'success': False,
            'error': f'Pipeline failed (exit {e.returncode}).',
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
        }), 500
    finally:
        for p in [hdr_path, dat_path]:
            try:
                os.remove(p)
            except OSError:
                pass

    return jsonify({
        'success': True,
        'imageUrl': f'/output/{out_name}',
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
