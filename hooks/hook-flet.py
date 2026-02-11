# Custom PyInstaller hook to disable the problematic flet hook
# This hook simply excludes the problematic flet_cli module
hiddenimports = []
excludedimports = ['flet_cli.__pyinstaller']