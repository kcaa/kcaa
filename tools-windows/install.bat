@echo off

call config.bat

echo Installing PIP...
%PYTHON% %BINDIR%\get-pip.py

echo Installing KCAA Python server prerequisites...
%PIP% install python-dateutil
%PIP% install requests
%PIP% install selenium

pause
