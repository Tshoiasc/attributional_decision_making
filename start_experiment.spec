# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

from PyInstaller.building.build_main import COLLECT
from PyInstaller.building.datastruct import Tree
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

spec_path = Path(globals().get("SPEC", Path.cwd())).resolve()
project_root = spec_path.parent
project_root_str = str(project_root)

datas = []
extra_trees = []

font_path = os.path.join(project_root_str, "fonts")
if os.path.isdir(font_path):
    extra_trees.append((font_path, "fonts"))

hiddenimports = collect_submodules("pygame")

a = Analysis(
    [os.path.join(project_root_str, "start_experiment.py")],
    pathex=[project_root_str],
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

for folder_path, prefix in extra_trees:
    a.datas += Tree(folder_path, prefix=prefix)

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

