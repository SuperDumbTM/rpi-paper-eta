@echo off

set ENVNAME="epd-eta-ctrl"

REM Check wheather anaconda is installed.
WHERE conda
if (%ERRORLEVEL% > 0) then (
    echo "Error: anaconda is not installed, quitting..."
    exit 1
)

echo "Creating conda enviroment %ENVNAME% with Python version 3.11"
echo:
call conda create --name %ENVNAME% python=3.11 -y
timeout 2

echo "Installing required Python packages."
echo:
call pip install -r "%~dp0..\..\requirements.txt"

pause