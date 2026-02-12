@echo off
REM Windows用ビルドスクリプト（uv使用）

echo Building Windows application...

REM uvの確認
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo uvがインストールされていません。
    echo インストール方法: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)

REM 依存パッケージのインストール
echo Installing dependencies...
uv sync

REM PyInstallerでビルド
echo Building executable...
uv run pyinstaller build_windows.spec

echo Build complete! Executable is in dist\EnglishSkillApp.exe

pause

