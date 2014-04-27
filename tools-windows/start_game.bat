@echo off

call config.bat

set SERVERBIN=%cd%\..\server\server_main.py
set PYTHONPATH=%PYTHONPATH%;%cd%\..\server

echo %PYTHONPATH%

%PYTHON% ^
  %SERVERBIN% ^
  --proxy_controller=%PROXYCONTROLLERHOST%:%PROXYCONTROLLERPORT% ^
  --proxy=%PROXYCONTROLLERHOST%:%PROXYPORT% ^
  --server_port=%SERVERPORT% ^
  --backend_update_interval=%BACKENDUPDATEINTERVAL% ^
  --kancolle_browser=%KANCOLLEBROWSER% ^
  --kcaa_browser=%KCAABROWSER% ^
  --frontend_update_interval=%FRONTENDUPDATEINTERVAL% ^
  --chrome_binary=%CHROMEBIN% ^
  --chromedriver_binary=%CHROMEDRIVERBIN% ^
  --phantomjs_binary=%PHANTOMJSBIN% ^
  --credentials=%CREDENTIALS% ^
  --debug=%DEBUG%
