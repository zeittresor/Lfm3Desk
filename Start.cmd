@echo off
cd /d "%~dp0"
if not exist "%~dp0lfm3gui.exe" (
  call "%~dp0Build.cmd"
  if errorlevel 1 exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0EnsureRuntime.ps1"
if errorlevel 1 exit /b 1
if exist "%~dp0tools\dotnet-runtime\dotnet.exe" set "DOTNET_ROOT=%~dp0tools\dotnet-runtime"
if "%~1"=="" (
  start "" "%~dp0lfm3gui.exe"
  exit /b 0
)
"%~dp0lfm3gui.exe" %*
exit /b %errorlevel%
