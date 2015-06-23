@echo off

call config.bat

echo Creating USERDATADIR: %USERDATADIR%
mkdir %USERDATADIR%

echo Installing PIP...
%PYTHON% %BINDIR%\get-pip.py

echo Installing KCAA Python server prerequisites...
%PIP% install --upgrade python-dateutil
%PIP% install --upgrade requests
%PIP% install --upgrade selenium
%PIP% install --upgrade --find-links https://code.google.com/p/google-visualization-python/ gviz-api-py

pause
