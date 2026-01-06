# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

# 获取当前工作目录
cwd = os.getcwd()

# 定义要包含的数据文件
# (源路径, 目标文件夹)
added_files = [
    ('static', 'static'),
    ('templates', 'templates'),
    ('app', 'app'),
    ('core', 'core'),
    ('utils', 'utils'),
    ('AutoMdxBuilder_python', 'AutoMdxBuilder_python'),
    ('config.py', '.'),
    ('wsgi.py', '.'),
    ('requirements.txt', '.'),
]

# 添加 Redis (针对系统)
if sys.platform == 'darwin':
    import subprocess
    redis_path = subprocess.check_output(["which", "redis-server"]).decode().strip()
    if redis_path:
        added_files.append((redis_path, 'bin'))
elif sys.platform == 'win32':
    # 假设用户已经在本地 bin 目录下准备好了 redis-server.exe
    if os.path.exists('bin/redis-server.exe'):
        added_files.append(('bin/redis-server.exe', 'bin'))

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[cwd],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # Flask ecosystem
        'flask', 'flask_cors', 'werkzeug', 'jinja2', 'click', 'itsdangerous',
        # Celery ecosystem
        'celery', 'celery.app', 'celery.app.amqp', 'celery.app.log', 'celery.app.task',
        'celery.worker', 'celery.worker.autoscale', 'celery.worker.components',
        'celery.worker.consumer', 'celery.worker.strategy',
        'celery.bin', 'celery.bin.celery', 'celery.platforms', 'celery.backends',
        'celery.backends.redis', 'celery.concurrency', 'celery.concurrency.prefork',
        # Kombu (Celery dependency)
        'kombu', 'kombu.transport', 'kombu.transport.redis', 'kombu.serialization',
        'kombu.utils', 'kombu.utils.json', 'kombu.utils.encoding',
        # Billiard (Celery multiprocessing)
        'billiard', 'billiard.pool', 'billiard.process', 'billiard.context',
        # Redis
        'redis', 'redis.connection', 'redis.client',
        # Other dependencies
        'dotenv', 'fitz', 'PIL', 'openpyxl', 'gunicorn',
        # App modules
        'app', 'app.tasks', 'app.routes', 'core.pdf_processor', 'core.amb_executor',
        'utils', 'utils.excel_utils', 'utils.logger'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutoMdxBuilder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # 小白版建议先开启控制台，方便排错
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoMdxBuilder',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='AutoMdxBuilder.app',
        icon=None,
        bundle_identifier=None,
    )
