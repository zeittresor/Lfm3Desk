@echo off
cd /d "%~dp0"
set "TASK_DOTNET=dotnet"
if exist "%~dp0tools\dotnet\dotnet.exe" set "TASK_DOTNET=%~dp0tools\dotnet\dotnet.exe"
set "TASK_PYTHON=python"
if exist "%~dp0.venv\Scripts\python.exe" set "TASK_PYTHON=%~dp0.venv\Scripts\python.exe"
"%TASK_DOTNET%" run --project tests\CliTests.csproj -c Release
if errorlevel 1 exit /b 1
"%TASK_PYTHON%" -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tests\Test-Setup.ps1" -Python "%TASK_PYTHON%"
if errorlevel 1 exit /b 1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tests\Test-Reuse.ps1"
exit /b %errorlevel%
