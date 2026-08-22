# build.spec
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)

block_cipher = None

# 1. collect package assets
uiautomator2_datas = collect_data_files("uiautomator2")
webview_datas = collect_data_files("webview")
pythonnet_datas = collect_data_files("pythonnet")
clr_loader_datas = collect_data_files("clr_loader")

package_metadata = (
    copy_metadata("pywebview")
    + copy_metadata("pythonnet")
    + copy_metadata("clr_loader")
)

pythonnet_binaries = collect_dynamic_libs("pythonnet")

extra_hiddenimports = (
    collect_submodules("pythonnet")
    + collect_submodules("clr_loader")
)

# 2. Project assets loaded by path at runtime.
# Python modules (controller/, worker/, blueprints/, config.py, etc.) are found
# by Analysis from app.py and must not be copied again as data files.
project_datas = [
    ('templates', 'templates'),
    ('static', 'static'),
]

# 3. merge datas
datas = (
    uiautomator2_datas
    + webview_datas
    + pythonnet_datas
    + clr_loader_datas
    + package_metadata
    + project_datas
)


a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[
        ('adb/windows/adb.exe', 'adb/windows'),
        ('adb/windows/AdbWinApi.dll', 'adb/windows'),
        ('adb/windows/AdbWinUsbApi.dll', 'adb/windows'),
        *pythonnet_binaries,
    ],
    datas=datas,
    hiddenimports=[
        # APScheduler
        'apscheduler.triggers.cron',
        'apscheduler.triggers.date',
        'apscheduler.triggers.interval',
        'apscheduler.executors.pool',
        'apscheduler.executors.base',
        'apscheduler.jobstores.memory',
        'apscheduler.jobstores.base',

        # Google
        'google.oauth2.service_account',
        'google.auth.transport.requests',
        'googleapiclient.discovery',
        # Flask
        'flask',
        'werkzeug.utils',
        'werkzeug.serving',

        # multiprocessing
        'multiprocessing.spawn',
        'multiprocessing.forkserver',

        # your modules
        'controller.posting',
        'controller.trust',
        'controller.boost',
        'controller.update',
        'worker.worker',

         # PyWebView
        'webview',
        'webview.platforms',
        'webview.platforms.edgechromium',
        'webview.platforms.winforms',
        *extra_hiddenimports,
    ],
    hookspath=[],
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
    name='Insta-Tool',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon='static/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='Insta-Tool',
)
