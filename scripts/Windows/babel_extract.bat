@echo off

set /p ENVNAME=<"%~dp0..\ENVNAME"

REM Check wheather anaconda is installed.
WHERE /q conda
IF ERRORLEVEL 1 (
    echo "Error: anaconda is not installed, quitting..."
    exit 1
)

echo "Extracting strings from the project"
echo:
call conda activate %ENVNAME% && cd ..\..\ && pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .

pause