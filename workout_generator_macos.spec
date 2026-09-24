# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("templates", "templates"),
        ("static", "static"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="WORKOUT Generator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="WORKOUT Generator",
)

app = BUNDLE(
    coll,
    name="WORKOUT Generator.app",
    icon=None,
    bundle_identifier="app.workout.generator",
    info_plist={
        "CFBundleName": "WORKOUT Generator",
        "CFBundleDisplayName": "WORKOUT Generator",
        "NSHighResolutionCapable": True,
    },
)
