@echo off

for /d /r "%~dp0..\..\paper_eta" %%i in (__pycache__) do (
    echo Deleting "%%i"...
    rd /s /q "%%i"
)

pause