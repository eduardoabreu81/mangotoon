@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python 3 is required but was not found.
        echo Install Python from https://www.python.org/downloads/ and try again.
        exit /b 1
    )
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% --version
if %errorlevel% neq 0 (
    echo Python is installed but could not be started.
    exit /b 1
)

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo uv was not found. Installing uv for the current user...
    %PYTHON_CMD% -m pip install --user uv
    if %errorlevel% neq 0 (
        echo Failed to install uv.
        exit /b 1
    )
)

echo Installing dependencies...
%PYTHON_CMD% -m uv sync --extra dev
if %errorlevel% neq 0 (
    echo Dependency installation failed.
    exit /b 1
)

echo Initializing local data...
%PYTHON_CMD% scripts\init_data.py
if %errorlevel% neq 0 (
    echo Data initialization failed.
    exit /b 1
)

echo Starting MangoToon at http://127.0.0.1:8000/
start "" "http://127.0.0.1:8000/"
%PYTHON_CMD% -m uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
