"""
Celery异步任务
"""
from celery import Celery, Task
from pathlib import Path
import sys
import os
import logging
from dotenv import load_dotenv

# 加载配置
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 创建Celery应用
celery_app = Celery('automdxbuilder_web')

# 从环境变量或默认值配置
celery_app.conf.broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery_app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)


class CallbackTask(Task):
    """支持进度回调的任务基类"""

    def update_progress(self, current, total, status=''):
        """更新任务进度"""
        self.update_state(
            state='PROGRESS',
            meta={
                'current': current,
                'total': total,
                'status': status
            }
        )


@celery_app.task(bind=True, base=CallbackTask)
def convert_pdf_task(self, task_id, pdf_path, output_dir, dpi=300, quality=85, crop=False):
    """
    PDF转换任务

    Args:
        task_id: 任务ID
        pdf_path: PDF文件路径
        output_dir: 输出目录
        dpi: DPI设置
        quality: 图片质量
        crop: 是否裁剪
    """
    try:
        from core.pdf_processor import PDFProcessor

        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 进度回调函数
        def progress_callback(current, total, page_num):
            self.update_progress(
                current=current,
                total=total,
                status=f'正在处理第 {current}/{total} 页'
            )

        # 执行转换
        import os
        import unicodedata
        
        # 调试日志：检查文件是否存在
        exists = os.path.exists(pdf_path)
        abs_path = os.path.abspath(pdf_path)
        normalized_path = unicodedata.normalize('NFC', pdf_path)
        normalized_exists = os.path.exists(normalized_path)
        
        self.update_progress(0, 100, f"DEBUG: 检查文件 {exists}, 绝对路徑 {abs_path}")
        logger.info(f"DEBUG: 原始路径: {pdf_path}, 是否存在: {exists}")
        logger.info(f"DEBUG: 绝对路径: {abs_path}")
        logger.info(f"DEBUG: NFC化路径: {normalized_path}, 是否存在: {normalized_exists}")
        
        if not exists:
            # 尝试修复路径（Mac上的NFC/NFD问题）
            if normalized_exists:
                pdf_path = normalized_path
                logger.info("DEBUG: 使用NFC化路径成功")
            else:
                # 尝试再次搜索该目录下的pdf
                parent_dir = Path(pdf_path).parent
                if parent_dir.exists():
                    all_files = list(parent_dir.glob("*.pdf"))
                    logger.info(f"DEBUG: 目录下的文件: {all_files}")
                    if all_files:
                        pdf_path = str(all_files[0])
                        logger.info(f"DEBUG: 修正路径为: {pdf_path}")

        processor = PDFProcessor(pdf_path)
        with processor:
            stats = processor.extract_images(
                output_dir=str(Path(output_dir) / 'imgs'),
                dpi=dpi,
                quality=quality,
                crop=crop,
                progress_callback=progress_callback
            )

        return {
            'task_id': task_id,
            'status': 'success',
            'message': 'PDF转换完成',
            'stats': stats
        }

    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'error',
            'message': f'转换失败: {str(e)}'
        }


@celery_app.task(bind=True, base=CallbackTask)
def process_index_task(self, task_id, index_file_path, body_start=1):
    """
    处理索引文件任务

    Args:
        task_id: 任务ID
        index_file_path: 索引文件路径 (TXT或Excel)
        body_start: 正文起始页
    """
    try:
        from utils.excel_utils import ExcelIndexConverter

        index_path = Path(index_file_path)
        task_dir = index_path.parent
        file_ext = index_path.suffix.lower()

        # 目标文件：index_all.txt
        target_file = task_dir / 'index_all.txt'

        self.update_progress(
            current=10,
            total=100,
            status='正在读取索引文件...'
        )

        if file_ext in ['.xlsx', '.xls']:
            # Excel文件 - 需要转换
            self.update_progress(
                current=30,
                total=100,
                status='正在转换Excel文件...'
            )

            converter = ExcelIndexConverter(index_path)

            # 自动检测Excel结构（是否有表头）
            structure = ExcelIndexConverter.detect_structure(index_path)
            skip_rows = structure['skip_rows'] if structure else 0

            # 使用检测到的配置加载（第一列词目，第二列页码）
            count = converter.load(
                sheet_name=None,
                skip_rows=skip_rows,
                entry_col=0,
                page_col=1
            )

            if count == 0:
                return {
                    'task_id': task_id,
                    'status': 'error',
                    'message': 'Excel文件中没有有效数据'
                }

            self.update_progress(
                current=60,
                total=100,
                status=f'正在保存 {count} 条数据...'
            )

            # 保存为TXT
            converter.save_as_txt(target_file)

            # 获取预览
            preview = converter.get_preview(20)

        else:
            # TXT文件 - 直接复制
            self.update_progress(
                current=50,
                total=100,
                status='正在复制TXT文件...'
            )

            import shutil
            shutil.copy(str(index_path), str(target_file))

            # 读取预览
            with open(target_file, 'r', encoding='utf-8') as f:
                lines = [f.readline() for _ in range(20)]
                preview = ''.join(lines)
                total_lines = sum(1 for _ in f) + 20

            count = total_lines

        self.update_progress(
            current=90,
            total=100,
            status='正在完成...'
        )

        # 保存body_start到配置文件（简单存储）
        body_start_file = task_dir / 'body_start.txt'
        with open(body_start_file, 'w') as f:
            f.write(str(body_start))

        return {
            'task_id': task_id,
            'status': 'success',
            'message': '索引文件处理完成',
            'count': count,
            'preview': preview,
            'body_start': body_start
        }

    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'error',
            'message': f'处理索引文件失败: {str(e)}'
        }


