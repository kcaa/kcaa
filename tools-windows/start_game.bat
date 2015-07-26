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
  --show_kancolle_screen=%SHOWKANCOLLESCREEN% ^
  --frontend_update_interval=%FRONTENDUPDATEINTERVAL% ^
  --chrome_binary=%CHROMEBIN% ^
  --chromium_binary=%CHROMIUMBIN% ^
  --chrome_user_data_basedir=%CHROMEUSERDATABASEDIR% ^
  --chromedriver_binary=%CHROMEDRIVERBIN% ^
  --phantomjs_binary=%PHANTOMJSBIN% ^
  --preferences=%PREFERENCES% ^
  --journal_basedir=%JOURNAL_BASEDIR% ^
  --state_basedir=%STATE_BASEDIR% ^
  --credentials=%CREDENTIALS% ^
  --debug=%DEBUG% ^
  --log_file=%LOGFILE% ^
  --log_level=%LOGLEVEL% ^
  --keep_timestamped_logs=%KEEPTIMESTAMPEDLOGS%

echo Server exited. Close this window!
