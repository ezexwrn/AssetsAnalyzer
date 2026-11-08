@echo off
set "PY=python"
if exist "%~dp0runtime\python.exe" set "PY=%~dp0runtime\python.exe"
if not "%~1"=="" goto run

echo Assets Analyzer
echo.
set "FOLDER="
set /p "FOLDER=Drag a game folder here (or paste its path) and press Enter: "
if not defined FOLDER goto help
set "FOLDER=%FOLDER:"=%"
"%PY%" "%~dp0analyzer.py" scan "%FOLDER%"
goto end

:help
"%PY%" "%~dp0analyzer.py"
goto end

:run
"%PY%" "%~dp0analyzer.py" %*

:end
echo.
pause