"""
简化任务管理器 - 使用线程代替 Celery，内存存储代替 Redis
"""
import threading
import uuid
import time
import os
import sys
import platform
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def _find_automdxbuilder_path() -> str:
    """
    智能查找 AutoMdxBuilder 可执行文件路径

    优先级:
    1. 环境变量 AMB_PATH
    2. 打包后的程序内置路径
    3. 当前目录下的 AutoMdxBuilder_python/AutoMdxBuilder
    4. 系统默认路径（根据操作系统）
    """
    # 1. 检查环境变量
    if 'AMB_PATH' in os.environ:
        return os.environ['AMB_PATH']

    # 2. 检测是否在 PyInstaller 打包环境中
    if getattr(sys, 'frozen', False):
        # 打包环境：AutoMdxBuilder 在资源目录中
        if hasattr(sys, '_MEIPASS'):
            # sys._MEIPASS 是 PyInstaller 解压临时文件的目录
            bundled_path = Path(sys._MEIPASS) / 'AutoMdxBuilder_python' / 'AutoMdxBuilder'
            if bundled_path.exists():
                logger.info(f"使用打包的 AutoMdxBuilder: {bundled_path}")
                return str(bundled_path)

    # 3. 检查当前目录
    current_dir = Path.cwd()
    local_path = current_dir / 'AutoMdxBuilder_python' / 'AutoMdxBuilder'
    if local_path.exists():
        logger.info(f"使用本地 AutoMdxBuilder: {local_path}")
        return str(local_path)

    # 4. 根据操作系统返回默认路径
    system = platform.system()
    if system == 'Windows':
        # Windows 默认路径（假设安装在 Program Files 或当前目录）
        default_paths = [
            r'C:\Program Files\AutoMdxBuilder\AutoMdxBuilder.exe',
            r'C:\AutoMdxBuilder\AutoMdxBuilder.exe',
            'AutoMdxBuilder.exe'
        ]
        for path in default_paths:
            if Path(path).exists():
                logger.info(f"使用系统路径: {path}")
                return path
        # 如果都不存在，返回第一个作为默认值（让后续检查报错）
        return default_paths[0]
    else:
        # macOS/Linux 默认路径
        default_path = '/usr/local/bin/AutoMdxBuilder'
        logger.info(f"使用默认路径: {default_path}")
        return default_path


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    state: str = 'PENDING'
    current: int = 0
    total: int = 100
    status: str = ''
    result: Any = None
    error: str = ''


# 全局任务存储
_tasks: Dict[str, TaskInfo] = {}
_lock = threading.Lock()


def get_task(task_id: str) -> Optional[TaskInfo]:
    """获取任务信息"""
    with _lock:
        return _tasks.get(task_id)


def update_task(task_id: str, **kwargs):
    """更新任务状态"""
    with _lock:
        if task_id in _tasks:
            task = _tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)


def create_task() -> str:
    """创建新任务"""
    task_id = str(uuid.uuid4())[:8]
    with _lock:
        _tasks[task_id] = TaskInfo(task_id=task_id)
    return task_id


def run_in_thread(func: Callable, task_id: str, *args, **kwargs):
    """在后台线程中运行任务"""

    def wrapper():
        try:
            update_task(task_id, state='PROGRESS')
            result = func(task_id, *args, **kwargs)
            update_task(task_id, state='SUCCESS', result=result)
        except Exception as e:
            logger.error(f"任务 {task_id} 失败: {e}", exc_info=True)
            update_task(task_id, state='FAILURE', error=str(e))

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    return task_id


# ===== 实际任务函数 =====

def convert_pdf_task(task_id: str, pdf_path: str, output_dir: str,
                     dpi: int = 300, quality: int = 85, crop: bool = False) -> dict:
    """PDF 转换任务"""
    try:
        import sys
        from pathlib import Path

        # 确保能找到 core 模块
        base_dir = Path(__file__).parent.parent
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        from core.pdf_processor import PDFProcessor

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        def progress_callback(current, total, page_num):
            update_task(task_id, current=current, total=total,
                        status=f'正在处理第 {current}/{total} 页')

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
        logger.error(f"PDF转换失败: {e}", exc_info=True)
        return {
            'task_id': task_id,
            'status': 'error',
            'message': f'转换失败: {str(e)}'
        }


def process_index_task(task_id: str, index_file_path: str, body_start: int = 1) -> dict:
    """处理索引文件任务"""
    try:
        import sys
        from pathlib import Path

        base_dir = Path(__file__).parent.parent
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        from utils.excel_utils import ExcelIndexConverter

        index_path = Path(index_file_path)
        task_dir = index_path.parent
        file_ext = index_path.suffix.lower()
        target_file = task_dir / 'index_all.txt'

        update_task(task_id, current=10, total=100, status='正在读取索引文件...')

        if file_ext in ['.xlsx', '.xls']:
            update_task(task_id, current=30, total=100, status='正在转换Excel文件...')

            converter = ExcelIndexConverter(index_path)
            structure = ExcelIndexConverter.detect_structure(index_path)
            skip_rows = structure['skip_rows'] if structure else 0

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

            update_task(task_id, current=60, total=100, status=f'正在保存 {count} 条数据...')
            converter.save_as_txt(target_file)
            preview = converter.get_preview(20)

        else:
            update_task(task_id, current=50, total=100, status='正在复制TXT文件...')
            import shutil
            shutil.copy(str(index_path), str(target_file))

            with open(target_file, 'r', encoding='utf-8') as f:
                lines = [f.readline() for _ in range(20)]
                preview = ''.join(lines)
                total_lines = sum(1 for _ in f) + 20
            count = total_lines

        update_task(task_id, current=90, total=100, status='正在完成...')

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
        logger.error(f"处理索引失败: {e}", exc_info=True)
        return {
            'task_id': task_id,
            'status': 'error',
            'message': f'处理索引文件失败: {str(e)}'
        }


def build_mdx_task(task_id: str, config_path: str, output_dir: str) -> dict:
    """MDX 构建任务"""
    try:
        import sys
        import os
        from pathlib import Path

        base_dir = Path(__file__).parent.parent
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        from core.amb_executor import AutoMdxBuilderExecutor

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        def output_callback(line):
            import re
            if '%' in line:
                match = re.search(r'(\d+)%', line)
                if match:
                    percent = int(match.group(1))
                    update_task(task_id, current=percent, total=100, status=line.strip())
            else:
                update_task(task_id, status=line.strip())

        # 智能查找 AutoMdxBuilder 路径
        amb_path = _find_automdxbuilder_path()
        executor = AutoMdxBuilderExecutor(amb_path)
        success, message = executor.execute(
            config_path=config_path,
            output_callback=output_callback
        )

        if success:
            config_dir = Path(config_path).parent
            mdx_files = list(config_dir.rglob('*.mdx'))
            mdd_files = list(config_dir.rglob('*.mdd'))

            import shutil
            for file in mdx_files + mdd_files:
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
        logger.error(f"MDX构建失败: {e}", exc_info=True)
        return {
            'task_id': task_id,
            'status': 'error',
            'message': f'构建失败: {str(e)}'
        }
