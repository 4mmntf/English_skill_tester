# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('.venv/Lib/site-packages/flet_desktop/app/flet', 'flet'),
    ],
    hiddenimports=[
        'openai',
        'azure.cognitiveservices.speech',
        'pydantic',
        'pydantic_settings',
        'dotenv',
        'flet.core',
        'flet.core.page',
        'flet.core.control',
        'flet.core.event',
        'flet.utils',
        'flet_desktop',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    excludes=['flet_cli.__pyinstaller'],
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EnglishSkillApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUIアプリなのでコンソールを表示しない
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # アイコンファイルがある場合は指定
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='EnglishSkillApp',
)