@celery_app.task(bind=True, base=CallbackTask)
def build_mdx_task(self, task_id, config_path, output_dir):
    """
    MDX构建任务

    Args:
        task_id: 任务ID
        config_path: 配置文件路径
        output_dir: 输出目录
    """
    try:
        from core.amb_executor import AutoMdxBuilderExecutor
        import subprocess

        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 获取AutoMdxBuilder路径
        amb_path = os.environ.get('AMB_PATH', '/usr/local/bin/AutoMdxBuilder')

        # 输出回调函数
        def output_callback(line):
            # 解析进度（如果有）
            if '%' in line:
                try:
                    # 尝试提取百分比
                    import re
                    match = re.search(r'(\d+)%', line)
                    if match:
                        percent = int(match.group(1))
                        self.update_progress(
                            current=percent,
                            total=100,
                            status=line.strip()
                        )
                except:
                    pass
            self.update_progress(
                current=0,
                total=100,
                status=line.strip()
            )

        # 执行构建
        executor = AutoMdxBuilderExecutor(amb_path)
        success, message = executor.execute(
            config_path=config_path,
            output_callback=output_callback
        )

        if success:
            # 移动生成的文件到输出目录
            config_dir = Path(config_path).parent
            mdx_files = list(config_dir.rglob('*.mdx'))
            mdd_files = list(config_dir.rglob('*.mdd'))

            for file in mdx_files + mdd_files:
                import shutil
                shutil.move(str(file), str(Path(output_dir) / file.name))

            return {
                'task_id': task_id,
                'status': 'success',
                'message': 'MDX构建完成',
                'files': [f.name for f in mdx_files + mdd_files]
            }
        else:
            return {
                'task_id': task_id,
                'status': 'error',
                'message': f'构建失败: {message}'
            }

    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'error',
            'message': f'构建失败: {str(e)}'
        }


@celery_app.task
def cleanup_old_files(hours=24):
    """
    清理旧文件任务

    Args:
        hours: 保留时长（小时）
    """
    try:
        import time
        import shutil
        from config import Config

        current_time = time.time()
        deleted_count = 0

        # 清理上传目录
        upload_dir = Path(Config.UPLOAD_FOLDER)
        if upload_dir.exists():
            for task_dir in upload_dir.iterdir():
                if task_dir.is_dir():
                    # 检查修改时间
                    mtime = task_dir.stat().st_mtime
                    age_hours = (current_time - mtime) / 3600
                    if age_hours > hours:
                        shutil.rmtree(task_dir)
                        deleted_count += 1

        # 清理输出目录
        output_dir = Path(Config.OUTPUT_FOLDER)
        if output_dir.exists():
            for task_dir in output_dir.iterdir():
                if task_dir.is_dir():
                    mtime = task_dir.stat().st_mtime
                    age_hours = (current_time - mtime) / 3600
                    if age_hours > hours:
                        shutil.rmtree(task_dir)
                        deleted_count += 1

        return {
            'status': 'success',
            'message': f'已清理 {deleted_count} 个旧任务目录'
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'清理失败: {str(e)}'
        }
