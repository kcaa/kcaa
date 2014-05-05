@echo off

call config.bat

if %PROXYCONTROLLERDAEMON%==0 (
  echo Running proxy controller.
  start /b call run_proxy.bat
)

set SERVERBIN=%cd%\..\server\server_main.py

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
  --chrome_user_data_basedir=%CHROMEUSERDATABASEDIR% ^
  --chromedriver_binary=%CHROMEDRIVERBIN% ^
  --phantomjs_binary=%PHANTOMJSBIN% ^
  --credentials=%CREDENTIALS% ^
  --debug=%DEBUG%

echo Server exited. Close this window!
