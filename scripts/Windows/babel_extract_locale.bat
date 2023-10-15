@echo off

set /p ENVNAME=<"%~dp0..\ENVNAME"

REM Check wheather anaconda is installed.
WHERE /q conda
IF ERRORLEVEL 1 (
    echo "Error: anaconda is not installed, quitting..."
    exit 1
)

echo "Updating translation files"
echo:
call conda activate %ENVNAME% && cd ..\..\
call pybabel update -i messages.pot -d translations

pause