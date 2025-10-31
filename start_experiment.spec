# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.building.build_main import COLLECT
from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

project_root = os.path.abspath(os.path.dirname(__file__))

datas = []

for filename in ("config.json", "stimuli.csv"):
    source = os.path.join(project_root, filename)
    if os.path.exists(source):
        datas.append((source, "."))

for folder, prefix in (("fonts", "fonts"), ("pictures", "pictures")):
    folder_path = os.path.join(project_root, folder)
    if os.path.isdir(folder_path):
        datas.append(Tree(folder_path, prefix=prefix))

hiddenimports = collect_submodules("pygame")

a = Analysis(
    [os.path.join(project_root, "start_experiment.py")],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="PsychExperiment",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PsychExperiment",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="PsychExperiment.app",
        icon=None,
        bundle_identifier="com.psych.experiment",
    )

