import os
import sys
import uuid
import zipfile
import webbrowser
import threading
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from config import PRESET_SIZES
from image_processor import reframe_image

# 获取基础目录（支持 PyInstaller 打包）
def get_base_dir():
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后
        return Path(sys._MEIPASS)
    else:
        # 开发环境
        return Path(__file__).parent

BASE_DIR = get_base_dir()

# 工作目录（上传、输出目录）
WORK_DIR = Path.cwd()
UPLOADS_DIR = WORK_DIR / 'uploads'
OUTPUT_DIR = WORK_DIR / 'output'

app = Flask(__name__, template_folder=str(BASE_DIR / 'templates'), static_folder=str(BASE_DIR / 'static'))
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/sizes', methods=['GET'])
def get_sizes():
    sizes = [{'name': name, 'width': w, 'height': h} for name, (w, h) in PRESET_SIZES.items()]
    return jsonify({'sizes': sizes})


@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    uploaded = []

    for file in files:
        if file and allowed_file(file.filename):
            file_id = str(uuid.uuid4())
            ext = file.filename.rsplit('.', 1)[1].lower()
            # 获取不含扩展名的原始文件名
            original_name = secure_filename(file.filename)
            original_base = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
            filename = f"{file_id}.{ext}"
            filepath = UPLOADS_DIR / filename
            file.save(filepath)
            uploaded.append({
                'id': file_id,
                'name': file.filename,
                'originalBase': original_base,
                'preview': f'/uploads/{filename}'
            })

    return jsonify({'files': uploaded})


@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_file(UPLOADS_DIR / filename)


@app.route('/api/process', methods=['POST'])
def process_images():
    data = request.get_json()
    file_ids = data.get('fileIds', [])
    original_names = data.get('originalNames', [])
    sizes = data.get('sizes', [])
    crop_direction = data.get('cropDirection', 'auto')
    output_format = data.get('outputFormat', 'jpeg')

    if not file_ids or not sizes:
        return jsonify({'error': 'Missing fileIds or sizes'}), 400

    # Build file info mapping
    file_info = {}
    for i, fid in enumerate(file_ids):
        original_name = original_names[i] if i < len(original_names) else f"image_{i}"
        original_base = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
        for ext in ALLOWED_EXTENSIONS:
            path = UPLOADS_DIR / f"{fid}.{ext}"
            if path.exists():
                file_info[fid] = {'path': path, 'original_base': original_base}
                break

    # Create output directory for this batch
    batch_id = str(uuid.uuid4())[:8]
    batch_dir = OUTPUT_DIR / batch_id
    batch_dir.mkdir(exist_ok=True)

    # Determine format settings
    if output_format == 'png':
        file_ext = 'png'
        save_format = 'PNG'
        save_kwargs = {'compress_level': 6}
    else:
        file_ext = 'jpg'
        save_format = 'JPEG'
        save_kwargs = {'quality': 100}

    # Process images
    size_tuples = [(s['width'], s['height']) if isinstance(s, dict) else tuple(s) for s in sizes]

    for fid, info in file_info.items():
        src = info['path']
        original_base = info['original_base']
        try:
            from PIL import Image
            with Image.open(src) as img:
                for w, h in size_tuples:
                    out_img = reframe_image(img, w, h, crop_direction)
                    out_name = f"{original_base}_{w}x{h}.{file_ext}"
                    out_img.save(batch_dir / out_name, format=save_format, **save_kwargs)
        except Exception as e:
            print(f"Error processing {src}: {e}")

    # Check output files count
    output_files = list(batch_dir.iterdir())

    if len(output_files) == 1:
        single_file = output_files[0]
        return jsonify({
            'downloadUrl': f'/download/{batch_id}/{single_file.name}',
            'isSingleFile': True
        })
    else:
        # Generate zip name with size info
        size_str = '_'.join([f"{w}x{h}" for w, h in size_tuples[:3]])
        if len(size_tuples) > 3:
            size_str += f"_等{len(size_tuples)}尺寸"
        zip_name = f"裁剪图片_{batch_id}_{size_str}.zip"
        zip_path = OUTPUT_DIR / zip_name
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in output_files:
                zf.write(f, f.name)

        return jsonify({
            'downloadUrl': f'/download/{zip_name}',
            'isSingleFile': False
        })


@app.route('/download/<filename>')
def download_file(filename):
    filepath = OUTPUT_DIR / filename
    if filepath.exists():
        return send_file(filepath, as_attachment=True)
    # Try as directory with single file
    return jsonify({'error': 'File not found'}), 404


@app.route('/download/<batch_id>/<filename>')
def download_single_file(batch_id, filename):
    filepath = OUTPUT_DIR / batch_id / filename
    if not filepath.exists():
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, as_attachment=True)


@app.route('/api/cleanup', methods=['POST'])
def cleanup_files():
    data = request.get_json()
    file_ids = data.get('fileIds', [])

    for fid in file_ids:
        for ext in ALLOWED_EXTENSIONS:
            path = UPLOADS_DIR / f"{fid}.{ext}"
            if path.exists():
                path.unlink()

    return jsonify({'success': True})


def wait_and_open_browser(url, port, max_attempts=10):
    """等待服务器启动后再打开浏览器"""
    import socket
    import time

    for _ in range(max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                webbrowser.open('http://127.0.0.1:' + str(port))
                return
        except:
            pass
        time.sleep(0.5)

    # 超时后也尝试打开
    webbrowser.open('http://127.0.0.1:' + str(port))


if __name__ == '__main__':
    # 确保工作目录存在
    UPLOADS_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 启动后自动打开浏览器
    threading.Thread(target=wait_and_open_browser, args=('http://127.0.0.1:5000', 5000), daemon=True).start()
    app.run(host='127.0.0.1', debug=False, use_reloader=False, port=5000)
