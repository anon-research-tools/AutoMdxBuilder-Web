"""
简化版路由 - 使用线程任务管理器
"""
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid

from app_simple import task_manager

bp = Blueprint('main', __name__)


def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@bp.route('/')
def index():
    """主页"""
    return render_template('index.html')


@bp.route('/api/upload', methods=['POST'])
def upload_pdf():
    """上传PDF文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '只支持PDF文件'}), 400

        task_id = str(uuid.uuid4())

        task_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        filename = secure_filename(file.filename)
        if not filename or not filename.lower().endswith('.pdf'):
            filename = f"{task_id}.pdf"
        filepath = task_dir / filename
        file.save(str(filepath))

        current_app.logger.info(f'文件上传成功: {filename}, 任务ID: {task_id}')

        return jsonify({
            'task_id': task_id,
            'filename': filename,
            'message': '文件上传成功'
        })

    except Exception as e:
        current_app.logger.error(f'上传文件出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/convert', methods=['POST'])
def convert_pdf():
    """启动PDF转换任务"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        dpi = data.get('dpi', current_app.config['PDF_DEFAULT_DPI'])
        quality = data.get('quality', current_app.config['PDF_DEFAULT_QUALITY'])
        crop = data.get('crop', current_app.config['PDF_AUTO_CROP'])

        if not task_id:
            return jsonify({'error': '缺少task_id'}), 400

        task_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        if not task_dir.exists():
            return jsonify({'error': '任务不存在'}), 404

        pdf_files = list(task_dir.glob('*.pdf'))
        if not pdf_files:
            return jsonify({'error': '未找到PDF文件'}), 404

        pdf_path = str(pdf_files[0])
        output_dir = str(task_dir)

        # 使用线程任务管理器
        thread_task_id = task_manager.create_task()
        task_manager.run_in_thread(
            task_manager.convert_pdf_task,
            thread_task_id,
            pdf_path, output_dir, dpi, quality, crop
        )

        current_app.logger.info(f'PDF转换任务已启动: {task_id}, 线程任务ID: {thread_task_id}')

        return jsonify({
            'task_id': task_id,
            'celery_task_id': thread_task_id,  # 保持 API 兼容
            'message': 'PDF转换任务已启动'
        })

    except Exception as e:
        current_app.logger.error(f'启动转换任务出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/upload-index', methods=['POST'])
def upload_index():
    """上传索引文件"""
    try:
        data = request.form
        task_id = data.get('task_id')
        body_start = int(data.get('body_start', 1))

        if not task_id:
            return jsonify({'error': '缺少task_id'}), 400

        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        original_filename = file.filename
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''

        if file_ext not in ['txt', 'xlsx', 'xls']:
            return jsonify({'error': '只支持TXT和Excel文件'}), 400

        task_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        if not task_dir.exists():
            return jsonify({'error': '任务不存在'}), 404

        filename = secure_filename(original_filename)
        if not filename or '.' not in filename:
            filename = f"index.{file_ext}"
        index_file_path = task_dir / filename
        file.save(str(index_file_path))

        # 使用线程任务管理器
        thread_task_id = task_manager.create_task()
        task_manager.run_in_thread(
            task_manager.process_index_task,
            thread_task_id,
            str(index_file_path), body_start
        )

        current_app.logger.info(f'索引处理任务已启动: {task_id}, 线程任务ID: {thread_task_id}')

        return jsonify({
            'task_id': task_id,
            'celery_task_id': thread_task_id,
            'filename': filename,
            'message': '索引文件上传成功，正在处理...'
        })

    except Exception as e:
        current_app.logger.error(f'上传索引文件出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/build', methods=['POST'])
def build_mdx():
    """启动MDX构建任务"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        config_content = data.get('config', '')

        if not task_id:
            return jsonify({'error': '缺少task_id'}), 400

        task_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        if not task_dir.exists():
            return jsonify({'error': '任务不存在'}), 404

        config_path = task_dir / 'build.toml'
        if config_content:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
        else:
            return jsonify({'error': '缺少配置文件'}), 400

        output_dir = str(Path(current_app.config['OUTPUT_FOLDER']) / task_id)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 使用线程任务管理器
        thread_task_id = task_manager.create_task()
        task_manager.run_in_thread(
            task_manager.build_mdx_task,
            thread_task_id,
            str(config_path), output_dir
        )

        current_app.logger.info(f'MDX构建任务已启动: {task_id}, 线程任务ID: {thread_task_id}')

        return jsonify({
            'task_id': task_id,
            'celery_task_id': thread_task_id,
            'message': 'MDX构建任务已启动'
        })

    except Exception as e:
        current_app.logger.error(f'启动构建任务出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/status/<thread_task_id>')
def task_status(thread_task_id):
    """查询任务状态"""
    try:
        task = task_manager.get_task(thread_task_id)

        if task is None:
            return jsonify({
                'state': 'UNKNOWN',
                'status': '任务不存在'
            })

        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': '等待中...'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'current': task.current,
                'total': task.total,
                'status': task.status
            }
        elif task.state == 'SUCCESS':
            result = task.result
            if isinstance(result, dict) and result.get('status') == 'error':
                response = {
                    'state': 'FAILURE',
                    'status': result.get('message', '未知错误')
                }
            else:
                response = {
                    'state': task.state,
                    'result': result
                }
        else:  # FAILURE
            response = {
                'state': task.state,
                'status': task.error or '任务失败'
            }

        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f'查询任务状态出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/download/<task_id>')
def download_result(task_id):
    """下载生成的词典文件"""
    try:
        filename = request.args.get('filename')
        output_dir = Path(current_app.config['OUTPUT_FOLDER']) / task_id

        if not output_dir.exists():
            return jsonify({'error': '任务结果不存在'}), 404

        if filename:
            file_path = output_dir / filename
            if not file_path.exists():
                return jsonify({'error': f'文件 {filename} 不存在'}), 404

            return send_file(
                file_path,
                as_attachment=True,
                download_name=file_path.name
            )
        else:
            mdx_files = list(output_dir.glob('*.mdx'))
            if not mdx_files:
                return jsonify({'error': '未找到MDX文件'}), 404

            mdx_file = mdx_files[0]
            return send_file(
                mdx_file,
                as_attachment=True,
                download_name=mdx_file.name
            )

    except Exception as e:
        current_app.logger.error(f'下载文件出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/cleanup/<task_id>', methods=['DELETE'])
def cleanup_task(task_id):
    """清理任务文件"""
    try:
        import shutil

        upload_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        if upload_dir.exists():
            shutil.rmtree(upload_dir)

        output_dir = Path(current_app.config['OUTPUT_FOLDER']) / task_id
        if output_dir.exists():
            shutil.rmtree(output_dir)

        current_app.logger.info(f'任务文件已清理: {task_id}')

        return jsonify({'message': '文件已清理'})

    except Exception as e:
        current_app.logger.error(f'清理文件出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
