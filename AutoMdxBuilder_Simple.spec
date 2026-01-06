# -*- mode: python ; coding: utf-8 -*-
"""
简化版 PyInstaller 配置
无需 Redis 和 Celery！
"""
import sys
import os

block_cipher = None
cwd = os.getcwd()

# 数据文件
added_files = [
    ('static', 'static'),
    ('templates', 'templates'),
    ('app_simple', 'app_simple'),
    ('core', 'core'),
    ('utils', 'utils'),
    ('AutoMdxBuilder_python', 'AutoMdxBuilder_python'),
]

a = Analysis(
    ['desktop_simple.py'],
    pathex=[cwd],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # Flask
        'flask', 'flask_cors', 'werkzeug', 'jinja2', 'click', 'itsdangerous',
        'markupsafe',
        # 核心依赖
        'fitz', 'PIL', 'PIL.Image', 'openpyxl',
        # 应用模块
        'app_simple', 'app_simple.routes', 'app_simple.task_manager',
        'core', 'core.pdf_processor', 'core.amb_executor', 'core.config_generator',
        'utils', 'utils.excel_utils', 'utils.logger',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型依赖
        'celery', 'redis', 'kombu', 'billiard', 'gunicorn',
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'tkinter', 'PyQt5', 'PyQt6',
    ],
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
    console=True,  # 保留控制台窗口，方便看状态
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

# macOS 打包为 .app
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='AutoMdxBuilder.app',
        icon=None,
        bundle_identifier='com.automdxbuilder.app',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleName': 'AutoMdxBuilder',
            'NSHighResolutionCapable': True,
        },
    )
