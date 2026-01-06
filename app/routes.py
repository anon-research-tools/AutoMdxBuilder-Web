"""
Web应用路由
"""
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
import os
from app.tasks import convert_pdf_task, build_mdx_task, process_index_task

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
    """
    上传PDF文件
    返回任务ID
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': '只支持PDF文件'}), 400

        # 生成唯一的任务ID
        task_id = str(uuid.uuid4())

        # 创建任务目录
        task_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        task_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        filename = secure_filename(file.filename)
        # 确保文件有.pdf扩展名
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
    """
    启动PDF转换任务
    参数: task_id, dpi, quality, crop
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        dpi = data.get('dpi', current_app.config['PDF_DEFAULT_DPI'])
        quality = data.get('quality', current_app.config['PDF_DEFAULT_QUALITY'])
        crop = data.get('crop', current_app.config['PDF_AUTO_CROP'])

        if not task_id:
            return jsonify({'error': '缺少task_id'}), 400

        # 查找PDF文件
        task_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        if not task_dir.exists():
            return jsonify({'error': '任务不存在'}), 404

        pdf_files = list(task_dir.glob('*.pdf'))
        if not pdf_files:
            return jsonify({'error': '未找到PDF文件'}), 404

        pdf_path = str(pdf_files[0])
        output_dir = str(task_dir)

        # 启动Celery任务
        celery_task = convert_pdf_task.delay(
            task_id=task_id,
            pdf_path=pdf_path,
            output_dir=output_dir,
            dpi=dpi,
            quality=quality,
            crop=crop
        )

        current_app.logger.info(f'PDF转换任务已启动: {task_id}, Celery任务ID: {celery_task.id}')

        return jsonify({
            'task_id': task_id,
            'celery_task_id': celery_task.id,
            'message': 'PDF转换任务已启动'
        })

    except Exception as e:
        current_app.logger.error(f'启动转换任务出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/upload-index', methods=['POST'])
def upload_index():
    """
    上传索引文件 (TXT/Excel)
    参数: task_id, file (TXT或Excel文件), body_start (正文起始页)
    """
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

        # 检查文件扩展名
        original_filename = file.filename
        file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''

        if file_ext not in ['txt', 'xlsx', 'xls']:
            return jsonify({'error': '只支持TXT和Excel文件(.txt, .xlsx, .xls)'}), 400

        # 任务目录
        task_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        if not task_dir.exists():
            return jsonify({'error': '任务不存在'}), 404

        # 保存上传的索引文件，确保保留扩展名
        filename = secure_filename(original_filename)
        if not filename or '.' not in filename:
            filename = f"index.{file_ext}"
        index_file_path = task_dir / filename
        file.save(str(index_file_path))

        current_app.logger.info(f'索引文件上传成功: {filename}, 任务ID: {task_id}')

        # 启动Celery任务处理索引文件
        celery_task = process_index_task.delay(
            task_id=task_id,
            index_file_path=str(index_file_path),
            body_start=body_start
        )

        current_app.logger.info(f'索引文件处理任务已启动: {task_id}, Celery任务ID: {celery_task.id}')

        return jsonify({
            'task_id': task_id,
            'celery_task_id': celery_task.id,
            'filename': filename,
            'message': '索引文件上传成功，正在处理...'
        })

    except Exception as e:
        current_app.logger.error(f'上传索引文件出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/build', methods=['POST'])
def build_mdx():
    """
    启动MDX构建任务
    参数: task_id, config (TOML配置内容)
    """
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        config_content = data.get('config', '')

        if not task_id:
            return jsonify({'error': '缺少task_id'}), 400

        # 任务目录
        task_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        if not task_dir.exists():
            return jsonify({'error': '任务不存在'}), 404

        # 保存配置文件
        config_path = task_dir / 'build.toml'
        if config_content:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
        else:
            # 使用默认配置
            return jsonify({'error': '缺少配置文件'}), 400

        # 输出目录
        output_dir = str(Path(current_app.config['OUTPUT_FOLDER']) / task_id)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 启动Celery任务
        celery_task = build_mdx_task.delay(
            task_id=task_id,
            config_path=str(config_path),
            output_dir=output_dir
        )

        current_app.logger.info(f'MDX构建任务已启动: {task_id}, Celery任务ID: {celery_task.id}')

        return jsonify({
            'task_id': task_id,
            'celery_task_id': celery_task.id,
            'message': 'MDX构建任务已启动'
        })

    except Exception as e:
        current_app.logger.error(f'启动构建任务出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/status/<celery_task_id>')
def task_status(celery_task_id):
    """
    查询任务状态
    """
    try:
        from app.tasks import celery_app
        task = celery_app.AsyncResult(celery_task_id)

        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': '等待中...'
            }
        elif task.state == 'PROGRESS':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 100),
                'status': task.info.get('status', '')
            }
        elif task.state == 'SUCCESS':
            # 检查任务内部是否报错
            result = task.result
            if isinstance(result, dict) and result.get('status') == 'error':
                response = {
                    'state': 'FAILURE',
                    'status': result.get('message', '未知内部錯誤')
                }
            else:
                response = {
                    'state': task.state,
                    'result': result
                }
        else:
            # FAILURE or other states
            response = {
                'state': task.state,
                'status': str(task.info)
            }

        return jsonify(response)

    except Exception as e:
        current_app.logger.error(f'查询任务状态出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/download/<task_id>')
def download_result(task_id):
    """
    下载生成的词典文件 (MDX/MDD)
    """
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
            # 兼容旧逻辑：默认下载第一个 MDX 文件
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
    """
    清理任务文件
    """
    try:
        import shutil

        # 删除上传目录
        upload_dir = Path(current_app.config['UPLOAD_FOLDER']) / task_id
        if upload_dir.exists():
            shutil.rmtree(upload_dir)

        # 删除输出目录
        output_dir = Path(current_app.config['OUTPUT_FOLDER']) / task_id
        if output_dir.exists():
            shutil.rmtree(output_dir)

        current_app.logger.info(f'任务文件已清理: {task_id}')

        return jsonify({'message': '文件已清理'})

    except Exception as e:
        current_app.logger.error(f'清理文件出错: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500
